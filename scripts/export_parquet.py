#!/usr/bin/env python3
"""Export the complete materials SQLite database to validated Parquet files.

Usage: python export_materials_parquet.py materials.sqlite parquet-directory
Requires pyarrow. The source is opened read-only and is never modified.
Every column remains in each file, including dataset_id in partition folders.
For a single file use pyarrow.parquet.ParquetFile(path).read(); for a directory
use pyarrow.dataset.dataset(path, format="parquet", partitioning=None).
"""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from urllib.parse import quote

import pyarrow as pa
import pyarrow.parquet as pq


TABLES = ("datasets", "sources", "materials", "observations", "build_info")
BATCH_ROWS = 10_000
FILE_ROWS = 250_000


def quote_identifier(value):
    return '"' + value.replace('"', '""') + '"'


def update_digest(digest, rows):
    # A canonical logical row stream, independent of Parquet encoding/batches.
    # JSON preserves TEXT contents, NULL, integers and float64 round trips.
    for row in rows:
        digest.update(json.dumps(row, ensure_ascii=False, separators=(",", ":"),
                                 allow_nan=False).encode("utf-8"))
        digest.update(b"\n")


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export(source, destination):
    if destination.exists():
        raise SystemExit(f"Output directory already exists: {destination}")
    destination.mkdir(parents=True)
    source_before = source.stat()
    connection = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    connection.execute("BEGIN")
    manifest = {
        "format_version": 1,
        "source_file": source.name,
        "source_bytes": source_before.st_size,
        "database_profile": "full",
        "sqlite_pragmas": {name: connection.execute(f"PRAGMA {name}").fetchone()[0]
                           for name in ("user_version", "application_id")},
        "compression": "zstd",
        "compression_level": 9,
        "batch_rows": BATCH_ROWS,
        "max_rows_per_observation_file": FILE_ROWS,
        "partition_column_is_also_stored_in_files": True,
        "nulls_and_json_text_preserved": True,
        "pyarrow_version": pa.__version__,
        "sqlite_schema": [dict(zip(("type", "name", "table", "sql"), row))
                          for row in connection.execute(
                              "SELECT type,name,tbl_name,sql FROM sqlite_master "
                              "WHERE sql IS NOT NULL ORDER BY type,name")],
        "tables": {},
        "files": [],
    }
    started = time.monotonic()
    for table in TABLES:
        declaration = connection.execute(
            f"PRAGMA table_info({quote_identifier(table)})").fetchall()
        columns = [row[1] for row in declaration]
        types = {"TEXT": pa.string(), "REAL": pa.float64(),
                 "INTEGER": pa.int64(), "BLOB": pa.binary()}
        schema = pa.schema([pa.field(row[1], types[row[2].upper()],
                                    nullable=not bool(row[3]))
                            for row in declaration])
        manifest["tables"][table] = {
            "columns": [{"name": row[1], "sqlite_type": row[2],
                         "nullable": not bool(row[3]),
                         "primary_key_position": row[5]} for row in declaration],
            "rows": 0,
            "partitions": {},
        }
        states = {}
        cursor = connection.execute(f"SELECT * FROM {quote_identifier(table)} ORDER BY rowid")
        dataset_index = columns.index("dataset_id") if table == "observations" else None
        while rows := cursor.fetchmany(BATCH_ROWS):
            groups = defaultdict(list)
            for row in rows:
                groups[row[dataset_index] if dataset_index is not None else None].append(row)
            for dataset_id, partition_rows in groups.items():
                if dataset_id not in states:
                    directory = destination
                    if dataset_id is not None:
                        directory /= "observations" / Path("dataset_id=" + quote(dataset_id, safe=""))
                        directory.mkdir(parents=True, exist_ok=True)
                    states[dataset_id] = {"directory": directory, "writer": None,
                                          "file_rows": 0, "file_number": 0,
                                          "rows": 0, "digest": hashlib.sha256(),
                                          "null_counts": [0] * len(columns),
                                          "sample_first": None, "sample_last": None,
                                          "files": []}
                state = states[dataset_id]
                update_digest(state["digest"], partition_rows)
                for position in range(0, len(partition_rows), BATCH_ROWS):
                    chunk = partition_rows[position:position + BATCH_ROWS]
                    offset = 0
                    while offset < len(chunk):
                        if state["writer"] is None:
                            name = (f"part-{state['file_number']:05d}.parquet"
                                    if dataset_id is not None else f"{table}.parquet")
                            path = state["directory"] / name
                            state["files"].append(path)
                            state["writer"] = pq.ParquetWriter(
                                path, schema, compression="zstd", compression_level=9,
                                use_dictionary=True, write_statistics=True,
                                version="2.6")
                        take = min(len(chunk) - offset, FILE_ROWS - state["file_rows"])
                        records = chunk[offset:offset + take]
                        arrays = [pa.array([row[index] for row in records], type=field.type)
                                  for index, field in enumerate(schema)]
                        arrow_table = pa.Table.from_arrays(arrays, schema=schema)
                        state["writer"].write_table(arrow_table, row_group_size=BATCH_ROWS)
                        for index, array in enumerate(arrays):
                            state["null_counts"][index] += array.null_count
                        state["rows"] += take
                        state["file_rows"] += take
                        state["sample_first"] = state["sample_first"] or records[0]
                        state["sample_last"] = records[-1]
                        offset += take
                        if dataset_id is not None and state["file_rows"] == FILE_ROWS:
                            state["writer"].close()
                            state["writer"] = None
                            state["file_rows"] = 0
                            state["file_number"] += 1
            manifest["tables"][table]["rows"] += len(rows)
            if manifest["tables"][table]["rows"] % 100_000 == 0:
                print(f"Exported {table}: {manifest['tables'][table]['rows']:,} rows "
                      f"in {time.monotonic() - started:.1f}s", flush=True)
        for dataset_id, state in states.items():
            if state["writer"] is not None:
                state["writer"].close()
            digest = hashlib.sha256()
            actual_rows = 0
            null_counts = [0] * len(columns)
            first = last = None
            for path in state["files"]:
                parquet = pq.ParquetFile(path)
                assert parquet.schema_arrow.equals(schema), (path, parquet.schema_arrow, schema)
                for batch in parquet.iter_batches(batch_size=BATCH_ROWS):
                    values = [column.to_pylist() for column in batch.columns]
                    records = list(zip(*values))
                    update_digest(digest, records)
                    actual_rows += batch.num_rows
                    for index, column in enumerate(batch.columns):
                        null_counts[index] += column.null_count
                    first = first or records[0]
                    last = records[-1]
                manifest["files"].append({
                    "path": str(path.relative_to(destination)),
                    "rows": parquet.metadata.num_rows,
                    "row_groups": parquet.metadata.num_row_groups,
                    "bytes": path.stat().st_size,
                    "sha256": file_hash(path),
                })
            assert actual_rows == state["rows"], (table, dataset_id, actual_rows, state["rows"])
            assert null_counts == state["null_counts"], (table, dataset_id, null_counts)
            assert digest.digest() == state["digest"].digest(), (table, dataset_id, "content mismatch")
            assert first == state["sample_first"] and last == state["sample_last"]
            manifest["tables"][table]["partitions"][dataset_id or "all"] = {
                "rows": actual_rows,
                "content_sha256": digest.hexdigest(),
                "null_counts": dict(zip(columns, null_counts)),
                "first_id_or_key": first[0],
                "last_id_or_key": last[0],
                "full_content_validation": "passed",
            }
        print(f"Validated {table}: {manifest['tables'][table]['rows']:,} rows "
              f"in {time.monotonic() - started:.1f}s", flush=True)
    connection.rollback()
    connection.close()
    source_after = source.stat()
    assert (source_before.st_size, source_before.st_mtime_ns) == (
        source_after.st_size, source_after.st_mtime_ns), "Source changed during export"
    manifest["source_unchanged_size_and_mtime"] = True
    manifest["parquet_bytes"] = sum(item["bytes"] for item in manifest["files"])
    manifest["compression_ratio_to_sqlite"] = source_before.st_size / manifest["parquet_bytes"]
    manifest["elapsed_seconds"] = round(time.monotonic() - started, 2)
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in (
        "parquet_bytes", "compression_ratio_to_sqlite", "elapsed_seconds")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    export(arguments.source.resolve(), arguments.destination.resolve())
