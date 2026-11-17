#!/usr/bin/env python3
"""Reproducible USDA FPL-GTR-282 table collector. No OCR or inferred missing values."""
import argparse,collections,datetime,hashlib,json,pathlib,re,subprocess,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/wood';OUT=ROOT/'data/staging/wood'
NUMBER=r'(?:\d[\d,]*(?:\.\d+)?|—|–)'
URLS={
 '04':('https://research.fs.usda.gov/download/treesearch/62243.pdf','Moisture relations and physical properties of wood'),
 '05':('https://research.fs.usda.gov/download/treesearch/62244.pdf','Mechanical properties of wood'),
 '13':('https://research.fs.usda.gov/download/treesearch/62261.pdf','Drying and control of moisture content and dimensional changes')}
SOURCES=[];MATERIALS={};OBS=[];COUNTS=collections.Counter();SKIPPED=[]
def dump(name,rows):
 with (OUT/name).open('w') as f:
  for row in rows:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def material(name,ch,page,table,row,identity=None):
 name=re.sub(r'\s+',' ',name.strip()).replace('—con.','').strip(' ,')
 ident='wood:'+slug(name)+(('-'+slug(identity)) if identity else '')
 if ident not in MATERIALS:MATERIALS[ident]={'id':ident,'name':name,'kind':'generic','category':'wood','aliases':[],'description':'Wood species/common-name record; values are source-specific averages, not design allowables.','source_id':'wood:chapter-'+ch,'source_locator':f'PDF page {page}; printed page {int(ch)}–{page}; table {table}; row {row}'}
 return ident

def observation(mat,prop,value,unit,ch,page,table,row,conditions=None,method=None):
 if value in ('—','–',''):return
 try:v=float(value.replace(',','').replace('−','-'))
 except Exception:raise ValueError((prop,value,row))
 loc=f'PDF page {page}; printed page {int(ch)}–{page}; table {table}; row {row}'
 ident='wood:'+hashlib.sha256((mat+'|'+prop+'|'+loc+'|'+json.dumps(conditions,sort_keys=True)).encode()).hexdigest()[:24]
 OBS.append({'id':ident,'material_id':mat,'property':prop,'value':v,'value_text':value,'unit':unit,'source_id':'wood:chapter-'+ch,'source_locator':loc,'method':method or 'Published tabulated value in USDA Wood Handbook FPL-GTR-282 (2021)','data_status':'reported','conditions':conditions or {}});COUNTS[table]+=1

def pages(ch):return (RAW/f'chapter_{ch}.txt').read_text().split('\f')
def numsplit(line,n):
 m=re.match(r'^(.*?)\s+('+NUMBER+r'(?:\s+'+NUMBER+r'){'+str(n-1)+r'})\s*$',line)
 return (m.group(1),m.group(2).split()) if m else None

def woodname(label,group):
 # Imported tables include botanical names in parentheses, often wrapped.
 label=label.split('(')[0].strip()
 return f'{group}, {label}' if group else label

def basic():
 # 4-1 two columns, no hierarchy inside columns.
 p=pages('04')[1]
 for col,(a,b) in enumerate([(15,64),(64,120)]):
  active=False
  for lineno,line in enumerate(p.splitlines(),1):
   s=line[a:b]
   if 'Hardwoods' in s or 'Softwoods' in s:active=True;continue
   if not active:continue
   found=numsplit(s,2)
   if not found:continue
   label,values=found
   if not label.strip():continue
   m=material(label,'04',2,'4-1',label.strip())
   for woodpart,val in zip(['heartwood','sapwood'],values):
    observation(m,'green_moisture_content',val,'%', '04',2,'4-1',label.strip(),{'wood_part':woodpart,'state':'green','moisture_basis':'mass of water / ovendry wood mass','source_line':line,'column':col+1})
 # 4-2 19 RH columns, valid upper RH cells are intentionally blank at high T.
 p=pages('04')[3];started=False;rows=0
 m=material('Wood (general equilibrium-moisture reference)','04',4,'4-2','temperature / RH grid')
 for line in p.splitlines():
  z=re.match(r'^\s*([–−-]?\d+\.\d+)\s+\((\d+)\)\s+(.+)$',line)
  if not z:continue
  vals=z.group(3).split()
  if not all(re.fullmatch(r'\d+\.\d+',x) for x in vals):continue
  rows+=1
  for j,v in enumerate(vals):
   observation(m,'equilibrium_moisture_content',v,'%', '04',4,'4-2',f'T={z.group(1)} °C; RH={(j+1)*5}%',{'temperature_C':float(z.group(1).replace('–','-').replace('−','-')),'relative_humidity_percent':(j+1)*5,'reference_species':'primarily Sitka spruce','sorption_condition':'oscillating vapor pressure desorption','source_line':line,'limitations':'Precision 0.1% illustrates trends only; actual EMC varies. Source says not reliable for thermodynamic/scientific physical-model evaluation.'})
 assert rows==25,rows
 # 4-3 two-column domestic shrinkage.
 p=pages('04')[7]
 for col,(a,b) in enumerate([(6,68),(68,130)]):
  group='';active=False
  for line in p.splitlines():
   s=line[a:b];t=s.strip()
   if t.startswith('Species'):active=True;continue
   if not active:continue
   if t=='a':break
   if not t or t in ('Hardwoods','Softwoods') or re.fullmatch('[ab]',t):continue
   found=numsplit(s,3)
   if found:
    label,vals=found
    if not label.strip():continue
    # Headers are at 0 indentation; descendants have 3-space indentation.
    indent=len(label)-len(label.lstrip())
    if indent<3:group_for_row=''
    else:group_for_row=group
    name=woodname(label,group_for_row)
    if name.endswith('northb'):name=name[:-1]
    m=material(name,'04',8,'4-3',name)
    for direction,v in zip(['radial','tangential','volumetric'],vals):
     observation(m,'shrinkage_'+direction,v,'%', '04',8,'4-3',name,{'initial_state':'green','final_state':'ovendry','basis':'percentage of green dimension','direction':direction,'sampling_region':'United States domestic woods','source_line':line,'column':col+1},'ASTM D143 small clear specimens; tabulated average')
   elif re.fullmatch(r'[A-Za-z ,—.\-]+',t) and len(t)<35:
    group=t.replace('—con.','').strip()
 # 4-4 imported shrinkage, all data rows already have common name, no hierarchy.
 p=pages('04')[8]
 for col,(a,b) in enumerate([(0,72),(72,142)]):
  for line in p.splitlines():
   s=line[a:b];z=re.match(r'^(.*?)\s+('+NUMBER+r')\s+('+NUMBER+r')\s+('+NUMBER+r')\s+(AF|AM|AS)\s*$',s)
   if not z:continue
   label=z.group(1).strip();name=label.split('(')[0].strip();m=material(name,'04',9,'4-4',label,identity=label)
   for direction,v in zip(['radial','tangential','volumetric'],z.groups()[1:4]):
    observation(m,'shrinkage_'+direction,v,'%', '04',9,'4-4',label,{'initial_state':'green','final_state':'ovendry','basis':'percentage of green dimension','direction':direction,'location_code':z.group(5),'location_codes':{'AF':'Africa','AM':'Tropical America','AS':'Asia and Oceania'},'source_name':label,'source_line':line,'column':col+1,'limitations':'From world literature; may not represent a true species average.'})

def mechanical(table,page_numbers,props,region,imported=False):
 group='';current=None;source_name='';rowcounts=0
 for page in page_numbers:
  text=pages('05')[page-1]
  # Follow header line ending units; skip everything through it.
  ls=text.splitlines();start=next(i for i,l in enumerate(ls) if l.strip().endswith('(N)') or (table=='5-4a' and l.strip().endswith('(kPa)') and 'content' in l) or (table=='5-5a' and 'gravity' in l and 'content' in l))
  for lineno,line in enumerate(ls[start+1:],start+2):
   if line.strip()=='a':break
   z=re.search(r'\b(Green|\d+%)\s+(?=[0-9—])',line)
   if z:
    label=line[:z.start()].strip();state=z.group(1);suffix=line[z.end():].strip();loc_origin=None
    if imported:
     zz=re.search(r'\s+(AF|AM|AS)$',suffix)
     if zz:loc_origin=zz.group(1);suffix=suffix[:zz.start()]
    tokens=suffix.split()
    if not all(re.fullmatch(NUMBER,t) for t in tokens):
     SKIPPED.append({'table':table,'page':page,'line':line,'reason':'Non-numeric token'});continue
    if label and (not imported or state=='Green'):
     # First-letter indent distinguishes group descendants in domestic tables.
     indent=len(line[:z.start()])-len(line[:z.start()].lstrip())
     name=label.split('(')[0].strip() if imported else woodname(label,group if indent>0 else '')
     current=material(name,'05',page,table,label,identity=(table+' '+label) if imported else None);source_name=label
    if not current:raise ValueError('Missing species '+line)
    # Missing specific gravity is left blank (not carried from preceding row).
    expected=len(props)
    if len(tokens)==expected-1:tokens=['']+tokens
    if len(tokens)!=expected:
     SKIPPED.append({'table':table,'page':page,'line':line,'reason':f'Expected {expected} values got {len(tokens)}'});continue
    rowcounts+=1
    cond={'moisture_condition':state,'moisture_content_percent':float(state[:-1]) if state.endswith('%') else None,'specimen':'small clear wood specimens, not graded structural design values','sampling_region':region,'source_name':source_name,'source_line':line}
    if loc_origin:cond['location_code']=loc_origin
    if table=='5-3a':cond['specific_gravity_basis']='ovendry mass / volume at stated green or 12% moisture condition'
    if table=='5-4a':cond['specific_gravity_basis']='ovendry mass / green volume (table note)'
    if table=='5-5a':cond['specific_gravity_basis']='As displayed on green row; imported table does not define a per-row volume basis'
    for (prop,unit),v in zip(props,tokens):
     observation(current,prop,v,unit,'05',page,table,f'{source_name}; {state}; text line {lineno}',cond)
   else:
    t=line.strip()
    if t in ('Hardwoods','Softwoods'):group='';continue
    if not imported and re.fullmatch(r'[A-Za-z ,—.\-]+',t) and len(t)<30 and t not in ('names','content'):
     # Strip source superscript footnotes from group headings only.
     group=t.replace('—con.','').strip();group=group.replace('Douglas-fire','Douglas-fir');group=re.sub(r'(Hickory, true)d$',r'\1',group)
 COUNTS[table+'_rows']=rowcounts

def thermal():
 for page in [15,16]:
  group=''
  for line in pages('04')[page-1].splitlines():
   # 4 SI values each followed by an inch-pound value, plus specific gravity.
   z=re.match(r'^(.*?)\s+(0\.\d+)\s+(.+)$',line)
   if z:
    vals=re.findall(r'\d+(?:\.\d+)?',z.group(3))
    if len(vals)!=8:continue
    label=z.group(1);indent=len(label)-len(label.lstrip())
    if not label.strip():continue
    # Page-specific leading margin is 11 or 7.
    base=11 if page==15 else 7
    name=woodname(label,group if indent>base else '')
    m=material(name,'04',page,'4-7',name)
    conditions={'reference_temperature_C_approx':24,'heat_flow':'across grain','source_line':line,'limitations':'Approximate values; conductivity may vary by as much as 20%; listed specific gravities are not species averages.'}
    observation(m,'specific_gravity',z.group(2),'1','04',page,'4-7',name,{**conditions,'volume_basis':'ovendry'})
    for prop,index,unit,moisture in [('thermal_conductivity',0,'W/(m K)',0),('thermal_conductivity',2,'W/(m K)',12),('thermal_resistivity',4,'m K/W',0),('thermal_resistivity',6,'m K/W',12)]:
     observation(m,prop,vals[index],unit,'04',page,'4-7',name,{**conditions,'moisture_content_percent':moisture})
   else:
    t=line.strip()
    if t in ('Hardwoods','Softwoods'):group='';continue
    if re.fullmatch(r'[A-Za-z ,\-]+',t) and len(t)<30 and t not in ('Species','gravity','Specific','Conductivity','Resistivity'):
     group=t
 # 4-8 heat capacity (left half of two-column page)
 m=material('Wood (general heat-capacity reference)','04',17,'4-8','temperature / moisture grid')
 for line in pages('04')[16].splitlines():
  s=line[:72];z=re.match(r'^\s*(\d{3})\s+(\d+)\s+\((\d+)\)\s+(.+)$',s)
  if not z:continue
  vals=re.findall(r'\d+(?:\.\d+)?',z.group(4))
  if len(vals)!=8:continue
  for j,mc in enumerate([0,5,12,20]):
   observation(m,'specific_heat_capacity',vals[2*j],'kJ/(kg K)','04',17,'4-8',f'{z.group(1)} K; {mc}% MC',{'temperature_K':int(z.group(1)),'temperature_C_as_printed':int(z.group(2)),'moisture_content_percent':mc,'source_line':line})

def dimensional_change():
 # Directly tabulated per-percentage-point moisture coefficients, not our own derivation.
 text=pages('13')[16]
 for col,(a,b) in enumerate([(9,66),(66,136)]):
  for line in text.splitlines():
   section=line[a:b]
   z=re.match(r'^(.*?)\s+(0\.\d{5})\s+(0\.\d{5})\s*$',section)
   if not z:continue
   rawname=z.group(1).strip()
   footnote_b=rawname.endswith('b')
   name=rawname[:-1] if footnote_b else rawname
   name=name.rstrip('-').strip()
   m=material(name,'13',17,'13-5',rawname)
   for direction,value in zip(['radial','tangential'],z.groups()[1:]):
    observation(m,'moisture_dimensional_change_coefficient_'+direction,value,'1/%MC','13',17,'13-5',rawname,{'direction':direction,'valid_moisture_content_percent_min':6,'valid_moisture_content_percent_max':14,'reference_dimension_moisture_content_percent':10,'moisture_change_basis':'per one percentage-point change in moisture content','assumed_shrinkage_start_moisture_content_percent':22 if footnote_b else 30,'source_line':line,'column':col+1,'source_derivation':'Table coefficients derived by source from total shrinkage; not calculated by this collector.'})

def main():
 RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 for ch,(url,title) in URLS.items():
  p=RAW/f'chapter_{ch}.pdf'
  if not p.exists():
   with urllib.request.urlopen(url,timeout=120) as src:p.write_bytes(src.read())
  assert p.read_bytes()[:5]==b'%PDF-'
  subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))],check=True,capture_output=True)
  SOURCES.append({'id':'wood:chapter-'+ch,'title':'Wood Handbook (2021), Chapter '+str(int(ch))+': '+title,'publisher':'USDA Forest Service, Forest Products Laboratory','url':url,'retrieved_at':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'local_path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'media_type':'application/pdf','license':'U.S. government publication; third-party cited values/material may need separate rights review. No item-specific license text extracted.','license_status':'unknown','description':'Official FPL-GTR-282 (2021), archived chapter PDF; printed page numbers are chapter-local.'})
 # Full original handbook preserved as a separate reference; no unparsed tables claimed.
 full=RAW/'wood_handbook_2021.pdf'
 fullurl='https://www.govinfo.gov/content/pkg/GOVPUB-A13-PURL-gpo158673/pdf/GOVPUB-A13-PURL-gpo158673.pdf'
 if not full.exists():
  import shutil
  with urllib.request.urlopen(fullurl,timeout=120) as src,full.open('wb') as dst:shutil.copyfileobj(src,dst)
 assert full.read_bytes()[:5]==b'%PDF-'
 SOURCES.append({'id':'wood:handbook-2021','title':'Wood Handbook—Wood as an Engineering Material, FPL-GTR-282 (2021), full original','publisher':'USDA Forest Service, Forest Products Laboratory; archived by U.S. Government Publishing Office','url':fullurl,'retrieved_at':datetime.datetime.fromtimestamp(full.stat().st_mtime,datetime.timezone.utc).isoformat(),'local_path':str(full.relative_to(ROOT)),'sha256':hashlib.sha256(full.read_bytes()).hexdigest(),'media_type':'application/pdf','license':'U.S. government publication; item-specific third-party rights not individually established','license_status':'unknown','description':'Full 546-page original preserved; dataset imports only the explicitly listed chapter tables.'})
 basic()
 props=[('specific_gravity','1'),('modulus_of_rupture','kPa'),('modulus_of_elasticity','MPa'),('work_to_maximum_load','kJ/m3'),('impact_bending_failure_drop_height','mm'),('compression_parallel_to_grain','kPa'),('compression_perpendicular_to_grain','kPa'),('shear_parallel_to_grain','kPa'),('tension_perpendicular_to_grain','kPa'),('side_hardness','N')]
 mechanical('5-3a',range(4,9),props,'United States')
 props4=[props[i] for i in [0,1,2,5,6,7]]
 mechanical('5-4a',[14,15],props4,'Canada')
 props5=[props[i] for i in [0,1,2,3,5,7,9]]
 mechanical('5-5a',range(18,22),props5,'Imported woods, world literature',True)
 thermal()
 dimensional_change()
 assert len(OBS)>3000,len(OBS)
 assert not SKIPPED,SKIPPED
 assert not any(')' in m['name'] and '(' not in m['name'] for m in MATERIALS.values())
 assert len({o['id'] for o in OBS})==len(OBS),'Duplicate observation IDs'
 # Known reference checks from original tables.
 alder=[o for o in OBS if o['material_id']=='wood:alder-red' and o['property']=='shrinkage_radial'];assert len(alder)==1 and alder[0]['value']==4.4
 emc=[o for o in OBS if o['property']=='equilibrium_moisture_content' and o['conditions'].get('temperature_C')==21.1 and o['conditions'].get('relative_humidity_percent')==50];assert len(emc)==1 and emc[0]['value']==9.2
 # Reference checks spanning fields, moisture and imported species row continuations.
 alder_strength=[o for o in OBS if o['material_id']=='wood:alder-red' and o['property']=='modulus_of_rupture']
 assert sorted(o['value'] for o in alder_strength)==[45000,68000]
 merbau=[o for o in OBS if o['property']=='modulus_of_rupture' and 'merbau-5-5a' in o['material_id'] and o['conditions'].get('moisture_content_percent')==15]
 assert len(merbau)==1 and merbau[0]['value']==115800
 for o in OBS:
  assert o['material_id'] in MATERIALS
  assert o['source_id'] in {x['id'] for x in SOURCES}
 fir=[o for o in OBS if o['material_id']=='wood:fir-white' and o['property']=='moisture_dimensional_change_coefficient_tangential']
 assert len(fir)==1 and fir[0]['value']==0.00245
 dump('sources.jsonl',SOURCES);dump('materials.jsonl',MATERIALS.values());dump('observations.jsonl',OBS)
 summary={'materials':len(MATERIALS),'observations':len(OBS),'sources':len(SOURCES),'numeric_observations':len(OBS),'properties':dict(collections.Counter(o['property'] for o in OBS)),'tables':dict(COUNTS),'parse_rejections':SKIPPED,'known_limitations':['Generic species means, not graded structural design allowables.','Moisture and thermal reference tables have source-specific qualifications preserved in conditions.','No missing values are replaced by zero; blank specific gravity not carried forward.','Species common names have not been globally taxonomically reconciled; imported aliases may remain separate.','Whole chapters 4, 5 and 13 preserved; only explicitly supported table layouts are parsed.','Chapter 13 Table 13-5 coefficients are reported values; no dimensional-change calculation is executed.','Government-publication status noted but item-specific redistribution license not established.'],'attempted_failures':['Direct www.fpl.fs.usda.gov chapter URLs returned 403; official research.fs.usda.gov download worked.']}
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
