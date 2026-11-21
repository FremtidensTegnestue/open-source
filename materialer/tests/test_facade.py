"""Facade contract tests; native geometry tests use SolidCraft CLI when available."""
import copy
from datetime import date
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import facade
import facade_live
import pricing

ROOT=Path(__file__).resolve().parents[1]
APP_CLI='/Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli'
CLI=os.environ.get('SOLIDCRAFT_CLI') or (APP_CLI if Path(APP_CLI).is_file() else shutil.which('solidcraft-cli') or '')


class FakeClimate:
    """Unit-test factors only; real Rust is exercised separately in the live acceptance."""
    config={'snapshot':'test-only'}
    sources={'windboard':{'observations':[{'property_id':'property:density','value':255,
        'unit':'kg/m³','id':'fixture-density'}]}}
    calls=0
    def verify(self):pass
    def calculate(self,source,quantity,unit):
        return {m:quantity for m in facade.MODULES},{m:{'observation_id':'TEST','source':{}} for m in facade.MODULES}


def sample():
    return {'params':{k:v for k,(v,u) in facade.PARAMS.items()},'volumes':{
        'frame':.10668375,'vent':.01512,'plywood':.12672,'windboard':.06912,
        'slate':.0438016,'slate_battens':.0216,'wood':0},'active':'skifer',
        'element_id':'test-facade','bodies':54,'geometry_sha256':'test-geometry'}


class EstimateTests(unittest.TestCase):
    def test_unknown_price_is_not_a_free_complete_budget(self):
        r=facade.evaluate(sample(),FakeClimate())
        self.assertIsNone(r['budget']['forecast_excl_vat'])
        self.assertEqual(r['budget']['status'],'partial_budget')
        self.assertEqual(r['budget']['known_subtotal_excl_vat'],'0.00')

    def test_delivery_can_be_known_while_all_material_prices_are_unknown(self):
        s=sample();s['params'].update(Prisgrundlag='TEST local estimate',Levering=500)
        r=facade.evaluate(s,FakeClimate())
        self.assertEqual(r['budget']['known_subtotal_excl_vat'],'500.00')
        self.assertIsNone(r['budget']['forecast_excl_vat'])

    def test_dated_local_estimates_need_no_fabricated_url_and_are_escaped(self):
        s=sample();s['params']['Prisgrundlag']='TEST <script>bad</script>'
        for k,v in s['params'].items():
            if v == -1:s['params'][k]=0
        r=facade.evaluate(s,FakeClimate())
        self.assertEqual(r['budget']['forecast_excl_vat'],'0.00')
        page=pricing.render(r['budget'])
        self.assertNotIn('<script>bad</script>',page)
        self.assertIn('&lt;script&gt;bad&lt;/script&gt;',page)
        option=r['budget']['lines'][0]['options'][0]
        self.assertIsNone(option['source_url'])
        self.assertEqual(option['kind'],'estimate')

    def test_no_price_carries_silently_to_another_board_thickness(self):
        s=sample();s['params']['Prisgrundlag']='TEST own estimate'
        for k,v in s['params'].items():
            if v == -1:s['params'][k]=1
        before=facade.evaluate(s,FakeClimate())
        self.assertIsNotNone(before['budget']['forecast_excl_vat'])
        s['params']['Krydsfiner_tykkelse']=18
        after=facade.evaluate(s,FakeClimate())
        self.assertIsNone(after['budget']['forecast_excl_vat'])
        self.assertIsNone(next(x for x in after['budget']['lines'] if x['id']=='Pris_krydsfiner_m2')['selected'])

    def test_one_screw_product_is_purchased_once_for_both_applications(self):
        r=facade.evaluate(sample(),FakeClimate())
        screws=[x for x in r['budget']['lines'] if x['id']=='Pris_skruer_stk']
        self.assertEqual(len(screws),1)
        self.assertEqual(float(screws[0]['required_quantity']),284)
        self.assertEqual(r['rows'][3]['quantity_conversion']['density_observation_id'],'fixture-density')

    def test_invalid_geometry_or_nan_is_rejected(self):
        for name,value in [('Facade_bredde',3000),('Beklaedning',.3),('Timepris',float('nan'))]:
            p=sample()['params'];p[name]=value
            with self.assertRaises(ValueError):facade.validate_params(p)


@unittest.skipUnless(Path(CLI).is_file(),'SolidCraft CLI not installed')
class NativeFacadeTests(unittest.TestCase):
    def run_model(self,changes=None,extra=None):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            commands=[]
            if changes:commands.append({'command':'parameters.change','params':{'changes':changes}})
            commands+=extra or []
            (p/'commands.json').write_text(json.dumps({'commands':commands}))
            model=p/'model.json';measured=p/'measured.json'
            subprocess.run([CLI,'run',str(p/'commands.json'),'--in',str(ROOT/'examples/facade/model.json'),
                            '--save',str(model),'--quiet'],check=True,capture_output=True,text=True)
            subprocess.run([CLI,'eval','--in',str(model),'--json-out',str(measured)],
                           check=True,capture_output=True,text=True)
            data=json.loads(measured.read_text())
            # CLI measurement omits document metadata; exported JSON remains authoritative.
            data['metadata']=json.loads(model.read_text())['metadata']
            data['timeline']=data.get('timeline',[])
            return facade.collect({'text':model.read_text()},data,'example-facade')

    def test_real_geometry_width_and_height_not_a_precomputed_row(self):
        r=self.run_model({'Facade_bredde':'1991 mm','Facade_hoejde':'2663 mm'})
        self.assertEqual(r['bodies'],54)
        self.assertAlmostEqual(r['volumes']['plywood'],1.991*2.663*.022)

    def test_real_wood_choice_and_thickness(self):
        r=self.run_model({'Beklaedning':'1','Trae_tykkelse':'28 mm'})
        self.assertEqual(r['bodies'],30)
        self.assertEqual(r['active'],'trae')
        self.assertAlmostEqual(r['volumes']['wood'],16*2.4*.028*.148)

    def test_logical_mapping_survives_native_body_rename(self):
        r=self.run_model(extra=[{'command':'body.rename','params':{'body':'F56_Krydsfiner','name':'Min plade'}}])
        self.assertEqual(r['groups']['plywood'],['Min plade'])

    def test_unmapped_body_and_unmapped_material_stop_calculation(self):
        for command in [
            {'command':'solid.box','params':{'length':100,'width':100,'height':100,'corner':[4000,0,0]}},
            {'command':'material.assign','params':{'bodies':['F56_Krydsfiner'],'material':'FT56_timber'}}]:
            with self.assertRaises(ValueError):self.run_model(extra=[command])


class ViewTests(unittest.TestCase):
    def test_result_from_previous_tab_is_not_displayed_or_saved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'project.json';p.write_text(json.dumps({'project_directory':d,'project_id':'test','engine':{}}))
            class Control:
                def call(self,*args):return {'document_id':'another-tab','revision':2}
            live=facade_live.LiveFacade(p,control=Control(),climate=FakeClimate())
            live.state={'status':'current'};live.version={'document_id':'old-tab','revision':1}
            live.result={'secret-old-result':1};live.input_key='old'
            self.assertIsNone(live.view()['result'])
            with self.assertRaises(ValueError):live.save('old')

    def test_changed_area_is_not_called_same_function_saving(self):
        before=facade.evaluate(sample(),FakeClimate());after=copy.deepcopy(before);after['area_m2']=4
        c=facade_live.comparison(before,after)
        self.assertFalse(c['same_area'])
        self.assertIn('ikke en gevinst',c['note'])


if __name__=='__main__':unittest.main()
