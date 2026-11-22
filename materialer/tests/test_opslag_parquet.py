"""Keep the lightweight lookup bounded and source-bound, including non-numeric data."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import opslag_parquet
import pyarrow as pa
import pyarrow.parquet as pq


class ParquetLookupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        pq.write_table(pa.Table.from_pylist([dict(id='test:oak', name='TEST Egetræ',
                       dataset_id='test', kind='generic', category='wood')]), self.root / 'materials.parquet')

    def observations(self, source='test:source'):
        rows = [dict(id=f'test:observation:{i}', dataset_id='test', material_id='test:oak',
                     property='test:gwp', value=None if i == 0 else float(i), value_text='ND' if i == 0 else str(i),
                     unit='kg CO2e', declared_unit='1 m3', basis='TEST reference', module='A1-A3', method='TEST',
                     data_status='not_declared' if i == 0 else 'reported', conditions_json='{"scope":"test"}',
                     source_id=source, source_locator=f'TEST row {i}') for i in range(5)]
        folder = self.root / 'observations' / 'dataset_id=test'
        folder.mkdir(parents=True)
        pq.write_table(pa.Table.from_pylist(rows), folder / 'part-00000.parquet')
        sources = [dict(id=id_, title='TEST source', publisher='TEST publisher', url='https://example.invalid/test',
                        sha256='0' * 64, license='TEST rights', license_status='unknown') for id_ in ['test:source', 'test:unused']]
        pq.write_table(pa.Table.from_pylist(sources), self.root / 'sources.parquet')

    def test_empty_search_does_not_open_observation_database(self):
        result = opslag_parquet.lookup(self.root, term='no-such-material')
        self.assertEqual(result['material_matches'], 0)
        self.assertEqual(result['observations'], [])
        self.assertFalse(list(self.root.rglob('*.sqlite')))

    def test_excerpt_preserves_null_text_unit_conditions_and_source_rights(self):
        self.observations()
        result = opslag_parquet.lookup(self.root, term='EGETRÆ', observations=2)
        self.assertEqual(len(result['observations']), 2)
        row = result['observations'][0]
        self.assertIsNone(row['value'])
        self.assertEqual(row['value_text'], 'ND')
        self.assertEqual(row['declared_unit'], '1 m3')
        self.assertEqual(row['conditions_json'], '{"scope":"test"}')
        self.assertEqual([s['id'] for s in result['sources']], ['test:source'])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            opslag_parquet.display(result)
        self.assertIn('value: None', output.getvalue())
        self.assertIn('https://example.invalid/test', output.getvalue())
        self.assertIn('TEST rights', output.getvalue())

    def test_exact_id_and_invalid_limits(self):
        self.observations()
        self.assertEqual(opslag_parquet.lookup(self.root, material_id='test:oak')['material_matches'], 1)
        with self.assertRaises(ValueError):
            opslag_parquet.lookup(self.root, term='oak', observations=0)

    def test_missing_source_is_an_error(self):
        self.observations(source='test:missing')
        with self.assertRaisesRegex(ValueError, 'mangler sin kilde'):
            opslag_parquet.lookup(self.root, term='egetræ')

    def test_help_works_without_site_packages(self):
        result = subprocess.run([sys.executable, '-S', str(Path(opslag_parquet.__file__)), '--help'],
                                capture_output=True, text=True, check=True)
        self.assertIn('--material-id', result.stdout)


class ShippedParquetTests(unittest.TestCase):
    """Exercise the public beginner path against the files a download includes."""

    def test_all_shipped_parquet_files_match_the_manifest(self):
        manifest = json.loads((opslag_parquet.ROOT / 'manifest.json').read_text(encoding='utf-8'))
        for item in manifest['files']:
            with self.subTest(file=item['path']):
                path = opslag_parquet.ROOT / item['path']
                self.assertEqual(path.stat().st_size, item['bytes'])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item['sha256'])
                self.assertEqual(pq.read_metadata(path).num_rows, item['rows'])

    def test_oak_reference_keeps_its_unit_module_and_source(self):
        result = opslag_parquet.lookup(opslag_parquet.ROOT, material_id='br18:t7:G0407:row260')
        rows = {row['id']: row for row in result['observations']}
        density = rows['br18:t7:G0407:row260:mass']
        self.assertEqual(density['value'], 716.8)
        self.assertEqual(density['unit'], 'kg/m³')
        gwp = rows['br18:t7:G0407:row260:gwp:A1-A3']
        self.assertAlmostEqual(gwp['value'], -1008.75834622427)
        self.assertEqual(gwp['declared_unit'], '1 m³')
        self.assertEqual(gwp['module'], 'A1-A3')
        self.assertEqual(gwp['source_locator'], 'Sheet1!E260')
        self.assertEqual(gwp['source_id'], 'br18:source:table-7-2025.xlsx')
        self.assertEqual([s['id'] for s in result['sources']], [gwp['source_id']])
        self.assertTrue(result['sources'][0]['url'].startswith('https://'))
        self.assertTrue(result['sources'][0]['license_status'])

    def test_documented_cli_works_outside_the_project(self):
        env = dict(os.environ, PYTHONUTF8='1')
        with tempfile.TemporaryDirectory() as folder:
            for args, expected in [(['egetræ'], 'br18:t7:G0407:row260'),
                                   (['beton'], 'afgrænset uddrag'),
                                   (['--material-id', 'br18:t7:G0407:row260'], '716.8'),
                                   (['ft-no-match-81'], 'Ingen træf')]:
                with self.subTest(args=args):
                    result = subprocess.run([sys.executable, str(Path(opslag_parquet.__file__)), *args],
                                            cwd=folder, env=env, encoding='utf-8',
                                            capture_output=True, check=True)
                    self.assertIn(expected, result.stdout)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
