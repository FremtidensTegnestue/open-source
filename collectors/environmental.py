#!/usr/bin/env python3
"""Archive OEKOBAUDAT public soda4LCA JSON and extract reported values.

Original JSON is the primary published machine-readable source, preserved byte-for-byte.
No upstream code runs, no totals/normalisation are invented. stdlib Python only.
"""
import argparse,concurrent.futures,datetime,hashlib,json,math,pathlib,re,time,urllib.request,urllib.parse,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASES={'oekobaudat':'https://oekobaudat.de/OEKOBAU.DAT/resource'}
USER_AGENT='FremtidensTegnestue-MaterialResearch/0.1'

def dumps(o):return json.dumps(o,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def fetch(url,rel,refresh=False):
 p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);meta=p.with_suffix(p.suffix+'.http.json')
 if p.exists() and meta.exists() and not refresh:return p,json.loads(meta.read_text())
 for attempt in range(4):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'application/json'})
   with urllib.request.urlopen(req,timeout=50) as response:
    data=response.read();headers={'url':url,'final_url':response.url,'retrieved_at':stamp(),'status':response.status,'content_type':response.headers.get('Content-Type'),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
   # Avoid recording transient error HTML as a dataset.
   json.loads(data)
   tmp=p.with_suffix(p.suffix+'.part');tmp.write_bytes(data);tmp.replace(p);meta.write_text(dumps(headers)+'\n');return p,headers
  except Exception:
   if attempt==3:raise
   time.sleep(1.5*(attempt+1))
def lang(value):
 if isinstance(value,str):return value
 if isinstance(value,dict):return str(value.get('value',''))
 if not isinstance(value,list):return ''
 for l in ['en','da','de']:
  found=[x.get('value','') for x in value if x.get('lang')==l and x.get('value')]
  if found:return found[0]
 return next((x.get('value','') for x in value if x.get('value')),'')
def slug(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
def numeric(v):
 if isinstance(v,bool) or v is None:return None
 try:x=float(str(v).strip())
 except (ValueError,TypeError):return None
 return x if math.isfinite(x) else None
def cat(item):
 s=(item.get('classific','')+' '+item.get('name','')).lower()
 for pattern,value in [(r'holz|wood|timber','wood'),(r'beton|concrete|zement|cement','concrete'),(r'metall|metal|stahl|steel|aluminium|copper','metal'),(r'dämm|insulat|mineral wool','insulation'),(r'glas|glass','glass'),(r'kunststoff|plastic|polymer|polyethylene','polymer'),(r'ziegel|brick|masonry|kalksand','masonry'),(r'gips|gypsum','gypsum')]:
  if re.search(pattern,s):return value
 return 'other'
def source_record(key,item,path,meta,data=None):
 version=item.get('version','');ident=f'environmental:{key}:{item.get("uuid",path.stem)}@{version}'
 own=(data or {}).get('administrativeInformation',{}).get('publicationAndOwnership',{})
 license=own.get('licenseType','Unknown; see source record and program terms')
 status='verified' if own.get('licenseType') else 'unknown'
 if license not in ['Free of charge for all users and uses','Unknown; see source record and program terms']:status='restricted'
 return dict(id=ident,title=item.get('name',path.name),publisher=key,url=meta['url'],retrieved_at=meta['retrieved_at'],local_path=str(path.relative_to(ROOT)),sha256=meta['sha256'],media_type=meta.get('content_type','application/json'),license=license,license_status=status,description=dumps({'dataset_version':version,'copyright':own.get('copyright'),'accessRestrictions':own.get('accessRestrictions'),'owner':own.get('referenceToOwnershipOfDataSet'),'programOperator':item.get('regAuthority'),'regNo':item.get('regNo')}))
def extract(key,item,data,sid):
 matid=sid.replace('environmental:','environmental:material:',1)
 pi=data.get('processInformation',{});di=pi.get('dataSetInformation',{})
 names=di.get('name',{}).get('baseName',[]);name=lang(names) or item.get('name','Unnamed dataset')
 kind='generic' if item.get('type')=='LCI result' or 'generic' in item.get('subType','').lower() else 'product'
 material=dict(id=matid,name=name,kind=kind,category=cat(item),aliases=list(dict.fromkeys([x.get('value') for x in names if x.get('value')]+[item.get('name',name)])),description=lang(di.get('generalComment',[])),source_id=sid,source_locator='/processInformation/dataSetInformation')
 own=data.get('administrativeInformation',{}).get('publicationAndOwnership',{})
 timeinfo=pi.get('time',{})
 condition={'dataset_uuid':item['uuid'],'dataset_version':item.get('version'),'geography':item.get('geo'),'reference_year':timeinfo.get('referenceYear',item.get('refYear')),'valid_until':timeinfo.get('dataSetValidUntil',item.get('validUntil')),'dataset_type':item.get('type'),'subtype':item.get('subType'),'registration':item.get('regNo'),'classification':item.get('classific'),'standards':[c.get('name') for c in item.get('compliance',[])],'copyright':own.get('copyright')}
 exchanges=data.get('exchanges',{}).get('exchange',[])
 refs=pi.get('quantitativeReference',{}).get('referenceToReferenceFlow',[])
 declared=[]
 for i,x in enumerate(exchanges):
  if x.get('referenceFlow') or x.get('dataSetInternalID') in refs:
   for fp in x.get('flowProperties',[]):
    if fp.get('referenceFlowProperty'):
     declared.append({'exchange_index':i,'amount':fp.get('meanValue'),'unit':fp.get('referenceUnit'),'name':lang(fp.get('name',[])),'exchange_mean_amount':x.get('meanAmount'),'resulting_flow_amount':x.get('resultingflowAmount')})
 condition['declared_references']=declared
 unit=declared[0].get('unit') if len(declared)==1 else None
 declared_amount=declared[0].get('amount') if len(declared)==1 else None
 if declared_amount is not None:condition['declared_amount']=declared_amount
 def obs(path,prop,value,unit_,module=None,extra=None,method=None):
  val=numeric(value)
  if val is None:return None
  conditions={**condition,**(extra or {})}
  o=dict(id=sid+':'+hashlib.sha256(path.encode()).hexdigest()[:18],material_id=matid,property=prop,value=val,value_text=str(value),unit=unit_,source_id=sid,source_locator=path,data_status='reported',conditions=conditions)
  if module is not None:o['module']=str(module)
  if unit is not None:o['declared_unit']=unit
  if declared_amount is not None:o['basis']=f'{declared_amount} {unit}'
  if method:o['method']=method
  return o
 observations=[];missing=[]
 def append(path,prop,v,u,module=None,extra=None,method=None):
  o=obs(path,prop,v,u,module,extra,method)
  if o:observations.append(o)
  elif v is not None:missing.append({'locator':path,'value':v,'module':module,'property':prop})
 for i,result in enumerate(data.get('LCIAResults',{}).get('LCIAResult',[])):
  ref=result.get('referenceToLCIAMethodDataSet',{});label=lang(ref.get('shortDescription',[]));methodid=ref.get('refObjectId','unknown');anies=result.get('other',{}).get('anies',[])
  u=next((lang(a.get('value',{}).get('shortDescription',[])) for a in anies if a.get('name')=='referenceToUnitGroupDataSet' and isinstance(a.get('value'),dict)),None)
  # Preserve each method; never add A1-A3 to A1/A2/A3 or module D to lifecycle totals.
  tag=re.search(r'\(([^()]+)\)\s*$',label);prop=slug(tag.group(1) if tag else label) or 'environmental_impact'
  for n,a in enumerate(anies):
   if 'module' in a:append(f'/LCIAResults/LCIAResult/{i}/other/anies/{n}/value',prop,a.get('value'),u,a['module'],{'indicator_name':label,'indicator_uuid':methodid,**{k:v for k,v in a.items() if k not in ['value','module']}},methodid)
 for i,x in enumerate(exchanges):
  label=lang(x.get('referenceToFlowDataSet',{}).get('shortDescription',[]));flowid=x.get('referenceToFlowDataSet',{}).get('refObjectId');anies=x.get('other',{}).get('anies',[])
  u=next((lang(a.get('value',{}).get('shortDescription',[])) for a in anies if a.get('name')=='referenceToUnitGroupDataSet' and isinstance(a.get('value'),dict)),None)
  tag=re.search(r'\(([^()]+)\)\s*$',label);prop=slug(tag.group(1) if tag else label) or 'resource_flow'
  for n,a in enumerate(anies):
   if 'module' in a:append(f'/exchanges/exchange/{i}/other/anies/{n}/value',prop,a.get('value'),u,a['module'],{'indicator_name':label,'flow_uuid':flowid,'exchange_direction':x.get('exchange direction'),**{k:v for k,v in a.items() if k not in ['value','module']}})
  # Technical material properties are already explicit numeric fields.
  for n,p in enumerate(x.get('materialProperties',[])):
   append(f'/exchanges/exchange/{i}/materialProperties/{n}/value',slug(p.get('name','material_property')),p.get('value'),p.get('unit'),extra={'property_name':p.get('name'),'unit_description':p.get('unitDescription'),'reference_flow':bool(x.get('referenceFlow'))})
  if x.get('referenceFlow') or x.get('dataSetInternalID') in refs:
   for n,p in enumerate(x.get('flowProperties',[])):
    append(f'/exchanges/exchange/{i}/flowProperties/{n}/meanValue','reference_flow_'+slug(lang(p.get('name',[]))),p.get('meanValue'),p.get('referenceUnit'),extra={'flow_property_name':lang(p.get('name',[])),'flow_property_uuid':p.get('uuid'),'reference_flow_property':p.get('referenceFlowProperty',False)})
 return material,observations,missing

def attachment_register():
 stage=ROOT/'data/staging/environmental';count=0
 with (stage/'attachments.jsonl').open('w') as out:
  for path in sorted((ROOT/'data/raw/environmental/oekobaudat/processes').glob('*.json')):
   if path.name.endswith('.http.json'):continue
   data=json.loads(path.read_text());uuid,version=path.stem.split('_',1);sid='environmental:oekobaudat:'+uuid+'@'+version
   def walk(value,pointer):
    nonlocal count
    if isinstance(value,dict):
     for k,v in value.items():
      if k=='resourceURLs' and isinstance(v,list):
       for i,url in enumerate(v):
        out.write(dumps(dict(source_id=sid,source_locator=pointer+'/resourceURLs/'+str(i),url=url,title=lang(value.get('shortDescription',[])),download_status='referenced_not_downloaded'))+'\n');count+=1
      else:walk(v,pointer+'/'+k)
    elif isinstance(value,list):
     for i,v in enumerate(value):walk(v,pointer+'/'+str(i))
   walk(data,'')
 return count

def policy_sources():
 records=[]
 for name,title,publisher,url in [
  ('oekobaudat-data-users.html','OEKOBAUDAT data users and terms of use','BBSR / BMWSB','https://oekobaudat.de/en/guidance/data-users.html'),
  ('eco-platform-terms.html','ECO Platform terms: source evaluated but bulk collection excluded','ECO Platform','https://www.eco-platform.org/terms-conditions.html')]:
  path=ROOT/'data/raw/environmental/terms'/name;path.parent.mkdir(parents=True,exist_ok=True);metapath=path.with_suffix(path.suffix+'.http.json')
  if not path.exists():
   req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
   with urllib.request.urlopen(req,timeout=30) as response:path.write_bytes(response.read())
  if metapath.exists():meta=json.loads(metapath.read_text())
  else:
   meta={'url':url,'retrieved_at':stamp(),'sha256':sha(path)};metapath.write_text(dumps(meta)+'\n')
  records.append(dict(id='environmental:terms:'+name,title=title,publisher=publisher,url=url,retrieved_at=meta['retrieved_at'],local_path=str(path.relative_to(ROOT)),sha256=meta['sha256'],media_type='text/html',license='Policy text preserved as source evidence; no blanket relicensing',license_status='unknown'))
 return records

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('--provider',choices=[*BASES,'all'],default='all');parser.add_argument('--offline',action='store_true');parser.add_argument('--refresh-index',action='store_true',help='Refresh catalogue pages; immutable versioned process files remain cached');args=parser.parse_args()
 if args.offline and args.refresh_index:parser.error('--offline and --refresh-index are mutually exclusive')
 stage=ROOT/'data/staging/environmental';stage.mkdir(parents=True,exist_ok=True);failed=[];total={'sources':0,'materials':0,'observations':0};property_counts=collections.Counter();categories=collections.Counter();modules=collections.Counter();licenses=collections.Counter();providers={};started=stamp()
 with (stage/'sources.jsonl').open('w') as sourceout,(stage/'materials.jsonl').open('w') as matout,(stage/'observations.jsonl').open('w') as obsout,(stage/'unparsed-values.jsonl').open('w') as missout:
  for policy in policy_sources():sourceout.write(dumps(policy)+'\n');total['sources']+=1
  for key,base in BASES.items():
   if args.provider not in ['all',key]:continue
   entries=[];offset=0;seen=set();pc={'listed':0,'materials':0,'observations':0,'failed':0}
   while True:
    url=f'{base}/processes?format=json&startIndex={offset}&pageSize=500'
    if args.offline:
     path=ROOT/f'data/raw/environmental/{key}/index/{offset:06d}.json';meta=json.loads(path.with_suffix('.json.http.json').read_text())
    else:path,meta=fetch(url,f'data/raw/environmental/{key}/index/{offset:06d}.json',refresh=args.refresh_index)
    index=json.loads(path.read_text());items=index.get('data',[])
    src=source_record(key,{'name':f'{key} published process index offset {offset}'},path,meta);sourceout.write(dumps(src)+'\n');total['sources']+=1
    for item in items:
     k=(item.get('uuid'),item.get('version'))
     if k not in seen:entries.append(item);seen.add(k)
    offset+=len(items)
    if not items or offset>=index.get('totalCount',offset):break
   pc['listed']=len(entries);pc['reported_total']=index.get('totalCount');print(dumps({'provider':key,'indexed':len(entries),'time':stamp()}),flush=True)
   def load(item):
    try:
     filename=item['uuid']+'_'+item.get('version','unknown')+'.json';rel=f'data/raw/environmental/{key}/processes/{filename}';url=f'{base}/processes/{item["uuid"]}?format=json&view=extended&version='+urllib.parse.quote(item.get('version',''))
     if args.offline:
      p=ROOT/rel;meta=json.loads(p.with_suffix('.json.http.json').read_text())
     else:p,meta=fetch(url,rel)
     data=json.loads(p.read_text());src=source_record(key,item,p,meta,data);material,observations,missing=extract(key,item,data,src['id']);return src,material,observations,missing
    except Exception as exc:return {'error':str(exc),'provider':key,'item':item}
   with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
    for n,result in enumerate(pool.map(load,entries),1):
     if isinstance(result,dict):failed.append(result);pc['failed']+=1;continue
     src,material,observations,missing=result;sourceout.write(dumps(src)+'\n');matout.write(dumps(material)+'\n');licenses[src['license']]+=1;categories[material['category']]+=1;total['sources']+=1;total['materials']+=1;pc['materials']+=1
     for o in observations:obsout.write(dumps(o)+'\n');property_counts[o['property']]+=1;modules[o.get('module','technical')]+=1
     for m in missing:missout.write(dumps({'source_id':src['id'],**m})+'\n')
     count=len(observations);total['observations']+=count;pc['observations']+=count
     if n%100==0:print(dumps({'provider':key,'processed':n,'counts':total,'time':stamp()}),flush=True)
   providers[key]=pc
   sourceout.flush();matout.flush();obsout.flush();missout.flush()
 (stage/'failures.json').write_text(json.dumps(failed,ensure_ascii=False,indent=2)+'\n')
 summary={'dataset':'environmental','started_at':started,'finished_at':stamp(),'counts':total,'providers':providers,'properties':dict(property_counts),'categories':dict(categories),'modules':dict(modules),'record_license_fields':dict(licenses),'failures':len(failed),'excluded_sources':[{'source':'ECO SMDP / ECO Portal','reason':'Current ECO terms require an API license and restrict redistribution/deconstruction into a new data product; endpoint reachability is not sufficient authorization.','url':'https://www.eco-platform.org/terms-conditions.html'}],'limitations':['Published JSON primary source preserved byte-for-byte; referenced PDF attachments have not all been downloaded.','Historical/expired datasets retained with validity years; not a current-only catalogue.','No unit normalisation, aggregation or environmental totals calculated.','Geographic and technical applicability must be evaluated for each project; a material category is a navigation aid.','Publication license fields are recorded per dataset; no blanket redistribution license inferred.','Only explicit numeric structured values imported; prose technical data and missing markers remain in originals/unparsed-values.','Versions are pinned to index version; dataset identifiers retain provider and version, and duplicates across providers are not merged.']}
 summary['referenced_attachments']=attachment_register()
 (stage/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(dumps(summary),flush=True)
if __name__=='__main__':main()
