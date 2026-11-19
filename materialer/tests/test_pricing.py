"""Money and import boundaries, not supplier-format assumptions."""
import copy
import csv
from datetime import date
from decimal import Decimal
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pricing

TODAY = date(2026, 11, 19)


def offer(**changes):
    raw = dict(supplier_id='a', supplier_name='Test A', account_id='public', sku='A-1',
               product_id='test:film:0.2mm', mapping_reference='explicit fixture', source_url='https://example.test/a',
               observed_on='2026-11-19', review_on='2026-12-19', currency='DKK', unit='m2',
               kind='test', origin='nyt', availability='available', amount='500', price_quantity='100',
               purchase_step='100', minimum_quantity='0', tax_basis='incl_vat', vat_rate='0.25', price_basis='net')
    raw.update(changes)
    return raw


def store(*raws):
    values = [pricing.normalize_offer(r) for r in raws or [offer()]]
    return {'schema': 1, 'offers': [dict(x, received_at='2026-11-19T08:00:00+00:00') for x in values], 'imports': []}


def project():
    return {'schema': 1, 'scope_id': 'test-only-film', 'account_id': 'test-buyer',
            'currency': 'DKK', 'tax_basis': 'excl_vat',
            'budget': {'amount_excl_vat': '2000', 'revision': 'test-1', 'set_on': '2026-11-19'},
            'delivery': {'a': {'amount_excl_vat': '100', 'reference': 'test delivery'}},
            'lines': [{'id': 'film', 'label': 'TEST folie', 'product_id': 'test:film:0.2mm', 'unit': 'm2',
                       'net_quantity': '150', 'waste_rate': '0', 'origin': 'nyt', 'orders': [],
                       'selection': {'supplier_id': 'a', 'account_id': 'public', 'sku': 'A-1'}}]}


class PricingTests(unittest.TestCase):
    def test_normalization_preserves_gross_and_applies_tax_once(self):
        raw = offer()
        n = pricing.normalize_offer(raw)
        self.assertEqual(n['amount_excl_vat'], '4E+2')
        self.assertEqual(n['raw']['amount'], '500')
        self.assertEqual(raw['tax_basis'], 'incl_vat')
        self.assertEqual(pricing.normalize_offer(n['raw']), n)

    def test_list_discount_requires_evidence_and_no_double_discount(self):
        n = pricing.normalize_offer(offer(price_basis='list', discount_percent='20', discount_reference='test agreement'))
        self.assertEqual(Decimal(n['amount_excl_vat']), Decimal('320'))
        for changes in ({'price_basis': 'list', 'discount_percent': '20'}, {'discount_percent': '20'},
                        {'price_basis': 'list', 'discount_percent': '101', 'discount_reference': 'x'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                pricing.normalize_offer(offer(**changes))

    def test_ambiguous_tax_units_and_numbers_rejected(self):
        for changes in ({'tax_basis': 'unknown'}, {'tax_basis': 'incl_vat', 'vat_rate': None},
                        {'currency': 'EUR'}, {'unit': 'pakke'}, {'price_quantity': 0},
                        {'purchase_step': 0}, {'amount': 'NaN'}, {'amount': '-1'}, {'amount': True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                pricing.normalize_offer(offer(**changes))

    def test_purchase_steps_and_supplier_minimum_change_cheapest_goods(self):
        # A: 2*400=800; B: 1*700=700, despite B's higher price per m².
        s = store(offer(), offer(supplier_id='b', supplier_name='Test B', sku='B-1',
                                amount='700', price_quantity='150', purchase_step='150', tax_basis='excl_vat'))
        r = pricing.assess(project(), s, TODAY, True)
        self.assertEqual([o['goods_excl_vat'] for o in r['lines'][0]['options']], ['700.00', '800.00'])
        self.assertEqual(r['lines'][0]['selected']['supplier_id'], 'a')  # No automatic substitution.
        self.assertEqual(r['forecast_excl_vat'], '900.00')
        self.assertEqual(r['variance_excl_vat'], '-1100.00')
        s = store(offer(minimum_quantity='500'))
        self.assertEqual(pricing.assess(project(), s, TODAY, True)['lines'][0]['selected']['goods_excl_vat'], '2000.00')

    def test_partial_invoice_order_remainder_and_market_change(self):
        p = project()
        p['lines'][0]['net_quantity'] = '300'
        p['lines'][0]['orders'] = [dict(id='order-1', reference='test invoice+order', supplier_id='a',
                                      price_fixed=True, quantity='100', invoiced_quantity='40',
                                      invoiced_excl_vat='120', remaining_excl_vat='180')]
        a = pricing.assess(p, store(offer()), TODAY, True)
        b = pricing.assess(p, store(offer(amount='625')), TODAY, True)
        self.assertEqual(a['forecast_excl_vat'], '1200.00')  # 120+180+800+100.
        self.assertEqual(b['forecast_excl_vat'], '1400.00')  # Only unordered 200m² moves by 200.
        self.assertEqual(b['lines'][0]['actual_excl_vat'], '120.00')
        self.assertEqual(b['lines'][0]['committed_remaining_excl_vat'], '180.00')
        self.assertEqual(p['budget']['amount_excl_vat'], '2000')

    def test_unknown_price_quantity_delivery_or_scope_never_gives_complete_total(self):
        for change in ('selection', 'quantity', 'delivery', 'scope'):
            p = project()
            if change == 'selection': p['lines'][0]['selection'] = None
            if change == 'quantity': p['lines'][0]['net_quantity'] = None
            if change == 'delivery': p['delivery'] = {}
            if change == 'scope': p['unresolved_scope'] = ['Montage mangler']
            with self.subTest(change=change):
                r = pricing.assess(p, store(), TODAY, True)
                self.assertIsNone(r['forecast_excl_vat'])
                self.assertIsNone(r['variance_excl_vat'])
                self.assertEqual(r['budget_status'], 'unresolved')
                self.assertTrue(r['unresolved'])

    def test_expired_latest_does_not_resurrect_older_offer(self):
        old = offer(observed_on='2026-11-17')
        newer = offer(observed_on='2026-11-18', review_on='2026-11-18', amount='400')
        r = pricing.assess(project(), store(old, newer), TODAY, True)
        self.assertIsNone(r['forecast_excl_vat'])
        self.assertEqual(len(r['lines'][0]['options']), 1)
        self.assertIn('Pris skal opdateres', r['lines'][0]['options'][0]['issues'])

    def test_withdrawal_does_not_resurrect_previous_price(self):
        s = store(offer(observed_on='2026-11-17'), offer(observed_on='2026-11-18', availability='unavailable'))
        r = pricing.assess(project(), s, TODAY, True)
        self.assertIsNone(r['forecast_excl_vat'])

    def test_different_customer_product_unit_origin_and_test_data_are_not_compared(self):
        for changes in ({'account_id': 'other-buyer'}, {'product_id': 'different-film'},
                        {'unit': 'kg'}, {'origin': 'genbrug'}):
            with self.subTest(changes=changes):
                r = pricing.assess(project(), store(offer(**changes)), TODAY, True)
                self.assertEqual(r['lines'][0]['options'], [])
        self.assertEqual(pricing.assess(project(), store(), TODAY)['lines'][0]['options'], [])

    def test_future_observation_not_used(self):
        r = pricing.assess(project(), store(offer(observed_on='2026-11-20')), TODAY, True)
        self.assertEqual(r['lines'][0]['options'], [])

    def test_zero_requirement_does_not_buy_minimum_order(self):
        p = project(); p['lines'][0]['net_quantity'] = '0'
        r = pricing.assess(p, store(offer(minimum_quantity='100')), TODAY, True)
        self.assertEqual(r['forecast_excl_vat'], '0.00')
        self.assertEqual(r['delivery'], [])

    def test_budget_remains_unset_when_no_user_budget(self):
        p = project(); p['budget'] = None
        r = pricing.assess(p, store(), TODAY, True)
        self.assertEqual(r['budget_status'], 'not_set')
        self.assertIsNone(r['variance_excl_vat'])

    def test_known_overspend_detected_even_with_gaps(self):
        p = project(); p['budget']['amount_excl_vat'] = '100';p['unresolved_scope'] = ['Montage']
        r = pricing.assess(p, store(), TODAY, True)
        self.assertEqual(r['budget_status'], 'known_cost_above_budget')
        self.assertIsNone(r['forecast_excl_vat'])

    def test_duplicate_order_or_overinvoice_rejected(self):
        order = dict(id='x', reference='fixture', supplier_id='a', price_fixed=True,
                     quantity='40', invoiced_quantity='20', invoiced_excl_vat='30', remaining_excl_vat='30')
        p = project();p['lines'][0]['orders'] = [order, order]
        with self.assertRaises(ValueError):pricing.assess(p, store(), TODAY, True)
        p['lines'][0]['orders'] = [dict(order, invoiced_quantity='41')]
        with self.assertRaises(ValueError):pricing.assess(p, store(), TODAY, True)

    def test_unknown_remaining_commitment_not_assumed_zero(self):
        p = project();p['lines'][0]['orders'] = [dict(id='x',reference='fixture',supplier_id='a',price_fixed=True,
          quantity='150',invoiced_quantity='20',invoiced_excl_vat='30',remaining_excl_vat=None)]
        r = pricing.assess(p, store(), TODAY, True)
        self.assertIsNone(r['forecast_excl_vat'])
        self.assertIn('Resterende ordrepris mangler',r['lines'][0]['issues'])

    def test_import_idempotent_raw_preserved_and_invalid_batch_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'store.json'
            raw = json.dumps({'schema':1,'mode':'observations','offers':[offer()]}).encode()
            first = pricing.import_bytes(raw,'json',p,'fixture.json')
            before = p.read_bytes()
            again = pricing.import_bytes(raw,'json',p,'fixture.json')
            self.assertEqual(first['added'],1);self.assertTrue(again['duplicate'])
            self.assertEqual(p.read_bytes(),before)
            d = json.loads(before)
            self.assertEqual(Path(d['imports'][0]['original']).read_bytes(),raw)
            bad = json.dumps({'schema':1,'mode':'observations','offers':[offer(sku='new'),offer(unit='unknown')]}).encode()
            with self.assertRaises(ValueError):pricing.import_bytes(bad,'json',p,'bad.json')
            self.assertEqual(p.read_bytes(),before)

    def test_delta_mode_not_misinterpreted_as_full_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                pricing.import_bytes(b'{"schema":1,"mode":"delta","offers":[]}', 'json',Path(tmp)/'s.json','x')

    def test_csv_import_and_history_keep_absent_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'s.json'
            raw = offer(); f = io.StringIO();w = csv.DictWriter(f,fieldnames=list(raw));w.writeheader();w.writerow(raw)
            pricing.import_bytes(f.getvalue().encode(),'csv',p,'fixture.csv')
            pricing.import_bytes(json.dumps({'schema':1,'mode':'observations','offers':[offer(sku='new')]}).encode(),'json',p,'new.json')
            self.assertEqual(len(json.loads(p.read_text())['offers']),2)

    def test_delivery_counted_once_per_supplier_and_unknown_blocks_total(self):
        p = project();other = copy.deepcopy(p['lines'][0]);other.update(id='other',product_id='other',selection={'supplier_id':'a','account_id':'public','sku':'other'})
        p['lines'].append(other)
        r = pricing.assess(p,store(offer(),offer(product_id='other',sku='other')),TODAY,True)
        self.assertEqual(r['forecast_excl_vat'],'1700.00')

    def test_tampered_observation_rejected(self):
        s = store();s['offers'][0]['amount_excl_vat']='1'
        with self.assertRaises(ValueError):pricing.assess(project(),s,TODAY,True)

    def test_fetch_uses_format_limit_and_does_not_erase_store_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'s.json'
            raw = json.dumps({'schema':1,'mode':'observations','offers':[offer()]}).encode()
            class Response:
                def __enter__(self):return self
                def __exit__(self,*_):pass
                def geturl(self):return 'https://example.test/prices.json'
                def read(self,limit):return raw[:limit]
            with patch('pricing.urlopen',return_value=Response()):
                self.assertEqual(pricing.fetch('https://example.test/prices.json','json',p)['added'],1)
            before=p.read_bytes()
            with patch('pricing.urlopen',side_effect=URLError('test disconnected')):
                with self.assertRaises(URLError):pricing.fetch('https://example.test/prices.json','json',p)
            self.assertEqual(p.read_bytes(),before)
            with self.assertRaises(ValueError):pricing.fetch('https://user:secret@example.test/x','json',p)

    def test_same_sku_must_be_grouped_before_pack_rounding(self):
        p = project(); other=copy.deepcopy(p['lines'][0]); other['id']='other'
        p['lines'].append(other)
        with self.assertRaises(ValueError):pricing.assess(p,store(),TODAY,True)

    def test_source_link_must_not_execute_script(self):
        with self.assertRaises(ValueError):pricing.normalize_offer(offer(source_url='javascript:alert(1)'))

    def test_single_supplier_priority_is_counted_for_same_products_not_value_percent(self):
        p=project();other=copy.deepcopy(p['lines'][0]);other.update(id='second',product_id='second',selection={'supplier_id':'a','account_id':'public','sku':'A-2'})
        p['lines'].append(other)
        s=store(offer(),offer(product_id='second',sku='A-2'),offer(supplier_id='b',supplier_name='B',sku='B-1',amount='1'))
        r=pricing.assess(p,s,TODAY,True)
        a,b=r['supplier_baskets']
        self.assertEqual((a['supplier_id'],a['priced_lines'],a['required_lines']),('a',2,2))
        self.assertEqual((b['priced_lines'],b['missing_line_ids']),(1,['second']))
        self.assertIsNone(b['rest_purchase_total_excl_vat'])

    def test_price_and_transport_CO2_remain_separate_no_automatic_winner(self):
        p=project();p['delivery']['a'].update(transport_kg_co2e='3',climate_reference='test route A')
        p['delivery']['b']={'amount_excl_vat':'0','reference':'test delivery B','transport_kg_co2e':'30','climate_reference':'test route B'}
        r=pricing.assess(p,store(offer(),offer(supplier_id='b',sku='B-1',amount='400')),TODAY,True)
        a,b=r['supplier_baskets']
        self.assertEqual((a['rest_purchase_total_excl_vat'],a['transport_kg_co2e']),('900.00','3'))
        self.assertEqual((b['rest_purchase_total_excl_vat'],b['transport_kg_co2e']),('640.00','30'))
        self.assertEqual(r['lines'][0]['selected']['supplier_id'],'a')
        self.assertEqual(r['delivery_transport_kg_co2e'],'3')
        self.assertNotIn('winner',r)

    def test_unknown_transport_and_unknown_suppliers_are_not_zero(self):
        r=pricing.assess(project(),store(),TODAY,True)
        self.assertIsNone(r['delivery_transport_kg_co2e'])
        p=project();p['lines'][0]['selection']=None
        r=pricing.assess(p,store(),TODAY,True)
        self.assertIsNone(r['delivery_transport_kg_co2e'])

    def test_transport_source_required_but_price_and_climate_gaps_independent(self):
        p=project();p['delivery']['a']['transport_kg_co2e']='3'
        with self.assertRaises(ValueError):pricing.assess(p,store(),TODAY,True)
        p['delivery']['a'].update(amount_excl_vat=None,climate_reference='test route')
        r=pricing.assess(p,store(),TODAY,True)
        self.assertEqual(r['delivery_transport_kg_co2e'],'3')
        self.assertIsNone(r['forecast_excl_vat'])

    def test_craftsman_discount_belongs_to_buyer_account(self):
        discounted=offer(account_id='test-buyer',price_basis='list',discount_percent='20',discount_reference='TEST trade agreement')
        s=store(offer(),discounted)
        p=project();p['lines'][0]['selection']['account_id']='test-buyer'
        r=pricing.assess(p,s,TODAY,True)
        self.assertEqual(r['lines'][0]['selected']['goods_excl_vat'],'640.00')
        p['account_id']='different-buyer'
        r=pricing.assess(p,s,TODAY,True)
        self.assertIsNone(r['lines'][0]['selected'])
        self.assertEqual(len(r['lines'][0]['options']),1)  # Public reference only.

    def test_single_supplier_is_not_assumed_single_shipment_or_zero_transport(self):
        p=project();r=pricing.assess(p,store(),TODAY,True)
        self.assertEqual(len(r['supplier_baskets']),1)
        self.assertIsNone(r['supplier_baskets'][0]['transport_kg_co2e'])
        self.assertIn('CO2',r['supplier_baskets'][0]['issues'][-1])

    def test_render_escapes_suppliers_and_labels(self):
        p = project();p['lines'][0]['label']='<script>alert(1)</script>'
        result=pricing.render(pricing.assess(p,store(),TODAY,True))
        self.assertNotIn('<script>',result);self.assertIn('TESTDATA',result)


if __name__ == '__main__':
    unittest.main()
