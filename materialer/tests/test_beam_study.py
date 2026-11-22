import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import beam_study as b

EXAMPLE=Path(__file__).resolve().parents[1]/'examples/beam-study/study.json'


class BeamStudyTests(unittest.TestCase):
    def setUp(self):self.s=json.loads(EXAMPLE.read_text());self.c=self.s['candidates'][0]

    def test_invalid_inputs_and_path_ids_stop_before_solver(self):
        edits=[('span_mm',float('nan')),('include_self_weight',1),('external_line_load_N_mm',-1)]
        for key,value in edits:
            s=copy.deepcopy(self.s);s[key]=value
            with self.assertRaises(ValueError):b.validate(s)
        self.c['id']='../outside'
        with self.assertRaises(ValueError):b.validate(self.s)

    def test_unknown_fields_and_reference_not_guessed(self):
        self.s['automatic_approval']=True
        with self.assertRaises(ValueError):b.validate(self.s)
        del self.s['automatic_approval'];self.s['reference_candidate']='absent'
        with self.assertRaises(ValueError):b.validate(self.s)

    def test_own_weight_is_explicit_and_source_density_is_not_used(self):
        r=b.mechanical(self.s,self.c)
        self.assertAlmostEqual(r['volume_m3'],.115*.405*5.6)
        self.assertAlmostEqual(r['structural_mass_kg'],r['volume_m3']*420)
        self.assertAlmostEqual(r['own_line_load_N_mm']*5600,r['structural_mass_kg']*9.81)
        self.s['include_self_weight']=False
        self.assertEqual(b.mechanical(self.s,self.c)['total_line_load_N_mm'],4.6)

    def test_reference_scales_with_load_and_inverse_stiffness(self):
        self.s['include_self_weight']=False
        u=b.mechanical(self.s,self.c)['beam_theory_mm']
        self.assertAlmostEqual(b.mechanical(self.s,self.c,.8)['beam_theory_mm'],u/.8)
        self.s['external_line_load_N_mm']*=2
        self.assertAlmostEqual(b.mechanical(self.s,self.c)['beam_theory_mm'],2*u)

    def test_unknown_price_and_changed_section_do_not_become_zero(self):
        self.assertIsNone(b.beam_price(self.s,self.c)['net_material_excl_vat'])
        self.c['price']={'amount_excl_vat_per_m':100,'section_mm':[95,450],
                         'observed_on':'2026-11-22','reference':'TEST estimate'}
        self.assertIsNone(b.beam_price(self.s,self.c)['net_material_excl_vat'])
        self.c['price']['section_mm']=[115,405]
        self.assertEqual(b.beam_price(self.s,self.c)['net_material_excl_vat'],'560.00')
        self.c['price']['amount_excl_vat_per_m']=0
        self.assertEqual(b.beam_price(self.s,self.c)['net_material_excl_vat'],'0.00')

    def test_missing_reference_or_criterion_is_unknown_not_approval(self):
        self.s['limits']={'deflection_mm':None,'max_height_mm':None,'reference':''}
        b.validate(self.s)
        r=b.checks(self.s,self.c,{'deflection_mm':3},{'deflection_mm':4})
        self.assertIsNone(r['baseline_deflection']);self.assertFalse(r['whole_design_verified'])
        self.s['limits']['deflection_mm']=10
        with self.assertRaises(ValueError):b.validate(self.s)

    def test_recipe_grain_load_and_overlapping_reaction_sets(self):
        with tempfile.TemporaryDirectory() as d:
            cmds,mid=b.recipe(self.s,self.c,.8,4,2,Path(d))
            material=next(x['params'] for x in cmds if x['command']=='model.material.create')
            self.assertEqual(material['elastic']['young'][0],9200)
            self.assertEqual(material['density'],420e-12)
            nodes={x['params']['label']:x['params']['xyz'] for x in cmds if x['command']=='mesh.node.add'}
            self.assertEqual(nodes[mid],[2800,202.5,0])
            sets={x['params']['name']:x['params'] for x in cmds if x['command']=='model.set.create'}
            self.assertIn(sets['Anchor']['nodes'][0],sets['Left']['nodes'])

    def test_native_balance_or_wrong_displacement_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);q=b.mechanical(self.s,self.c)['total_line_load_N_mm'];L=5600
            u=b.mechanical(self.s,self.c)['beam_theory_mm']
            (folder/'nodes.csv').write_text(f'node,x [mm],y [mm],uy [mm]\n1,0,0,0\n2,2800,202.5,{-u}\n3,5600,405,0\n')
            def reactions(total):
                (folder/'reactions.csv').write_text(f'set,fy [N],mz [N·mm]\nLeft,{q*L/2},0\nRight,{q*L/2},{q*L*L/2}\ntotal,{total},{q*L*L/2}\n')
            reactions(q*L);self.assertAlmostEqual(b.parse_analysis(folder,self.s,self.c,1,2)['deflection_mm'],u)
            reactions(q*L+100)
            with self.assertRaises(ValueError):b.parse_analysis(folder,self.s,self.c,1,2)

    def test_unknown_climate_is_not_zero_and_mislabelled_modules_stop(self):
        source={'material_id':'m','density_observation_id':'density','gwp_observations':{k:None for k in b.MODULES}}
        runtime={'engine':{'binary':'unused','root':'root','store':'store','snapshot':'fixed'},'climate_source':source}
        mass={'status':'ok','snapshot':'fixed','value':500,'unit':'kg','inputs':{'density':{'id':'density','material_id':'m','property_id':'property:density'}}}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(b,'call',return_value=json.dumps(mass)):
            r=b.climate(1,runtime,Path(d));self.assertIsNone(r['known_subtotal_kgCO2e'])
        source['gwp_observations']['A1-A3']='gwp'
        wrong={'status':'ok','snapshot':'fixed','value':20,'module':'C3','inputs':{'declared_basis':{'dimension':'volume'},'source_observation':{'id':'gwp','material_id':'m','property_id':'property:gwp_total','module':'C3'}}}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(b,'call',side_effect=[json.dumps(mass),json.dumps(wrong)]):
            with self.assertRaises(ValueError):b.climate(1,runtime,Path(d))

    def test_stale_or_modified_saved_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);source=p/'input.json';source.write_text('{}')
            b.write(p/'resultat.json',{'bound_files':{str(source):b.sha(source)}})
            (p/'rapport.html').write_text('saved')
            b.write(p/'status.json',{'status':'partial_screening','result_sha256':b.sha(p/'resultat.json'),'html_sha256':b.sha(p/'rapport.html')})
            self.assertTrue(b.check(p)['current'])
            source.write_text('{"changed":true}')
            with self.assertRaises(ValueError):b.check(p)


if __name__=='__main__':unittest.main()
