import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bimcraft_adapter_tested', ROOT / 'adapters/bimcraft.py')
bimcraft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bimcraft)
MODELS = ROOT / 'examples/models/bimcraft'

class NormalizationTests(unittest.TestCase):
    def test_import_losses_survive_empty_inspect_warnings(self):
        summary = {'format': 'IFC2X3', 'elements': {'beam': 1}, 'skipped': ['IFCBEAM #81'], 'generic': 2, 'moved': [3000, -1000]}
        out = bimcraft.normalize({'types': {}, 'warnings': []}, [], {}, 'test', [], summary)
        self.assertEqual(out['extraction']['import_summary'], summary)
        self.assertEqual({w['code'] for w in out['warnings']}, {'ifc_import_skipped', 'ifc_import_generic'})
        self.assertTrue(all(w.get('severity') != 'notice' for w in out['warnings']))

    def test_no_name_guessing_and_no_missing_volume_estimate(self):
        inspect = {'types': {'floor': {'Concrete named type': {'thickness': 50}}}}
        out = bimcraft.normalize(inspect, [{'id':1,'category':'floor','type':'Concrete named type','area_m2':2,'thickness':50}], {}, 'test', [])
        self.assertIsNone(out['elements'][0]['material_name'])
        self.assertIsNone(out['elements'][0]['volume_m3'])
        self.assertEqual(out['elements'][0]['dimensions_m']['thickness'],0.05)
        self.assertEqual({w['code'] for w in out['warnings']},{'missing_material','missing_volume'})

    def test_mixed_layers_override_a_structure_material_shortcut(self):
        inspect={'types':{'floor':{'layered':{'layers':[{'material':'Timber','thickness':20},{'material':'Concrete','thickness':100}]}}}}
        out=bimcraft.normalize(inspect,[{'id':1,'category':'floor','type':'layered','material':'Concrete','volume_m3':0.12}],{},'test',[])
        self.assertIsNone(out['elements'][0]['material_name'])
        self.assertIn('mixed_material_layers',{w['code'] for w in out['warnings']})

    def test_same_explicit_material_in_multiple_layers_can_use_total(self):
        inspect={'types':{'floor':{'same':{'layers':[{'material':'Timber','thickness':20},{'material':'Timber','thickness':100}]}}}}
        out=bimcraft.normalize(inspect,[{'id':1,'category':'floor','type':'same','volume_m3':0.12}],{},'test',[])
        self.assertEqual(out['elements'][0]['material_name'],'Timber')
        self.assertEqual(out['elements'][0]['source_ref']['volume_rounding_increment_m3'],0.001)

@unittest.skipUnless(shutil.which('bimcraft-cli'),'bimcraft-cli is not installed')
class ActualBIMcraftTests(unittest.TestCase):
    def test_five_control_quantities_materials_and_source_unchanged(self):
        path=MODELS/'controls.bimc';before=hashlib.sha256(path.read_bytes()).hexdigest()
        out=bimcraft.extract(path,page_size=2)
        self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(out['model']['sha256'],before)
        expected=json.loads((MODELS/'expected.json').read_text())
        byname={e['name']:e for e in out['elements']}
        self.assertEqual(len(byname),5)
        self.assertGreater(len(out['extraction']['commands']),1)
        for case in expected['cases']:
            with self.subTest(case=case['case_id']):
                row=byname[case['name']]
                self.assertEqual(row['material_name'],case['material_name'])
                self.assertAlmostEqual(row['volume_m3'],case['expected_volume_m3'],places=12)
                self.assertEqual(row['id'],case['element_id'])
        self.assertTrue(all(w['code']=='quantity_rounding' for w in out['warnings']))

    def test_authored_ifc_control_import(self):
        out=bimcraft.extract(MODELS/'controls.ifc')
        self.assertEqual(len(out['elements']),5)
        byname={e['name']:e for e in out['elements']}
        for case in json.loads((MODELS/'expected.json').read_text())['cases']:
            self.assertEqual(byname[case['name']]['material_name'],case['material_name'])
            self.assertAlmostEqual(byname[case['name']]['volume_m3'],case['expected_volume_m3'],places=12)
        self.assertIn('ifc_import_context',{w['code'] for w in out['warnings']})

    def test_missing_and_mixed_material_are_not_filled(self):
        for name,code in [('missing-material','missing_material'),('mixed-layers','mixed_material_layers')]:
            with self.subTest(model=name):
                out=bimcraft.extract(MODELS/(name+'.bimc'))
                self.assertIsNone(out['elements'][0]['material_name'])
                self.assertIn(code,{w['code'] for w in out['warnings']})

    def test_rounding_is_preserved_and_exposed(self):
        out=bimcraft.extract(MODELS/'rounded-volume.bimc')
        row=out['elements'][0]
        self.assertEqual(row['volume_m3'],0.005)
        self.assertNotEqual(row['volume_m3'],0.0048)
        self.assertEqual(row['source_ref']['volume_rounding_increment_m3'],0.001)
        self.assertIn('quantity_rounding',{w['code'] for w in out['warnings']})

if __name__=='__main__':unittest.main()
