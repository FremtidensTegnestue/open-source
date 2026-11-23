#!/usr/bin/env python3
"""Publish an unchanged, source-bound Table 7 excerpt for the browser lookup."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'materialer/data/parquet'
OUTPUT = ROOT / 'docs/materialer.json'


def export_materials(root=DATA):
    import pyarrow.dataset as ds
    import pyarrow.parquet as pq
    root = Path(root)
    materials = [row for row in pq.read_table(root / 'materials.parquet').to_pylist()
                 if row['id'].startswith('br18:t7:')]
    if len(materials) != 507:
        raise ValueError('Browserudgaven er afgrænset til de 507 kontrollerede tabel 7-referencer.')
    ids = {row['id'] for row in materials}
    table = ds.dataset(root / 'observations', format='parquet', partitioning='hive')
    observations = table.to_table(filter=ds.field('material_id').isin(ids)).to_pylist()
    if len(observations) != 2535:
        raise ValueError('Tabel 7-udtrækket har ikke de forventede 2.535 observationer.')
    used_sources = {row['source_id'] for row in materials + observations}
    for row in observations:
        basis_source = json.loads(row['conditions_json']).get('basis_source_id')
        if basis_source:
            used_sources.add(basis_source)
    sources = [row for row in pq.read_table(root / 'sources.parquet').to_pylist()
               if row['id'] in used_sources]
    if {row['id'] for row in sources} != used_sources:
        raise ValueError('En materialereference mangler sin kilde.')
    grouped = {id_: [] for id_ in ids}
    for row in observations:
        grouped[row['material_id']].append(row)
    records = []
    for material in sorted(materials, key=lambda row: row['id']):
        rows = sorted(grouped[material['id']], key=lambda row: row['id'])
        modules = [row['module'] for row in rows if row['property'] == 'global_warming_potential']
        if sorted(modules) != ['A1-A3', 'C3', 'C4', 'D'] or len(rows) != 5:
            raise ValueError('En reference mangler et modul eller har en dublet.')
        records.append({'material': material, 'observations': rows})
    return {'schema_version': 1, 'scope': 'BR18 tabel 7, generisk datagrundlag 2025',
            'material_count': len(records), 'observation_count': len(observations),
            'parquet_manifest_sha256': hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest(),
            'sources': sorted(sources, key=lambda row: row['id']), 'records': records}


def encoded(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify the shipped browser data without writing')
    args = parser.parse_args()
    content = encoded(export_materials())
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != content:
            parser.exit(1, 'Browserdata matcher ikke Parquet. Genbyg med scripts/build_browser_materials.py.\n')
        print('507 materialer / 2.535 observationer: browserdata matcher Parquet.')
    else:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(content, encoding='utf-8')
        print(f'Wrote {OUTPUT.relative_to(ROOT)} ({len(content.encode())} bytes)')


if __name__ == '__main__':
    main()
