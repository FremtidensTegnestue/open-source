"""Check the separate screw subset against Parquet, including all original context."""
import json
import unittest
from scripts.build_browser_fasteners import DATA, IDS, OUTPUT, encoded, export_fasteners


class BrowserFastenersTest(unittest.TestCase):
    def test_shipped_export_matches_parquet_exactly(self):
        self.assertEqual(OUTPUT.read_text(encoding='utf-8'), encoded(export_fasteners()))

    def test_only_reviewed_materials_and_nine_unchanged_climate_rows_are_exposed(self):
        import pyarrow.dataset as ds
        import pyarrow.parquet as pq
        data = json.loads(OUTPUT.read_text(encoding='utf-8'))
        original = {r['id']: r for r in pq.read_table(DATA / 'materials.parquet').to_pylist() if r['id'] in IDS}
        rows = ds.dataset(DATA / 'observations', format='parquet', partitioning=None).to_table(
            filter=ds.field('material_id').isin(IDS) & (ds.field('property') == 'climate_change')).to_pylist()
        self.assertEqual(len(rows), 9)
        self.assertEqual({r['id'] for r in rows}, {r['id'] for record in data['records'] for r in record['observations']})
        for record in data['records']:
            self.assertEqual(record['material'], original[record['material']['id']])
            self.assertEqual(record['observations'], sorted([r for r in rows if r['material_id'] == record['material']['id']], key=lambda r: r['module']))
        source_ids = {r['id'] for r in data['sources']}
        sources = [r for r in pq.read_table(DATA / 'sources.parquet').to_pylist() if r['id'] in source_ids]
        self.assertEqual(data['sources'], sorted(sources, key=lambda r: r['id']))

    def test_unreported_factors_are_not_inserted_as_zero(self):
        data = json.loads(OUTPUT.read_text(encoding='utf-8'))
        for record in data['records']:
            modules = {r['module'] for r in record['observations']}
            self.assertNotIn('C4', modules)
            if record['material']['name'] == 'Stainless steel screws':
                self.assertNotIn('C3', modules)
            else:
                self.assertEqual(next(r['value'] for r in record['observations'] if r['module'] == 'C3'), 0)


if __name__ == '__main__':
    unittest.main()
