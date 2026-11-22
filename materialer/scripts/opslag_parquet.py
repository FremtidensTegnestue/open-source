#!/usr/bin/env python3
"""Read a bounded material/source excerpt directly from the shipped Parquet base.

No SQLite build, source download, conversion or calculation is performed.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'data' / 'parquet'
FIELDS = ['id', 'material_id', 'property', 'value', 'value_text', 'unit',
          'declared_unit', 'basis', 'module', 'method', 'data_status',
          'conditions_json', 'source_id', 'source_locator']
SOURCE_FIELDS = ['id', 'title', 'publisher', 'url', 'sha256', 'license', 'license_status']


def lookup(root, term=None, material_id=None, limit=5, observations=12):
    if limit < 1 or observations < 1:
        raise ValueError('Grænserne skal være større end nul.')
    if bool(term) == bool(material_id):
        raise ValueError('Angiv enten et søgeord eller --material-id.')
    import pyarrow.dataset as ds
    import pyarrow.parquet as pq

    root = Path(root)
    materials = pq.read_table(root / 'materials.parquet',
                              columns=['id', 'dataset_id', 'name', 'kind', 'category']).to_pylist()
    hits = [m for m in materials if m['id'] == material_id] if material_id else [
        m for m in materials if term.casefold() in m['name'].casefold()]
    total = len(hits)
    hits = hits[:limit]
    result = dict(material_matches=total, materials=hits, observations=[], sources=[],
                  observation_limit=observations, scope='Parquet-grunddata; tillæg er ikke læst')
    if not hits:
        return result
    data = ds.dataset(root / 'observations', format='parquet', partitioning='hive')
    table = data.scanner(columns=FIELDS,
                         filter=ds.field('material_id').isin([m['id'] for m in hits])).head(observations)
    result['observations'] = table.to_pylist()
    ids = {row['source_id'] for row in result['observations']}
    sources = pq.read_table(root / 'sources.parquet', columns=SOURCE_FIELDS).to_pylist()
    result['sources'] = [source for source in sources if source['id'] in ids]
    if {source['id'] for source in result['sources']} != ids:
        raise ValueError('En vist observation mangler sin kilde i sources.parquet.')
    return result


def display(result):
    print(result['scope'])
    print(f"Materialer: {len(result['materials'])} vist af {result['material_matches']} navnetræf.")
    for material in result['materials']:
        print(f"  {material['id']} | {material['name']} | {material['kind']}")
    if not result['materials']:
        print('Ingen træf. Prøv et kortere søgeord eller et konkret materiale-ID.')
        return
    print(f"\nObservationer: {len(result['observations'])} vist (højst {result['observation_limit']}; afgrænset uddrag).")
    for row in result['observations']:
        print(f"\n  {row['id']} | {row['property']}")
        for group in [('value', 'value_text', 'unit'), ('declared_unit', 'basis', 'module'),
                      ('method', 'data_status', 'conditions_json'), ('material_id', 'source_id', 'source_locator')]:
            print('    ' + ' | '.join(f'{key}: {row[key]}' for key in group))
    print('\nKilder til de viste observationer:')
    for source in result['sources']:
        print(f"\n  {source['id']}")
        for key in SOURCE_FIELDS[1:]:
            print(f"    {key}: {source[key]}")
    print('\nNavnetræf er kandidater. Opslaget vælger ikke et produkt og beregner ikke klima.')
    print('None i value er ingen enkelt numerisk værdi; læs også value_text og data_status.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('term', nargs='?', help='Ord eller tekst i materialets navn, fx beton eller egetræ')
    parser.add_argument('--material-id', help='Vis et bestemt ID fra søgeresultatet')
    parser.add_argument('--limit', type=int, default=5, help='Højst så mange materialer (standard: 5)')
    parser.add_argument('--observations', type=int, default=12, help='Højst så mange observationer (standard: 12)')
    args = parser.parse_args()
    if bool(args.term) == bool(args.material_id):
        parser.error('Angiv enten et søgeord eller --material-id.')
    try:
        display(lookup(ROOT, args.term, args.material_id, args.limit, args.observations))
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith('pyarrow'):
            parser.exit(1, 'Mangler pyarrow. Installér i dit lokale Python-miljø: python -m pip install pyarrow==26.0.1\n')
        raise
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Opslag kunne ikke gennemføres: {exc}\n')


if __name__ == '__main__':
    main()
