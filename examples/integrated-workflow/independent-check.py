from pathlib import Path
from decimal import Decimal
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,math,os,struct,subprocess

ROOT=Path(__file__).resolve().parents[2]
CASE=ROOT/'examples/integrated-workflow'
OUT=CASE/'independent-evidence';OUT.mkdir(exist_ok=True)
MODELS=[CASE/v/f for v in ['base','revised'] for f in ['model.sc','model.bimc','unbound.bimc','transfer.glb','roundtrip.glb']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in MODELS}
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
def run(label,args,expected=0):
 r=subprocess.run([str(x) for x in args],cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
 (OUT/(label+'.stdout.json')).write_text(r.stdout)
 (OUT/(label+'.stderr.txt')).write_text(r.stderr)
 assert r.returncode==expected,(label,r.returncode,r.stderr)
 return r

def bim_records(r):return [json.loads(x) for x in r.stdout.splitlines() if x.strip()]
def glb(path):
 b=path.read_bytes();pos=12;doc=None;binary=None
 while pos<len(b):
  length,typ=struct.unpack_from('<II',b,pos);chunk=b[pos+8:pos+8+length];pos+=8+length
  if typ==0x4e4f534a:doc=json.loads(chunk)
  elif typ==0x004e4942:binary=chunk
 def accessor(index):
  a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC3':3}[a['type']];fmt={5126:'f',5125:'I',5123:'H'}[a['componentType']];size=struct.calcsize('<'+fmt*n);start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
  return [struct.unpack_from('<'+fmt*n,binary,start+i*stride) for i in range(a['count'])]
 # Assert this fixture's placement transform instead of silently assuming a generic scene.
 root=doc['nodes'][0];assert root['scale']==[.001]*3 and all(abs(x-y)<1e-14 for x,y in zip(root['rotation'],[-2**-.5,0,0,2**-.5]))
 meshes={}
 for node in doc['nodes']:
  if 'mesh'not in node:continue
  assert set(node)=={'mesh','name'}
  tris=[]
  for prim in doc['meshes'][node['mesh']]['primitives']:
   vertices=accessor(prim['attributes']['POSITION']);indices=[i[0] for i in accessor(prim['indices'])]
   tris += [[vertices[i] for i in indices[j:j+3]] for j in range(0,len(indices),3)]
  meshes[node['name']]=tris
 return meshes,doc

def key(tri):return tuple(sorted(tuple(round(v,7) for v in point) for point in tri))
def volume(tris):
 # Independent direct determinant integration in mm; no CAD measurements or adapter implementation.
 return abs(math.fsum(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]) for a,b,c in tris)/6)/1e9
results={}
for revision,t in [('base',100),('revised',120)]:
 folder=CASE/revision
 args=['bimcraft-cli','run',folder/'model.bimc','--cmd','elements {"category":"component"}']
 for name in ['ConcretePanel','Rail_A','Rail_B']:args += ['--cmd','family '+json.dumps({'name':name})]
 records=bim_records(run(revision+'-bim-live',args))
 rows=next(x['elements'] for x in records if isinstance(x.get('elements'),list));assert len(rows)==3
 families={x['name']:x['family'] for x in records if 'family'in x}
 source=json.loads(run(revision+'-cad-live',['solidcraft-cli','eval',folder/'model.sc']).stdout)
 returned=json.loads(run(revision+'-roundtrip-live',['solidcraft-cli','eval','--in',folder/'roundtrip.glb']).stdout)
 forward,doc=glb(folder/'transfer.glb')
 expected={'ConcretePanel':float((Decimal('1.5')-Decimal('.3')*Decimal('.2'))*Decimal(t)/1000),'Rail_A':.0008,'Rail_B':.0008}
 source_by={x['name']:x for x in source['bodies']};returned_by={x['name']:x for x in returned['bodies']}
 checks=[]
 for row in rows:
  name=row['family'];form=families[name]['forms'][0]
  assert row['angle']==0
  world=[[[p[0]+row['at'][0],p[1]+row['at'][1],p[2]+row['offset']] for p in tri] for tri in form['mesh']]
  equal=Counter(map(key,world))==Counter(map(key,forward[name]));assert equal,name+' triangle mismatch'
  v=volume(world);assert math.isclose(v,expected[name],rel_tol=1e-12)
  back=returned_by[str(row['id'])];assert back['closed']
  error=max(abs(a-b) for end in ['min','max'] for a,b in zip(back['bbox'][end],source_by[name]['bbox'][end]));assert error<.002
  checks.append({'part':name,'triangles':len(world),'GLB_BIM_world_triangles_equal_1e-7mm':equal,'independently_integrated_volume_m3':v,'expected_volume_m3':expected[name],'return_max_bbox_error_mm':error,'returned_volume_relative_error':abs(back['volume_mm3']/1e9/expected[name]-1)})
 # Run guard behavior ourselves with all output destinations confined to /tmp.
 run(revision+'-unbound-live',['python3','materials.py','assess',folder/'unbound.bimc','--software','bimcraft','--mesh-quantities','--bindings',folder/'unbound-bindings.json','--out',OUT/(revision+'-unbound-assessment.json')],2)
 unbound=json.loads((OUT/(revision+'-unbound-assessment.json')).read_text());assert unbound['status']=='partial'and all(x['status']=='unresolved'and x['calculations']=={} for x in unbound['elements'])
 results[revision]={'component_count':len(rows),'parts':checks,'unbound_guard_passed':True,'forward_glb_material_names':[m['name']for m in doc['materials']]}
for soft,ext in [('solidcraft','sc'),('bimcraft','bimc')]:
 args=['python3','materials.py','assess',CASE/'revised'/('model.'+ext),'--software',soft,'--bindings',CASE/'base'/('solid-bindings.json'if soft=='solidcraft'else'bim-bindings.json'),'--out',OUT/(soft+'-stale-assessment.json')]
 if soft=='bimcraft':args+=['--mesh-quantities']
 r=run(soft+'-stale-live',args,1);assert json.loads(r.stderr)['code']=='model_changed';assert not(OUT/(soft+'-stale-assessment.json')).exists()
results['stale_guard_passed']=True
results['source_models_unchanged']=all(sha(p)==before[str(p)] for p in MODELS);assert results['source_models_unchanged']
(OUT/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
