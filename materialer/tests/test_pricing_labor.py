import copy
from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pricing
from pricing_editor import BudgetEditor, server_for
from test_pricing import project, store, TODAY


def labor(**changes):
    row=dict(id='work',label='TEST arbejde',hours='10',hourly_rate='400',rate_basis='contractor_rate',employer_addon_percent=None,linked_line_ids=['film'],reference='FIKTIV timepris og timer')
    row.update(changes)
    return row


class LaborTests(unittest.TestCase):
    def test_work_total_and_person_hours(self):
        p=project();p['labor']=[labor(hours='8')]
        r=pricing.assess(p,store(),TODAY,True)
        self.assertEqual(r['known_labor_excl_vat'],'3200.00')
        self.assertEqual(r['forecast_excl_vat'],'4100.00')

    def test_gross_wage_needs_employer_additions(self):
        p=project();p['labor']=[labor(rate_basis='gross_wage',hourly_rate='200')]
        r=pricing.assess(p,store(),TODAY,True)
        self.assertIsNone(r['forecast_excl_vat'])
        self.assertIsNone(r['labor'][0]['additional_excl_vat'])
        p['labor'][0]['employer_addon_percent']='40'
        r=pricing.assess(p,store(),TODAY,True)
        self.assertEqual(r['known_labor_excl_vat'],'2800.00')
        self.assertEqual(r['labor'][0]['effective_hourly_cost'],'280.0')

    def test_contractor_rate_does_not_get_wage_addons_again(self):
        r=pricing.assess(dict(project(),labor=[labor(employer_addon_percent='40')]),store(),TODAY,True)
        self.assertEqual(r['known_labor_excl_vat'],'4000.00')

    def test_missing_hours_or_rate_is_not_free(self):
        for changes in ({'hours':None},{'hourly_rate':None}):
            r=pricing.assess(dict(project(),labor=[labor(**changes)]),store(),TODAY,True)
            self.assertIsNone(r['forecast_excl_vat'])
            self.assertIsNone(r['labor'][0]['additional_excl_vat'])

    def test_included_installation_not_charged_twice(self):
        r=pricing.assess(dict(project(),labor=[labor(included_in_line_id='film')]),store(),TODAY,True)
        self.assertEqual(r['forecast_excl_vat'],'900.00')
        self.assertEqual(r['labor'][0]['additional_excl_vat'],'0.00')
        with self.assertRaises(ValueError):pricing.assess(dict(project(),labor=[labor(included_in_line_id='absent')]),store(),TODAY,True)

    def test_no_duplicate_work_and_no_negative_cost(self):
        with self.assertRaises(ValueError):pricing.assess(dict(project(),labor=[labor(),labor()]),store(),TODAY,True)
        with self.assertRaises(ValueError):pricing.assess(dict(project(),labor=[labor(hours='-1')]),store(),TODAY,True)

    def test_reference_comparison_keeps_budget_and_identifies_new_coverage(self):
        p=dict(project(),labor=[labor()]);before=pricing.assess(p,store(),TODAY,True)
        after_input=copy.deepcopy(p);after_input['labor'][0]['hours']='8'
        after=pricing.assess(after_input,store(),TODAY,True)
        diff=pricing.compare_reports(before,after)
        self.assertEqual(diff['whole_forecast_delta_excl_vat'],'-800.00')
        self.assertEqual(after['budget'],before['budget'])
        p['labor'][0]['hours']=None;partial=pricing.assess(p,store(),TODAY,True)
        diff=pricing.compare_reports(partial,after)
        self.assertIsNone(diff['whole_forecast_delta_excl_vat'])
        self.assertEqual(diff['newly_priced'],[['labor','work']])


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.project=self.root/'project.json';self.store=self.root/'store.json';self.variant=self.root/'variant.json'
        self.project.write_text(json.dumps(dict(project(),labor=[labor()])))
        self.store.write_text(json.dumps(store()))
        self.editor=BudgetEditor(self.project,self.store,self.variant,TODAY,True)
        self.original=self.project.read_bytes()

    def tearDown(self):self.tmp.cleanup()

    def test_save_variant_and_reference_stays_byte_identical(self):
        _,result=self.editor.evaluate({'l0_hours':'8'},True)
        self.assertEqual(result['comparison']['whole_forecast_delta_excl_vat'],'-800.00')
        self.assertEqual(self.project.read_bytes(),self.original)
        self.assertEqual(json.loads(self.variant.read_text())['labor'][0]['hours'],'8')
        self.assertEqual(json.loads(self.variant.read_text())['budget']['amount_excl_vat'],'2000')

    def test_reopen_saved_variant_keeps_original_reference(self):
        self.editor.evaluate({'l0_hours':'8'},True)
        reopened=BudgetEditor(self.variant,self.store,self.root/'variant2.json',TODAY,True)
        self.assertEqual(reopened.initial_report['comparison']['whole_forecast_delta_excl_vat'],'-800.00')
        _,r=reopened.evaluate({'l0_hours':'9'},True)
        self.assertEqual(r['comparison']['whole_forecast_delta_excl_vat'],'-400.00')
        self.assertEqual(self.project.read_bytes(),self.original)

    def test_clear_field_and_invalid_value(self):
        _,result=self.editor.evaluate({'l0_hours':''})
        self.assertIsNone(result['forecast_excl_vat'])
        with self.assertRaises(ValueError):self.editor.evaluate({'l0_hours':'-1'})
        with self.assertRaises(ValueError):self.editor.evaluate({'unknown':'1'})

    def test_source_change_and_output_collision_rejected(self):
        self.project.write_bytes(self.original+b' ')
        with self.assertRaises(ValueError):self.editor.evaluate({'l0_hours':'8'})
        with self.assertRaises(ValueError):BudgetEditor(self.project,self.store,self.project,TODAY,True)

    def test_local_http_form_preview_save_and_origin_guard(self):
        server=server_for(self.editor)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}/{self.editor.token}'
        try:
            with urlopen(base) as response:self.assertIn('Arbejdstimer'.encode(),response.read())
            payload=urlencode({'l0_hours':'8'}).encode()
            with urlopen(Request(base+'/preview',data=payload)) as response:
                data=json.loads(response.read());self.assertEqual(data['comparison']['whole_forecast_delta_excl_vat'],'-800.00')
            with urlopen(Request(base+'/save',data=payload)) as response:self.assertEqual(response.status,200)
            self.assertTrue(self.variant.exists())
            with self.assertRaises(HTTPError):urlopen(Request(base+'/preview',data=payload,headers={'Origin':'https://other.example'}))
            self.assertEqual(self.project.read_bytes(),self.original)
        finally:server.shutdown();server.server_close();thread.join(timeout=2)


if __name__=='__main__':unittest.main()
