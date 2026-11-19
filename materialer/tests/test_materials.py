import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('materials', Path(__file__).resolve().parents[1] / 'materials.py')
materials = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materials)

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'data/staging/fixture'
        self.stage.mkdir(parents=True)
        self.raw = self.root / 'data/raw/fixture/table.txt'
        self.raw.parent.mkdir(parents=True)
        self.raw.write_text('pine density 470 kg/m3; module D -12 kg CO2-eq\n')
        self.db = self.root / 'data/materials.sqlite'
        self.source = dict(id='fixture:source', title='Original table', publisher='Test', url='https://example.org/table', retrieved_at='2026-11-17T00:00:00Z', local_path='data/raw/fixture/table.txt', sha256=hashlib.sha256(self.raw.read_bytes()).hexdigest(), license='unknown', license_status='unknown')
        self.material = dict(id='fixture:pine', name='Fyrretræ', aliases=['pine'], kind='generic', category='wood', source_id='fixture:source', source_locator='line 1')
        self.obs = dict(id='fixture:pine:density', material_id='fixture:pine', property='density', value=470, value_text='470', unit='kg/m3', source_id='fixture:source', source_locator='line 1', conditions={'moisture_content_percent':12})
        self.write([self.obs])

    def write(self, observations):
        for name, records in [('sources',[self.source]),('materials',[self.material]),('observations',observations)]:
            (self.stage / (name+'.jsonl')).write_text(''.join(json.dumps(x)+'\n' for x in records))

    def test_numeric_conditions_provenance_and_negative_module_are_preserved(self):
        second = dict(self.obs, id='fixture:pine:D', property='gwp', value=-12, value_text='-1.2E1', unit='kg CO2-eq', module='D', declared_unit='1 m3')
        self.write([self.obs, second])
        result = materials.build(self.root,self.db)
        self.assertEqual(result['observations_by_dataset'],{'fixture':2})
        with materials.connect(self.db) as db:
            self.assertTrue(materials.verify(db,self.root)['ok'])
            obs=materials.rows(db,'SELECT * FROM observations WHERE module=?',['D'])[0]
            self.assertEqual(obs['value'],-12)
            self.assertEqual(obs['value_text'],'-1.2E1')
            self.assertEqual(obs['conditions']['moisture_content_percent'],12)
            self.assertEqual(obs['source_locator'],'line 1')
            self.assertEqual(db.execute('SELECT count(*) FROM observations').fetchone()[0],2)
            self.assertIn('fyrretrae',db.execute('SELECT search_text FROM materials').fetchone()[0])

    def test_invalid_original_does_not_replace_good_database(self):
        materials.build(self.root,self.db)
        old=self.db.read_bytes()
        self.raw.write_text('Changed source')
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):
            materials.build(self.root,self.db)
        self.assertEqual(old,self.db.read_bytes())
        self.assertFalse(self.db.with_name('materials.sqlite.building').exists())

    def test_database_only_does_not_claim_original_source_verification(self):
        materials.build(self.root, self.db)
        self.raw.unlink()
        with materials.connect(self.db) as db:
            limited = materials.verify(db, self.root, database_only=True)
            self.assertTrue(limited['ok'])
            self.assertEqual(limited['original_files_checked'], 0)
            self.assertFalse(limited['original_sources_verified'])
            self.assertEqual(limited['scope'], 'database_only')
            self.assertFalse(materials.verify(db, self.root)['ok'])

    def test_unknown_source_and_nan_are_rejected(self):
        self.write([dict(self.obs,source_id='absent')])
        with self.assertRaisesRegex(ValueError,'unknown material/source'):
            materials.build(self.root,self.db)
        self.write([dict(self.obs,value=float('nan'))])
        with self.assertRaises(ValueError):
            materials.build(self.root,self.db)

    def test_original_value_text_is_required(self):
        obs = dict(self.obs)
        del obs["value_text"]
        self.write([obs])
        with self.assertRaisesRegex(ValueError, "Missing original value"):
            materials.build(self.root,self.db)

    def test_missing_is_not_turned_into_zero(self):
        missing=dict(self.obs,value=None,value_text='MND',data_status='not_declared')
        self.write([missing]);materials.build(self.root,self.db)
        with materials.connect(self.db) as db:
            row=db.execute('SELECT value,value_text FROM observations').fetchone()
            self.assertIsNone(row[0]);self.assertEqual(row[1],'MND')

    def test_duplicate_ids_and_escaped_paths_are_rejected(self):
        self.write([self.obs,self.obs])
        with self.assertRaises(sqlite3.IntegrityError):materials.build(self.root,self.db)
        self.source['local_path']='../outside';self.write([self.obs])
        with self.assertRaisesRegex(ValueError,'escapes repository'):materials.build(self.root,self.db)

if __name__=='__main__':unittest.main()
