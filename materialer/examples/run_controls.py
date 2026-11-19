#!/usr/bin/env python3
"""Run actual application models and independently check source-bound calculations."""
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import materials
import material_calculations as calc
from report_io import write_report
import openpyxl

MATERIAL_IDS={
 'wood':'br18:t7:B1318:row2', 'concrete':'br18:t7:B1433:row25',
 'steel':'br18:t7:D1591:row129', 'glass':'br18:t7:G0954:row410',
 'insulation':'br18:t7:G0161:row196',
}
SOURCE_ROWS={'wood':2,'concrete':25,'steel':129,'glass':410,'insulation':196}
MODULE_COLUMNS={'A1-A3':5,'C3':6,'C4':7,'D':8}


def close(actual,expected,label):
 if not math.isclose(actual,float(expected),rel_tol=1e-10,abs_tol=1e-11):raise AssertionError(f'{label}: {actual} != {expected}')


def binding(element,category):
 mid=MATERIAL_IDS[category]
 return {'material_id':mid,'model_material_name':element['material_name'],
         'selection_note':'Explicit authored reference-quantity scenario using this named BR18 record. The rectangular specimen represents a quantity, not a verified as-built assembly/product, structural design or inferred product equivalence.',
         'density_observation_id':mid+':mass','gwp_observation_ids':[mid+':gwp:'+m for m in MODULE_COLUMNS]}


def main():
 sheet=openpyxl.load_workbook(ROOT/'data/raw/br18/table-7-2025.xlsx',data_only=False,read_only=False).active
 summaries=[];cache={};by_model={}
 for software in ('solidcraft','bimcraft'):
  expected=json.loads((ROOT/f'examples/models/{software}/expected.json').read_text())
  for item in expected['cases']:
   case_id=item.get('case_id',item.get('id'));category=case_id.split('-')[-1]
   if category not in MATERIAL_IDS:continue
   model_path=Path(item['model'])
   if not model_path.is_absolute():
    model_path=ROOT/model_path if str(model_path).startswith('examples/') else ROOT/f'examples/models/{software}'/model_path
   key=(software,str(model_path))
   if key not in cache:cache[key]=calc.extract(model_path,software)
   model=cache[key];element=next(e for e in model['elements'] if e['id']==item['element_id'])
   if isinstance(item['dimensions_mm'],list):dims=item['dimensions_mm']
   else:dims=[item['dimensions_mm'][k] for k in ('length','width','thickness')]
   # Independent arithmetic reads the ORIGINAL workbook, not DB calculation results.
   volume=Decimal(str(dims[0]))*Decimal(str(dims[1]))*Decimal(str(dims[2]))/Decimal(1000000000)
   close(element['volume_m3'],volume,case_id+' actual volume')
   srcrow=SOURCE_ROWS[category];density=Decimal(str(sheet.cell(srcrow,11).value));mass=volume*density
   mid=MATERIAL_IDS[category]
   assert element['material_name']==sheet.cell(srcrow,4).value.strip()
   by_model.setdefault(key,{'schema_version':1,'model_sha256':model['model']['sha256'],'elements':{}})['elements'][element['id']]=binding(element,category)
   summaries.append({'case_id':case_id,'software':software,'model':str(model_path.relative_to(ROOT)),'element_id':element['id'],'material_id':mid,
                     'expected_volume_m3':float(volume),'expected_mass_kg':float(mass),'source_reference':f'data/raw/br18/table-7-2025.xlsx Sheet1 row{srcrow}',
                     'independent_formula':'dimensions_mm product / 1e9; mass = analytical volume * original workbook density',
                     'gwp_expected':{mod:float(Decimal(str(sheet.cell(srcrow,col).value))*(volume if sheet.cell(srcrow,10).value=='m³' else mass/Decimal(1000))/Decimal(str(sheet.cell(srcrow,9).value))) for mod,col in MODULE_COLUMNS.items()}})
 with materials.connect(materials.DEFAULT_DB) as db:
  for key,b in by_model.items():
   model=cache[key];software,model_path=key;stem=Path(model_path).stem
   write_report(model,ROOT/f'examples/reports/{software}-{stem}-extraction.json',[model_path,materials.DEFAULT_DB])
   write_report(b,ROOT/f'examples/bindings/{software}-{stem}.json',[model_path,materials.DEFAULT_DB])
   report=calc.assess(db,model,b)
   assert report['status']=='ok',(key,report)
   write_report(report,ROOT/f'examples/reports/{software}-{stem}-assessment.json',[model_path,materials.DEFAULT_DB])
   for summary in [s for s in summaries if (s['software'],str(ROOT/s['model']))==key]:
    result=next(e for e in report['elements'] if e['element_id']==summary['element_id'])
    actual=result['calculations'];close(actual['mass']['value'],summary['expected_mass_kg'],summary['case_id']+' mass')
    for item in actual['climate']:close(item['value'],summary['gwp_expected'][item['module']],summary['case_id']+' '+item['module'])
    summary.update(status='passed',reported_mass_kg=actual['mass']['value'],model_quantity_rounding_bound_kg=actual['mass'].get('model_quantity_rounding_bound_kg'),report=f'examples/reports/{software}-{stem}-assessment.json')
  # Real Solidcraft specimen corresponding to the published USDA example.
  path=ROOT/'examples/models/solidcraft/solid-wood-moisture.sc';model=calc.extract(path,'solidcraft');element=model['elements'][0]
  moisture_binding={'schema_version':1,'model_sha256':model['model']['sha256'],'elements':{element['id']:{'material_id':'wood:fir-white','model_material_name':'Fir, white',
    'selection_note':'Authored white-fir specimen; explicit species and orientation reference scenario from USDA example, not inferred CLT behavior.',
    'operations':['moisture'],'moisture':{'coefficient_observation_id':'wood:51bdadf283844ea37156000c','dimension_axis':'x','direction':'tangential','initial_moisture_percent':8,'final_moisture_percent':11,
    'orientation_note':'In this authored specimen, world x explicitly represents tangential board width; this is an author assumption, not inferred from geometry.'}}}}
  report=calc.assess(db,model,moisture_binding);assert report['status']=='ok',report
  result=report['elements'][0]['calculations']['moisture'];expected=Decimal(232)*Decimal('.00245')*Decimal(3)/Decimal(1000)
  close(result['value'],expected,'USDA published moisture example')
  write_report(moisture_binding,ROOT/'examples/bindings/solidcraft-moisture.json',[path,materials.DEFAULT_DB])
  write_report(report,ROOT/'examples/reports/solidcraft-moisture-assessment.json',[path,materials.DEFAULT_DB])
  # Actual original ILCD declaration is per1000kg, despite reference exchange1.
  request={'kind':'climate','material_id':'environmental:material:oekobaudat:3428753d-b270-4b13-bbe0-244b981db333@00.04.000','gwp_observation_id':'environmental:oekobaudat:3428753d-b270-4b13-bbe0-244b981db333@00.04.000:5c075fc772a54566d4','quantity':{'value':500,'unit':'kg'}}
  env=calc.calculate(db,request);close(env['value'],Decimal(859)*Decimal(500)/Decimal(1000),'ILCD1000kg')
  write_report(request,ROOT/'examples/requests/environmental-1000kg.json',[materials.DEFAULT_DB])
  write_report(env,ROOT/'examples/reports/environmental-1000kg.json',[materials.DEFAULT_DB])
  guards=[]
  for software,relative in [('solidcraft','examples/models/solidcraft/unknown.sc'),('bimcraft','examples/models/bimcraft/missing-material.bimc'),('bimcraft','examples/models/bimcraft/mixed-layers.bimc')]:
   model=calc.extract(ROOT/relative,software)
   report=calc.assess(db,model,{'schema_version':1,'model_sha256':model['model']['sha256'],'elements':{}})
   assert report['status']=='partial' and all(not x['calculations'] for x in report['elements'])
   guards.append({'software':software,'model':relative,'status':report['status'],'numeric_calculations':0,'warnings':report['warnings']})
  summary={'status':'passed','model_calculation_cases':len(summaries),'mass_checks':len(summaries),'separate_climate_module_checks':4*len(summaries),'software':['solidcraft','bimcraft'],
           'material_families':list(MATERIAL_IDS),'cases':summaries,
           'extra_checks':{'wood_moisture_model':{'expected_change_mm':float(expected*1000),'actual_change_mm':result['value']*1000,'report':'examples/reports/solidcraft-moisture-assessment.json'},
                           'original_ilcd_1000kg_reference':{'expected_kg_co2_eq':429.5,'actual_kg_co2_eq':env['value']},'missing_material_guards':guards},
           'scope':'Authored homogeneous quantity specimens and explicit source-record scenarios; no full building, product equivalence or regulatory certification; BIMcraft floor quantity rounding retained as bound.'}
  assert len(summaries)==10
  write_report(summary,ROOT/'examples/reports/validation-summary.json',[materials.DEFAULT_DB])
  print(json.dumps({k:summary[k] for k in ('status','model_calculation_cases','mass_checks','separate_climate_module_checks','material_families')},indent=2))

if __name__=='__main__':main()
