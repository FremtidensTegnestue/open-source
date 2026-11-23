"""Check the actual public browser excerpt against original Parquet observations."""
import hashlib
import json
from pathlib import Path
import unittest
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from scripts.build_browser_materials import DATA, OUTPUT, encoded, export_materials


class BrowserMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = export_materials()

    def test_shipped_export_is_reproducible(self):
        self.assertEqual(OUTPUT.read_text(encoding='utf-8'),encoded(self.data))
        self.assertEqual(self.data['material_count'],507)
        self.assertEqual(self.data['observation_count'],2535)
        self.assertEqual(self.data['parquet_manifest_sha256'],hashlib.sha256((DATA/'manifest.json').read_bytes()).hexdigest())

    def test_all_values_and_context_are_unchanged(self):
        records=self.data['records']
        ids=[r['material']['id'] for r in records]
        obs=ds.dataset(DATA/'observations',format='parquet',partitioning='hive').to_table(filter=ds.field('material_id').isin(ids)).to_pylist()
        self.assertEqual({r['id']:r for r in obs},{r['id']:r for rec in records for r in rec['observations']})
        mats=pq.read_table(DATA/'materials.parquet').to_pylist()
        self.assertEqual({r['id']:r for r in mats if r['id'] in ids},{r['material']['id']:r['material'] for r in records})

    def test_primary_source_matches_independently_checked_excel_hash(self):
        sources={s['id']:s for s in self.data['sources']}
        source=sources['br18:source:table-7-2025.xlsx']
        self.assertEqual(source['sha256'],'3ac0babdd803cc688e058c9b1096c9871c849362014d4da80564000b73bcdb18')
        self.assertEqual(source['license_status'],'unknown')
        self.assertIn('br18:source:table-7.html',sources)
        self.assertTrue(all(row['source_id'] in sources for rec in self.data['records'] for row in rec['observations']))

    def test_oak_and_annual_installations_keep_distinct_basis(self):
        oak=next(r for r in self.data['records'] if r['material']['id']=='br18:t7:G0407:row260')
        density=next(r for r in oak['observations'] if r['property']=='density')
        self.assertEqual((density['value'],density['unit']),(716.8,'kg/m³'))
        annual=[o for r in self.data['records'] for o in r['observations'] if 'year' in (o['unit'] or '')]
        self.assertEqual(len(annual),60)
        self.assertTrue(all(json.loads(o['conditions_json'])['record_scope']=='installation_area_reference_factor' for o in annual))
