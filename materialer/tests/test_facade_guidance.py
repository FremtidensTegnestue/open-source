import copy
import json
from pathlib import Path
import tempfile
import unittest

import facade_guidance as g
import facade_live
from test_facade import sample,FakeClimate
import facade


class GuidanceTests(unittest.TestCase):
    def test_unknown_remains_unknown_in_budget_and_replacement_plan(self):
        r=facade.evaluate(sample(),FakeClimate());v=g.overview(r,r,g.defaults())
        self.assertEqual(v['priced_lines'],0)
        self.assertIsNone(v['price_per_m2'])
        self.assertIsNone(v['budget_difference'])
        self.assertTrue(all(x['replacement_count'] is None for x in v['lifetimes']))
        self.assertNotIn('disassembly',[x['id'] for x in v['areas']])

    def test_replacement_at_end_is_excluded(self):
        self.assertEqual(g.replacement_years(50,25),[25])
        self.assertEqual(g.replacement_years(50,50),[])
        self.assertEqual(g.replacement_years(50,20),[20,40])
        self.assertIsNone(g.replacement_years(50,None))

    def test_lifespan_does_not_create_climate_credits_or_technical_approval(self):
        r=facade.evaluate(sample(),FakeClimate());before=copy.deepcopy(r)
        s=g.defaults();s.update(period_years=50,dfd_requested=True)
        s['lifetimes']['plywood']={'years':25,'reference':'TEST project assumption'}
        s['evidence']['fire']={'status':'recorded','reference':'TEST document, not assessed'}
        v=g.overview(r,r,s)
        self.assertEqual(r,before)
        self.assertEqual(next(x for x in v['lifetimes'] if x['id']=='plywood')['replacement_years'],[25])
        self.assertIn('disassembly',[x['id'] for x in v['areas']])
        self.assertIn('ikke en teknisk godkendelse',v['notes'][-1])

    def test_known_subtotal_below_limit_is_not_claimed_within_budget(self):
        r=facade.evaluate(sample(),FakeClimate());s=g.defaults();s['budget_excl_vat']=10000
        v=g.overview(r,r,s)
        self.assertFalse(v['known_above_budget'])
        self.assertIsNone(v['budget_difference'])
        r['budget']['known_subtotal_excl_vat']='11000'
        self.assertTrue(g.overview(r,r,s)['known_above_budget'])

    def test_invalid_values_unreferenced_life_and_unsupported_keys_rejected(self):
        cases=[]
        for key,value in [('period_years',0),('budget_excl_vat',float('nan')),('dfd_requested',1)]:
            s=g.defaults();s[key]=value;cases.append(s)
        s=g.defaults();s['lifetimes']['wood']={'years':25,'reference':''};cases.append(s)
        s=g.defaults();s['evidence']['fire']={'status':'not_applicable','reference':''};cases.append(s)
        s=g.defaults();s['automatic_approval']=True;cases.append(s)
        for s in cases:
            with self.assertRaises(ValueError):g.validate(s)

    def test_every_known_field_is_stored_without_cross_project_writes(self):
        class Control:
            def call(self,*args):return {'document_id':'test','revision':1}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'project.json';p.write_text(json.dumps({'project_directory':d,'project_id':'test','engine':{}}))
            live=facade_live.LiveFacade(p,control=Control(),climate=FakeClimate())
            live.state={'status':'current'};live.version=Control().call();live.input_key='v1'
            live.result=facade.evaluate(sample(),FakeClimate());live.reference=copy.deepcopy(live.result)
            s=g.defaults();s['period_years']=50
            live.update_settings('v1',s)
            self.assertEqual(live.settings['revision'],1)
            with self.assertRaises(ValueError):live.update_settings('v1',s)
            with self.assertRaises(ValueError):live.update_settings('old',live.settings)
            reopened=facade_live.LiveFacade(p,control=Control(),climate=FakeClimate())
            self.assertEqual(reopened.settings,live.settings)
            external=copy.deepcopy(live.settings);external['budget_excl_vat']=12345
            live.settings_path.write_text(json.dumps(external))
            with self.assertRaises(ValueError):live.update_settings('v1',live.settings)
            self.assertEqual(json.loads(live.settings_path.read_text()),external)


if __name__=='__main__':unittest.main()
