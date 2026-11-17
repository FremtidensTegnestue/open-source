#!/usr/bin/env python3
"""Build the complete local SQLite database from the committed Parquet snapshot.

Run from any directory: python /path/to/repository/scripts/build_database.py
Existing databases are preserved unless --force is explicitly supplied. A forced
replacement is published atomically only after all validation has passed.
"""

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from urllib.parse import quote

try:
    import pyarrow.parquet as pq
except ImportError:
    raise SystemExit("Install snapshot dependencies: python -m pip install -r requirements.txt") from None


TABLES = ("datasets", "sources", "materials", "observations", "build_info")
BATCH_ROWS = 10_000
REPOSITORY = Path(__file__).resolve().parents[1]


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def update_digest(digest, rows):
    for row in rows:
        digest.update(json.dumps(row, ensure_ascii=False, separators=(",", ":"),
                                 allow_nan=False).encode("utf-8"))
        digest.update(b"\n")


def identifier(value):
    return '"' + value.replace('"', '""') + '"'


def validate_database(connection, manifest):
    """Read every restored cell back from SQLite, comparing snapshot row hashes."""
    for table in TABLES:
        columns = [item["name"] for item in manifest["tables"][table]["columns"]]
        dataset_index = columns.index("dataset_id") if table == "observations" else None
        digests = {key: hashlib.sha256()
                   for key in manifest["tables"][table]["partitions"]}
        counts = defaultdict(int)
        cursor = connection.execute(f"SELECT * FROM {identifier(table)} ORDER BY rowid")
        while rows := cursor.fetchmany(BATCH_ROWS):
            groups = defaultdict(list)
            for row in rows:
                groups[row[dataset_index] if dataset_index is not None else "all"].append(row)
            for partition, records in groups.items():
                update_digest(digests[partition], records)
                counts[partition] += len(records)
        for partition, expected in manifest["tables"][table]["partitions"].items():
            if (counts[partition] != expected["rows"]
                    or digests[partition].hexdigest() != expected["content_sha256"]):
                raise ValueError(f"Restored SQLite content mismatch: {table}/{partition}")
        print(f"Validated restored {table}: {sum(counts.values()):,} rows", flush=True)


def build(source, destination, force=False):
    if destination.exists() and not force:
        raise SystemExit(f"Database already exists: {destination}. Use --force to replace it.")
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1:
        raise ValueError("Unsupported Parquet snapshot format_version")
    for item in manifest["files"]:
        path = source / item["path"]
        if path.stat().st_size != item["bytes"] or file_sha256(path) != item["sha256"]:
            raise ValueError(f"Parquet file checksum failed: {path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=".materials-build-", dir=destination.parent) as temporary:
        temporary_database = Path(temporary) / "materials.sqlite"
        connection = sqlite3.connect(temporary_database)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN")
        try:
            schemas = {item["name"]: item["sql"] for item in manifest["sqlite_schema"]
                       if item["type"] == "table"}
            for table in TABLES:
                connection.execute(schemas[table])
            for table in TABLES:
                columns = [item["name"] for item in manifest["tables"][table]["columns"]]
                insert = (f"INSERT INTO {identifier(table)} ("
                          + ",".join(map(identifier, columns)) + ") VALUES ("
                          + ",".join("?" for _ in columns) + ")")
                for partition, expected in manifest["tables"][table]["partitions"].items():
                    prefix = ("observations/dataset_id=" + quote(partition, safe="") + "/"
                              if table == "observations" else f"{table}.parquet")
                    files = [source / item["path"] for item in manifest["files"]
                             if (item["path"].startswith(prefix) if table == "observations"
                                 else item["path"] == prefix)]
                    digest = hashlib.sha256()
                    count = 0
                    for path in sorted(files):
                        parquet = pq.ParquetFile(path)
                        if parquet.schema_arrow.names != columns:
                            raise ValueError(f"Unexpected column order: {path}")
                        for batch in parquet.iter_batches(batch_size=BATCH_ROWS):
                            records = list(zip(*(column.to_pylist() for column in batch.columns)))
                            update_digest(digest, records)
                            connection.executemany(insert, records)
                            count += len(records)
                    if count != expected["rows"] or digest.hexdigest() != expected["content_sha256"]:
                        raise ValueError(f"Parquet row count or content digest failed: {table}/{partition}")
                print(f"Restored {table}: {manifest['tables'][table]['rows']:,} rows "
                      f"in {time.monotonic() - started:.1f}s", flush=True)
            for item in manifest["sqlite_schema"]:
                if item["type"] == "index":
                    connection.execute(item["sql"])
            validate_database(connection, manifest)
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise ValueError("Restored database has foreign-key violations")
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise ValueError("Restored database failed SQLite integrity_check")
            pragmas = manifest.get("sqlite_pragmas", {})
            for name in ("user_version", "application_id"):
                connection.execute(f"PRAGMA {name}={int(pragmas.get(name, 0))}")
            schema_version = connection.execute(
                "SELECT value FROM build_info WHERE key='schema_version'").fetchone()[0]
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        if force:
            os.replace(temporary_database, destination)
        else:
            # Atomic no-overwrite publication, including a destination created
            # by another process while this build was running.
            os.link(temporary_database, destination)
        report = {
            "database": str(destination),
            "database_bytes": destination.stat().st_size,
            "database_profile": manifest.get("database_profile", "full"),
            "schema_version": schema_version,
            "snapshot_manifest_sha256": file_sha256(manifest_path),
            "tables": {name: item["rows"] for name, item in manifest["tables"].items()},
            "validation": "file SHA256, Parquet row SHA256, SQLite row SHA256, foreign keys, integrity_check passed",
            "elapsed_seconds": round(time.monotonic() - started, 2),
        }
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", type=Path, default=REPOSITORY / "data" / "parquet")
    parser.add_argument("--db", type=Path, default=REPOSITORY / "data" / "materials.sqlite")
    parser.add_argument("--force", action="store_true", help="Replace an existing database after validation")
    arguments = parser.parse_args()
    build(arguments.parquet_dir.resolve(), arguments.db.resolve(), force=arguments.force)
