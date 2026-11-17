import sys,random,json,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import materials
root=materials.ROOT
with materials.connect(materials.DEFAULT_DB) as db:
 sources={r['id']:dict(r) for r in db.execute('SELECT id,local_path FROM sources')}
 bounds=db.execute("SELECT min(rowid),max(rowid) FROM observations WHERE dataset_id='environmental'").fetchone()
 cache={};verified=0
 for rowid in random.Random(20261117).sample(range(bounds[0],bounds[1]+1),150):
  o=dict(db.execute('SELECT * FROM observations WHERE rowid=?',[rowid]).fetchone());sid=o['source_id']
  if sid not in cache:cache[sid]=json.loads((root/sources[sid]['local_path']).read_text())
  loc=o['source_locator'];value=cache[sid]
  assert loc.startswith('/'),loc
  for token in loc[1:].split('/'):
   token=token.replace('~1','/').replace('~0','~')
   value=value[int(token)] if isinstance(value,list) else value[token]
  assert float(value)==o['value'],(o['id'],value,o['value'])
  verified+=1
 tech=0
 for o in db.execute("SELECT * FROM observations WHERE dataset_id='technical' AND source_locator LIKE '$.%' LIMIT 100"):
  sid=o['source_id']
  if sid not in cache:cache[sid]=json.loads((root/sources[sid]['local_path']).read_text())
  value=cache[sid]
  for field,idx in re.findall(r'\.([^\.\[\]]+)|\[(\d+)\]',o['source_locator'][1:]):value=value[int(idx)] if idx else value[field]
  assert float(value)==o['value'],o['id'];tech+=1
 import openpyxl
 books={};br18=0
 for o in db.execute("SELECT * FROM observations WHERE dataset_id='br18'"):
  src=sources[o['source_id']]
  if not src['local_path'].endswith('.xlsx'):continue
  if o['source_id'] not in books:books[o['source_id']]=openpyxl.load_workbook(root/src['local_path'],read_only=False,data_only=False)
  sheet,location=o['source_locator'].split('!');cell=location.split(':')[0]
  value=books[o['source_id']][sheet][cell].value
  assert isinstance(value,(int,float)) and value==o['value'],(o['id'],value,o['value'])
  br18+=1
 report={'environmental_random_values_checked_against_original_json':verified,'technical_values_checked_against_original_json':tech,'br18_workbook_cells_checked_against_original':br18,'seed':20261117}
 print(json.dumps(report,indent=2))
