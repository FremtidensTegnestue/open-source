"""Fiktive grænseprøver af pricing.py; ingen køb, CADændringer eller projektfiler."""
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pricing

p={'schema':1,'scope_id':'TEST:fire-vinduer-kun-varebeloeb','account_id':'TEST:buyer','currency':'DKK','tax_basis':'excl_vat','budget':None,'delivery':{'TEST:supplier':{'amount_excl_vat':'0','reference':'TEST:fragt uden for varescenariet, ikke faktisk gratis fragt'}},'lines':[{'id':'TEST:windows','label':'FIKTIVE vinduer A','product_id':'TEST:window:A','unit':'stk','net_quantity':'4','waste_rate':'0','origin':'nyt','orders':[{'id':'TEST:O1:L1','reference':'FIKTIV aftale, intet køb','price_fixed':True,'supplier_id':'TEST:supplier','quantity':'4','invoiced_quantity':'3','invoiced_excl_vat':'12000','remaining_excl_vat':'4000'}],'selection':None}]}
store={'schema':1,'offers':[],'imports':[]}
def assess(x):return pricing.assess(x,store,date(2026,11,20),False)
a=assess(p);assert a['forecast_excl_vat']=='16000.00'
physical=copy.deepcopy(p);physical['lines'][0]['research_physical_context']={'received':3,'accepted_goods':2,'damaged':1,'installed':2,'documentation':'missing'}
b=assess(physical);assert a==b
credit=copy.deepcopy(p);credit['lines'][0]['orders'][0].update(invoiced_quantity='1',invoiced_excl_vat='-4000',remaining_excl_vat='4000')
try:assess(credit)
except ValueError as exc:credit_result={'accepted':False,'error':str(exc)}
else:raise AssertionError('Expected unsupported negative credit event to be rejected')
multi=copy.deepcopy(p);multi['lines'].append(copy.deepcopy(multi['lines'][0]));multi['lines'][1]['id']='TEST:other-line'
try:assess(multi)
except ValueError as exc:duplicate_result={'accepted':False,'error':str(exc)}
else:raise AssertionError('Expected duplicate order key to be rejected')
# Separate order-line keys can belong conceptually to the same external order header.
multi['lines'][1]['orders'][0]['id']='TEST:O1:L2';m=assess(multi);assert m['forecast_excl_vat']=='32000.00'
# Net snapshots can express a revised known budget, but not preserve its event history alone.
revised=copy.deepcopy(p);r=revised['lines'][0];r['net_quantity']='2';r['orders'][0].update(quantity='2',invoiced_quantity='2',invoiced_excl_vat='8000',remaining_excl_vat='0')
r2=copy.deepcopy(r);r2.update(id='TEST:windows-B',label='FIKTIVE vinduer B',product_id='TEST:window:B');r2['orders'][0].update(id='TEST:O2:L1',reference='FIKTIV ny aftale efter eksplicit aendring',quantity='2',invoiced_quantity='0',invoiced_excl_vat='0',remaining_excl_vat='9000');revised['lines'].append(r2)
c=assess(revised);assert c['forecast_excl_vat']=='17000.00'
manual={'kind':'TEST scenario, not executed transaction or lifecycle assessment','design_openings':['TEST:W01','TEST:W02','TEST:W03','TEST:W04'],'initial_order':{'type':'A','units':4,'unit_price_DKK_excl_vat':'4000'},'receipt':{'units':3,'accepted_goods':2,'quarantined':1,'unreceived':1},'installation':{'installed_units':2,'opening_ids':['TEST:W01','TEST:W02']},'return':{'damaged_units_returned':1,'return_is_not_automatic_cancellation':True},'agreed_change_assumption':{'A_remaining_obligation_cancelled_units':2,'A_retained_units':2,'A_invoice_original':'12000','A_credit_after_explicit_acceptance':'4000','B_new_order_units':2,'B_unit_price':'4500','supplier_acceptance':'FICTITIOUS explicit agreement, not inferred from return'},'calculated_goods_budget':{'reference':'16000','revised':'17000','difference':'1000'},'excluded_or_unknown':['actual product eligibility','labor','freight and fees','delay duration','climate factors','formal approval','VAT source conversion','payment','installation and document acceptance'],'climate_total':None,'date_and_role_tracking':'proposed, not implemented'}
result={'schema':'research-only-40','all_data_fictitious':True,'pricing_sha256':hashlib.sha256(Path(pricing.__file__).read_bytes()).hexdigest(),'checks':[{'name':'existing financial snapshot','passed':True,'known_goods_forecast':a['forecast_excl_vat'],'invoiced_snapshot':a['lines'][0]['actual_excl_vat'],'note':'actual_excl_vat currently comes from invoiced_excl_vat; not proof of delivery, payment or installation'},{'name':'physical context does not affect financial kernel','passed':a==b,'note':'extra research metadata ignored; no receipt, damage or approval semantics implemented'},{'name':'negative credit event unsupported','passed':not credit_result['accepted'],**credit_result},{'name':'same header key on two lines rejected','passed':not duplicate_result['accepted'],**duplicate_result},{'name':'unique line keys accepted','passed':True,'forecast':m['forecast_excl_vat'],'note':'TEST:O1:L1 and TEST:O1:L2; no external-order-header model added'},{'name':'revised net budget snapshot accepted','passed':True,'forecast':c['forecast_excl_vat'],'note':'does not itself preserve cancellation, credit or acceptance history'}],'limitations':'No delivery engine, event ledger, model identity test or live integrations built.'}
result['scenario'] = manual
print(json.dumps(result, ensure_ascii=False, indent=2))
