"""Isolated review reproductions. All prices/products fictitious; writes no project data."""
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
import pricing

DAY = date(2026, 11, 20)

def raw(**changes):
    r = dict(supplier_id='fixture-seller', supplier_name='FICTITIOUS supplier',
             account_id='fixture-buyer', sku='fixture-A', product_id='fixture:window:A',
             mapping_reference='Fictitious review fixture only', source_url='https://example.test/quote',
             observed_on='2026-11-20', review_on='2026-12-20', currency='DKK', unit='stk',
             kind='quote', origin='nyt', availability='available', amount='4000', price_quantity='1',
             purchase_step='1', minimum_quantity='0', tax_basis='excl_vat', price_basis='net')
    r.update(changes)
    return r

def store(*raws):
    return dict(schema=1, imports=[], offers=[dict(pricing.normalize_offer(r),
                received_at='2026-11-20T08:00:00+00:00') for r in raws])

def project():
    return dict(schema=1, scope_id='fixture-target-project', account_id='fixture-buyer',
                currency='DKK', tax_basis='excl_vat',
                delivery={'fixture-seller': {'amount_excl_vat':'0', 'reference':'Explicit fictitious zero freight'}},
                lines=[dict(id='windows', label='FICTITIOUS four windows', unit='stk',
                            product_id='fixture:window:A', net_quantity='4', waste_rate='0', origin='nyt', orders=[],
                            selection={'supplier_id':'fixture-seller','account_id':'fixture-buyer','sku':'fixture-A'})])

result = dict(date=str(DAY), prices='FICTITIOUS DKK excl VAT',
              code_sha256=hashlib.sha256((root/'pricing.py').read_bytes()).hexdigest(), findings=[])
p = project()
s = store(raw(quote_id='quote-other-project', scope_id='fixture-OTHER-project',
              quantity_condition='Only for a complete order of 40 units'))
r = pricing.assess(p, s, DAY)
assert r['forecast_excl_vat'] == '16000.00' and not r['unresolved']
result['findings'].append(dict(id='quote-scope', inputs={'project':p,'store':s},
    observed={'forecast_excl_vat':r['forecast_excl_vat'],'unresolved':r['unresolved']},
    meaning='Extra quotation scope/quantity fields are preserved but not enforced. Not a supported quote contract.'))

s = store(raw(quote_id='independent-quote-1', amount='4000'),
          raw(quote_id='independent-quote-2', amount='4500'))
s['offers'][1]['received_at'] = '2026-11-20T09:00:00+00:00'
available = pricing.current_offers(s, p['account_id'], DAY)
assert len(available) == 1 and available[0]['raw']['quote_id'] == 'independent-quote-2'
result['findings'].append(dict(id='independent-quotes', inputs={'store':s},
    observed={'stored':len(s['offers']),'available':len(available),'retained_quote':available[0]['raw']['quote_id']},
    meaning='Latest-price key collapses independently identified offers; it is not an offer-version/context model.'))

p = project()
p['lines'][0]['orders'] = [dict(id='fixture-order-A', reference='FICTITIOUS order for product A',
    supplier_id='fixture-seller', price_fixed=True, quantity='4', invoiced_quantity='0',
    invoiced_excl_vat='0', remaining_excl_vat='16000')]
before = pricing.assess(p, store(), DAY)
changed = copy.deepcopy(p)
changed['lines'][0]['product_id'] = 'fixture:window:B'
changed['lines'][0]['selection'] = None
after = pricing.assess(changed, store(), DAY)
assert before['forecast_excl_vat'] == after['forecast_excl_vat'] == '16000.00'
assert after['lines'][0]['options'] == [] and not after['unresolved']
result['findings'].append(dict(id='order-product-change', inputs={'before':p,'after':changed},
    observed={'forecast_before':before['forecast_excl_vat'],'forecast_after':after['forecast_excl_vat'],
              'unordered_after':after['lines'][0]['unordered_quantity'],'unresolved_after':after['unresolved']},
    meaning='Changing the product on an ordered line does not invalidate its old quantity coverage. The current editor does not offer this material switch.'))

try:
    pricing.normalize_offer(raw(kind='estimate'))
except ValueError as error:
    result['findings'].append(dict(id='estimate-kind', observed={'error':str(error)},
        meaning='An internal estimate without source_reference is rejected. Dated local estimates with an explicit source_reference are now supported.'))
else:
    raise AssertionError('Expected estimate without provenance to be rejected')

print(json.dumps(result, ensure_ascii=False, indent=2))
