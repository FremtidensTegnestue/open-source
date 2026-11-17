#!/usr/bin/env python3
"""Harvest pinned original OpenStudio/EnergyPlus physical material libraries.

Only reads data; never executes upstream Ruby or simulation programs.
"""
import argparse,collections,concurrent.futures,datetime,hashlib,json,math,pathlib,re,time,urllib.request
from decimal import Decimal
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/technical'; STAGE=ROOT/'data/staging/technical'
REPOS={
 'openstudio':{'repo':'NatLabRockies/openstudio-standards','commit':'0bd835164403285d82654c422e525a9877e3c47e','license':'Custom permissive OpenStudio license with redistribution/naming conditions; see original LICENSE.md','license_file':'LICENSE.md'},
 'energyplus':{'repo':'NatLabRockies/EnergyPlus','commit':'fcdda275c87255660bcad034197c03b64af2b0a8','license':'Custom permissive EnergyPlus license with redistribution/naming conditions; original dataset also attributes ASHRAE and other sources','license_file':'LICENSE.txt'},
}
OS_FILES=[
 'lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.materials.json',
 'lib/openstudio-standards/standards/ashrae_90_1_prm/data/ashrae_90_1_prm.materials.json',
 'lib/openstudio-standards/standards/cbes/data/cbes.materials.json',
 'lib/openstudio-standards/standards/deer/data/deer.materials.json',
 'lib/openstudio-standards/standards/necb/NECB2011/data/materials.json',
]
EP_FILES=['datasets/'+f for f in ['ASHRAE_2005_HOF_Materials.idf','MoistureMaterials.idf','WindowBlindMaterials.idf','WindowGasMaterials.idf','WindowGlassMaterials.idf','WindowScreenMaterials.idf','WindowShadeMaterials.idf']]
NUM=re.compile(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\Z')

def slug(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
def short(s):return hashlib.sha256(s.encode()).hexdigest()[:20]
def jsondump(x):return json.dumps(x,ensure_ascii=False,allow_nan=False,default=str)
def source_id(kind,path):return 'technical:source:'+kind+':'+path.replace('/','_')
def fetch(item,refresh=False):
 kind,path=item;conf=REPOS[kind];url=f'https://raw.githubusercontent.com/{conf["repo"]}/{conf["commit"]}/{path}'
 dest=RAW/kind/path;dest.parent.mkdir(parents=True,exist_ok=True)
 if refresh or not dest.exists():
  for attempt in range(3):
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FremtidensTegnestue-materials-research/1.0'}),timeout=90) as src:body=src.read()
    dest.write_bytes(body);break
   except Exception:
    if attempt==2:raise
    time.sleep(2**attempt)
 stat=dest.stat();digest=hashlib.sha256(dest.read_bytes()).hexdigest()
 return {'id':source_id(kind,path),'title':path.rsplit('/',1)[-1],'publisher':conf['repo'],'url':url,'retrieved_at':datetime.datetime.fromtimestamp(stat.st_mtime,datetime.timezone.utc).isoformat(),'local_path':str(dest.relative_to(ROOT)),'sha256':digest,'media_type':'application/json' if path.endswith('.json') else 'text/plain','license':conf['license'],'license_status':'verified','description':f'Unmodified original at Git commit {conf["commit"]}; units and original attribution retained.'}

def category(name,metadata=''):
 text=(name+' '+metadata).lower()
 # Discovery grouping only, not validated classification or product equivalence.
 groups=[('insulation',['insulat','fiberglass','mineral wool','polystyrene','polyurethane','cellulose','foam','rockwool','xps','eps ']),('glass',['glaz','glass','low-e','loe ','clear ','bronze ','tinted']),('concrete',['concrete','cement','mortar','grout','stucco']),('masonry',['brick','masonry','stone','granite','tile','marble','limestone','slate','clay']),('metal',['steel','metal','alumin','copper','iron','bronze']),('wood',['wood','timber','plywood','lumber','oak','pine','fir ','hardboard','particleboard','oriented strand','osb']),('polymer',['plastic','polymer','vinyl','polyester','polyprop','polyethylene','pvc','acrylic'])]
 for cat,terms in groups:
  if any(term in text for term in terms):return cat
 return 'other'

OS_UNITS={
 'thickness':'in','conductivity':'Btu*in/(h*ft^2*degF)','resistance':'h*ft^2*degF/Btu',
 'density':'lb/ft^3','specific_heat':'Btu/(lb*degF)','u_factor':'Btu/(h*ft^2*degF)',
 'thermal_absorptance':'1','solar_absorptance':'1','visible_absorptance':'1','solar_heat_gain_coefficient':'1','visible_transmittance':'1',
 'solar_transmittance_at_normal_incidence':'1','front_side_solar_reflectance_at_normal_incidence':'1','back_side_solar_reflectance_at_normal_incidence':'1',
 'visible_transmittance_at_normal_incidence':'1','front_side_visible_reflectance_at_normal_incidence':'1','back_side_visible_reflectance_at_normal_incidence':'1',
 'infrared_transmittance_at_normal_incidence':'1','front_side_infrared_hemispherical_emissivity':'1','back_side_infrared_hemispherical_emissivity':'1',
 'dirt_correction_factor_for_solar_and_visible_transmittance':'1',
}
PROP={'conductivity':'thermal_conductivity','specific_heat':'specific_heat_capacity','resistance':'thermal_resistance'}
DIMENSIONLESS=('absorptance','transmittance','reflectance','emissivity','resistance factor','coefficient a','coefficient b','coefficient c','coefficient d','coefficient of','porosity','saturation','relative humidity','moisture content')

def parse_os(sources):
 occurrences=collections.defaultdict(list); records={}
 for path in OS_FILES:
  data=json.loads((RAW/'openstudio'/path).read_text(),parse_float=Decimal,parse_int=Decimal)
  entries=data.get('materials') or data.get('tables',{}).get('materials',{}).get('table')
  assert entries is not None,path
  for i,record in enumerate(entries):
   # Equality includes every original field, so variants are not collapsed.
   canonical=json.dumps(record,sort_keys=True,default=str)
   key=short(canonical);records[key]=record;occurrences[key].append((path,i))
 materials=[];obs=[];skipped=[]
 for key,rec in records.items():
  path,i=occurrences[key][0];sid=source_id('openstudio',path);loc=(f'$.tables.materials.table[{i}]' if '/necb/' in path else f'$.materials[{i}]');mid='technical:openstudio:'+key
  matsource=str(rec.get('material_standard') or '')+' '+str(rec.get('code_category') or '')
  material_type=rec['material_type'];kind='assembly' if material_type=='SimpleGlazing' else 'generic'
  materials.append({'id':mid,'name':rec['name'],'kind':kind,'category':category(rec['name'],matsource),'aliases':[],'description':str(rec.get('notes') or '')+' | Simulation library record: '+str(material_type),'source_id':sid,'source_locator':loc})
  context={'library':'OpenStudio standards','material_type':material_type,'roughness':rec.get('roughness'),'material_standard':rec.get('material_standard'),'material_standard_source':rec.get('material_standard_source'),'code_category':rec.get('code_category'),'code_identifier':rec.get('code_identifier'),'notes':rec.get('notes'),'unit_system':'original imperial units','units_evidence_source':source_id('openstudio','lib/openstudio-standards/standards/Standards.Model.rb'),'same_record_other_occurrences':[{'source_id':source_id('openstudio',p),'source_locator':(f'$.tables.materials.table[{n}]' if '/necb/' in p else f'$.materials[{n}]')} for p,n in occurrences[key][1:]],'category_method':'keyword discovery grouping, not a technical equivalence classification'}
  for field,value in rec.items():
   if not isinstance(value,Decimal):continue
   if field not in OS_UNITS:
    skipped.append({'material_id':mid,'field':field,'reason':'unit not established from source implementation','value':str(value)});continue
   unit=OS_UNITS[field]
   # Source consumer has an anomalous AirGap resistance conversion with per-inch units.
   # Keep its ambiguity explicit rather than silently impose conventional area-R units.
   extra={}
   if material_type=='AirGap' and field=='resistance':
    unit='source_ambiguous';extra={'unit_ambiguity':'Source Ruby converts hr*ft^2*R/Btu*in -> m*K/W for AirGap; not treated as conventional area thermal resistance.'}
   if field=='resistance' and material_type=='StandardOpaqueMaterial':extra['interpretation']='Tabulated layer resistance, not intrinsic thermal conductivity.'
   n=float(value);assert math.isfinite(n)
   obs.append({'id':mid+':'+field,'material_id':mid,'property':PROP.get(field,field),'value':n,'value_text':str(value),'unit':unit,'source_id':sid,'source_locator':loc+'.'+field,'method':'OpenStudio standards simulation material library; properties may be generic or prescribed simulation inputs','data_status':'reported','conditions':context|extra})
 return materials,obs,skipped,{'total_input_records':sum(len(v) for v in occurrences.values()),'unique_complete_records':len(records),'duplicate_exact_records':sum(len(v)-1 for v in occurrences.values())}

def idf_records(text):
 # Preserve character offsets/line numbers while ignoring EnergyPlus comments.
 clean=re.sub(r'![^\n]*',lambda m:' '*len(m[0]),text)
 for match in re.finditer(r'([^;]+);',clean):
  section=match[1];tokens=[];offset=match.start(1)
  for tokenmatch in re.finditer(r'([^,]*)(?:,|$)',section):
   raw=tokenmatch[1]
   if tokenmatch.start()==len(section):continue
   stripped=raw.strip();start=offset+tokenmatch.start()+len(raw)-len(raw.lstrip());line=text.count('\n',0,start)+1
   original_line=text.splitlines()[line-1]
   label=original_line.split('!-',1)[1].strip() if '!-' in original_line else ''
   tokens.append((stripped,label,line))
  if tokens:yield tokens

def parse_ep():
 materials=[];obs=[];skipped=[];counts=collections.Counter();material_by_key={}
 for path in EP_FILES:
  text=(RAW/'energyplus'/path).read_text();sid=source_id('energyplus',path)
  for record_i,tokens in enumerate(idf_records(text)):
   typ=tokens[0][0]
   if not (typ.lower().startswith('material') or typ.lower().startswith('windowmaterial')):continue
   assert len(tokens)>1
   name=tokens[1][0];mid='technical:energyplus:'+short(path+'|'+name.casefold());counts[typ]+=1
   loc=f'{path}:L{tokens[0][2]} ({typ}, name={name})'
   cat='glass' if typ.lower().startswith('windowmaterial:glazing') else category(name)
   if mid not in material_by_key:
    material_by_key[mid]={'id':mid,'name':name,'kind':'generic','category':cat,'aliases':[],'description':'EnergyPlus dataset record '+typ+'; simulation properties, not a product declaration.','source_id':sid,'source_locator':loc}
    materials.append(material_by_key[mid])
   else:
    material_by_key[mid]['description']+=' | Also '+typ
   is_curve=typ in ('MaterialProperty:HeatAndMoistureTransfer:SorptionIsotherm','MaterialProperty:HeatAndMoistureTransfer:Suction','MaterialProperty:HeatAndMoistureTransfer:Redistribution','MaterialProperty:HeatAndMoistureTransfer:Diffusion','MaterialProperty:HeatAndMoistureTransfer:ThermalConductivity')
   for field_i,(value,label,line) in enumerate(tokens[2:],start=2):
    if not value or not NUM.fullmatch(value):continue
    if not label:
     skipped.append({'material_id':mid,'value':value,'field_index':field_i,'reason':'no source field label'});continue
    if label.lower().startswith('number of'):continue # Structural record count, not material property.
    if is_curve and (field_i<4 or field_i%2==1):continue # X-values stay paired as conditions, not extra independent properties.
    units=re.findall(r'\{([^{}]+)\}',label)
    propname=re.sub(r'\{[^{}]+\}','',label).strip();unit=units[-1] if units else ('1' if any(k in propname.lower() for k in DIMENSIONLESS) else 'source_unspecified')
    prop=slug(propname)
    if is_curve:prop=re.sub(r'_\d+$','',prop)
    prop=PROP.get(prop,prop)
    n=float(value);assert math.isfinite(n)
    context={'library':'EnergyPlus dataset','idf_object_type':typ,'record_name':name,'field_index':field_i,'original_field_label':label,'category_method':'keyword discovery grouping, not a technical equivalence classification'}
    if is_curve:
     xvalue,xlabel,xline=tokens[field_i-1];xunits=re.findall(r'\{([^{}]+)\}',xlabel);xname=re.sub(r'\{[^{}]+\}','',xlabel).strip()
     context['curve_point']={'index':(field_i-2)//2,'x_property':slug(re.sub(r'\s+\d+$','',xname)),'x_value':float(xvalue),'x_value_text':xvalue,'x_unit':xunits[-1] if xunits else ('1' if 'humidity' in xname.lower() or 'moisture' in xname.lower() else 'source_unspecified'),'x_source_locator':f'{path}:L{xline}','x_original_field_label':xlabel,'curve_model':typ}
    if typ.lower().startswith('materialproperty:'):context['interpretation']='Model-specific moisture/material function parameter; must use with its documented EnergyPlus model and other fields.'
    if prop.startswith('thermal_conductivity_coefficient') or prop.startswith('specific_heat_coefficient') or prop.startswith('viscosity_coefficient'):context['interpretation']='Temperature polynomial coefficient; coefficient index and units must be preserved.'
    obs.append({'id':mid+':object'+str(record_i)+':field'+str(field_i),'material_id':mid,'property':prop,'value':n,'value_text':value,'unit':unit,'source_id':sid,'source_locator':f'{path}:L{line} / {typ}[name={name}].{propname}','method':'EnergyPlus simulation dataset; original object type and field label retained','data_status':'reported','conditions':context})
 return materials,obs,skipped,counts

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');args=ap.parse_args();RAW.mkdir(parents=True,exist_ok=True);STAGE.mkdir(parents=True,exist_ok=True)
 items=[('openstudio',p) for p in OS_FILES]+[('energyplus',p) for p in EP_FILES]+[(kind,d['license_file']) for kind,d in REPOS.items()]+[('openstudio','lib/openstudio-standards/standards/Standards.Model.rb')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:sources=list(pool.map(lambda i:fetch(i,args.refresh),items))
 mats,obs,skipped,os_counts=parse_os(sources);m2,o2,skip2,ep_counts=parse_ep();mats+=m2;obs+=o2;skipped+=skip2
 # Assertions protect the scientific data contract and original preservation.
 assert len({m['id'] for m in mats})==len(mats)
 assert len({o['id'] for o in obs})==len(obs)
 mids={m['id'] for m in mats};sids={s['id'] for s in sources}
 assert all(o['material_id'] in mids and o['source_id'] in sids and math.isfinite(o['value']) for o in obs)
 assert all(m['source_id'] in sids for m in mats)
 for s in sources:assert hashlib.sha256((ROOT/s['local_path']).read_bytes()).hexdigest()==s['sha256']
 for filename,records in [('sources.jsonl',sources),('materials.jsonl',mats),('observations.jsonl',obs)]:
  (STAGE/filename).write_text(''.join(jsondump(x)+'\n' for x in records))
 (STAGE/'not_imported.json').write_text(json.dumps(skipped,ensure_ascii=False,indent=2))
 summary={'dataset':'technical','sources':len(sources),'materials':len(mats),'observations':len(obs),'distinct_material_names':len({m['name'] for m in mats}),'properties':dict(collections.Counter(o['property'] for o in obs)),'categories':dict(collections.Counter(m['category'] for m in mats)),'source_commits':{k:v['commit'] for k,v in REPOS.items()},'openstudio_deduplication':os_counts,'energyplus_object_types':dict(ep_counts),'not_imported_numeric_fields':len(skipped),'original_bytes':sum((ROOT/s['local_path']).stat().st_size for s in sources),'attempted_failures':[],'coverage':'All five materials JSON libraries in pinned OpenStudio tree and seven physical/moisture/window material EnergyPlus dataset files. Identical complete OpenStudio records deduplicated, variants kept.','known_limitations':['Most records are simulation library inputs, not certified product data or Danish design values.','Original imperial OpenStudio units preserved; no automatic SI conversion performed.','EnergyPlus examples may contain model coefficients rather than directly comparable physical properties; object type and field label identify context.','AirGap resistance unit ambiguity is explicitly marked source_ambiguous.','Keyword material categories are for discovery only; no equivalence or product matching is asserted.','The original files contain third-party attributions; repository custom permissive licenses and original notices preserved; no legal review of all cited handbook data.']}
 (STAGE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('properties','known_limitations')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
