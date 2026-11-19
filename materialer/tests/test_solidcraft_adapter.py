import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solidcraft_adapter',ROOT/'adapters/solidcraft.py')
solidcraft=importlib.util.module_from_spec(spec);spec.loader.exec_module(solidcraft)
MODELS=ROOT/'examples/models/solidcraft'


class NormalizationTests(unittest.TestCase):
    def test_no_bbox_volume_or_default_material_is_fabricated(self):
        body={'name':'OpenBody','closed':False,'material':'Default','bbox':{'min':[0,0,0],'max':[100,200,300]},'area_mm2':220000}
        elements,warnings=solidcraft.normalize_measurement({'bodies':[body]})
        self.assertIsNone(elements[0]['volume_m3'])
        self.assertIsNone(elements[0]['material_name'])
        self.assertIsNone(elements[0]['area_m2'])
        self.assertEqual(elements[0]['surface_area_m2'],0.22)
        self.assertEqual(elements[0]['dimensions_m'],{'x':0.1,'y':0.2,'z':0.3})
        self.assertEqual({w['code'] for w in warnings},{'material_unspecified','volume_unavailable'})

    def test_unphysical_quantities_and_failed_geometry_do_not_silently_pass(self):
        elements,warnings=solidcraft.normalize_measurement({'bodies':[{'name':'Bad','closed':True,'volume_mm3':float('nan'),'material':'Explicit','area_mm2':-1}]})
        self.assertIsNone(elements[0]['volume_m3'])
        self.assertIsNone(elements[0]['surface_area_m2'])
        self.assertIn('volume_unavailable',{w['code'] for w in warnings})
        with self.assertRaisesRegex(ValueError,'failed feature'):
            solidcraft.normalize_measurement({'bodies':[],'timeline':[{'name':'Cut','error':'invalid cut'}]})

    def test_script_json_is_not_an_inert_model(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'commands.json';path.write_text('{"commands":[]}')
            with self.assertRaisesRegex(ValueError,'command-script JSON'):
                solidcraft.extract(path)


@unittest.skipUnless(shutil.which('solidcraft-cli'),'Solidcraft CLI is required for live model integration checks')
class LiveModelTests(unittest.TestCase):
    def test_actual_volumes_and_material_assignments_match_analytic_controls(self):
        controls=json.loads((MODELS/'expected.json').read_text())
        self.assertEqual(len(controls['cases']),6)
        for case in controls['cases']:
            with self.subTest(case=case['id']):
                path=MODELS/case['model'];before=hashlib.sha256(path.read_bytes()).hexdigest()
                result=solidcraft.extract(path);element=result['elements'][0]
                self.assertEqual(element['id'],case['element_id'])
                self.assertEqual(element['material_name'],case['material'])
                self.assertAlmostEqual(element['volume_m3'],case['expected_volume_m3'],places=12)
                self.assertEqual(element['dimensions_m'],dict(zip(['x','y','z'],[v/1000 for v in case['dimensions_mm']])))
                self.assertIsNone(element['area_m2'])
                self.assertFalse(result['warnings'])
                self.assertEqual(result['model']['sha256'],before)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
                self.assertEqual(result['extraction']['raw_reply']['bodies'][0]['measured_by'],'smlib')

    def test_unknown_material_is_reported_even_when_app_supplies_default_density(self):
        result=solidcraft.extract(MODELS/'unknown.sc')
        self.assertIsNone(result['elements'][0]['material_name'])
        self.assertEqual(result['elements'][0]['volume_m3'],0.001)
        self.assertEqual(result['extraction']['raw_reply']['bodies'][0]['material'],'Default')
        self.assertIn('material_unspecified',{w['code'] for w in result['warnings']})

if __name__=='__main__':unittest.main()
