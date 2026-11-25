#!/usr/bin/env python3
"""Export two reviewed screw references, unchanged, separately from BR18 Table 7."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'materialer/data/parquet'
OUTPUT = ROOT / 'docs/fastgoerelser.json'
IDS = {
    'environmental:material:oekobaudat:889e2819-01be-4aa4-b7d3-d19e01e75c02@20.26.070': 'Galvanized steel screws',
    'environmental:material:oekobaudat:6c46fc8d-6a74-415b-8e6b-b90af72178ac@20.26.070': 'Stainless steel screws',
}
INDICATOR = 'a7ea142a-9749-11ed-a8fc-0242ac120002'  # GWP-total, EF 3.1


def export_fasteners(root=DATA):
    import pyarrow.dataset as ds
    import pyarrow.parquet as pq
    root = Path(root)
    materials = [r for r in pq.read_table(root / 'materials.parquet').to_pylist() if r['id'] in IDS]
    if {r['id']: r['name'] for r in materials} != IDS or any(r['kind'] != 'generic' for r in materials):
        raise ValueError('Det gennemgåede skrueudvalg er ændret.')
    observations = ds.dataset(root / 'observations', format='parquet', partitioning=None).to_table(
        filter=ds.field('material_id').isin(IDS) & (ds.field('property') == 'climate_change')).to_pylist()
    source_ids = {r['source_id'] for r in materials + observations}
    sources = [r for r in pq.read_table(root / 'sources.parquet').to_pylist() if r['id'] in source_ids]
    if {r['id'] for r in sources} != source_ids or len(sources) != 2:
        raise ValueError('Skrueudvalget mangler en kilde.')
    if any(r['license'] != 'Free of charge for all users and uses' or r['license_status'] != 'verified' for r in sources):
        raise ValueError('Kildernes registrerede vilkår er ændret; gennemgå viderebrug igen.')
    records = []
    for material in sorted(materials, key=lambda r: r['id']):
        rows = sorted([r for r in observations if r['material_id'] == material['id']], key=lambda r: r['module'])
        expected = ['A1-A3', 'C1', 'C2', 'D']
        if material['name'] == 'Galvanized steel screws':
            expected.insert(3, 'C3')
        if [r['module'] for r in rows] != expected:
            raise ValueError('Kildens modulomfang er ændret. Manglende faser må ikke blive nul.')
        for row in rows:
            c = json.loads(row['conditions_json'])
            if (row['source_id'] != material['source_id'] or row['method'] != INDICATOR
                    or row['unit'] != 'kg CO2 eq.' or row['declared_unit'] != 'kg' or row['basis'] != '1.0 kg'
                    or c['declared_amount'] != 1 or c['declared_references'] != [{
                        'exchange_index': 0, 'amount': 1.0, 'unit': 'kg', 'name': 'Mass',
                        'exchange_mean_amount': 1.0, 'resulting_flow_amount': 1.0}]
                    or c['standards'] != ['EN 15804+A2 (EF 3.1)'] or c['dataset_version'] != '20.26.070'
                    or c['geography'] != 'DE' or c['reference_year'] != 2023 or c['valid_until'] != 2026):
                raise ValueError('Skruekildens indikator, reference eller betingelser er ændret.')
        records.append({'material': material, 'observations': rows})
    return {'schema_version': 1, 'scope': 'ÖKOBAUDAT: to generiske skrue-referencer, GWP-total (EF 3.1)',
            'material_count': 2, 'observation_count': len(observations),
            'parquet_manifest_sha256': hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest(),
            'sources': sorted(sources, key=lambda r: r['id']), 'records': records}


def encoded(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = encoded(export_fasteners())
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != content:
            parser.exit(1, 'Browserens skruedata matcher ikke det gennemgåede Parquet-udsnit.\n')
        print('2 skrue-referencer / 9 GWP-total-observationer matcher Parquet.')
    else:
        OUTPUT.write_text(content, encoding='utf-8')
        print(f'Wrote {OUTPUT.relative_to(ROOT)} ({len(content.encode())} bytes)')
