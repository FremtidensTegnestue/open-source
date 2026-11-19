#!/usr/bin/env python3
"""Build searchable derivatives and inventories without executing upstream code."""
import collections, csv, hashlib, json, pathlib, re, shutil, zipfile
import openpyxl
from pypdf import PdfReader
ROOT=pathlib.Path(__file__).resolve().parent

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n')

def main():
    archives=[]; queue=list((ROOT/'archive').rglob('*.zip'))+list((ROOT/'upstream').rglob('*.zip')); seen=set()
    while queue:
        archive=queue.pop(0)
        if archive in seen: continue
        seen.add(archive)
        target=ROOT/'unpacked'/archive.relative_to(ROOT).with_suffix('')
        entry={'archive':str(archive.relative_to(ROOT)),'directory':str(target.relative_to(ROOT)),'members':[]}
        try:
            with zipfile.ZipFile(archive) as z:
                entry['crc_error']=z.testzip()
                for info in z.infolist():
                    entry['members'].append({'name':info.filename,'bytes':info.file_size,'crc32':f'{info.CRC:08x}'})
                    relative=pathlib.PurePosixPath(info.filename.replace('\\','/'))
                    if relative.is_absolute() or '..' in relative.parts: raise ValueError('Unsafe ZIP path')
                    dest=target.joinpath(*relative.parts)
                    if info.is_dir(): dest.mkdir(parents=True,exist_ok=True); continue
                    if (info.external_attr>>16)&0o170000==0o120000: continue
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(info) as src,dest.open('wb') as out: shutil.copyfileobj(src,out)
                    if dest.suffix.lower()=='.zip': queue.append(dest)
        except Exception as exc: entry['error']=str(exc)
        archives.append(entry)
    write_json(ROOT/'catalog/archives.json',archives)
    workbooks=[]; pdfs=[]; graphs=[]
    candidates=[p for group in ['archive','upstream','unpacked'] for p in (ROOT/group).rglob('*') if p.is_file()]
    for p in candidates:
        rel=p.relative_to(ROOT); suffix=p.suffix.lower()
        if suffix in ('.xlsx','.xlsm') and not p.name.startswith('~$'):
            record={'path':str(rel),'sheets':[]}
            try:
                w=openpyxl.load_workbook(p,data_only=False,read_only=False,keep_links=False)
                output=ROOT/'extracted/workbooks'/rel
                output.mkdir(parents=True,exist_ok=True)
                for i,s in enumerate(w.worksheets):
                    cells=[]; formulas=[]
                    for row in s:
                        for c in row:
                            if c.value is None: continue
                            value=c.value
                            if c.data_type=='f':
                                value=value if isinstance(value,str) else str(getattr(value,'text',value))
                                formulas.append({'cell':c.coordinate,'formula':value})
                            cells.append({'cell':c.coordinate,'type':c.data_type,'value':value})
                    name=f'{i+1:02d}-'+re.sub(r'[^\w.-]+','_',s.title)
                    write_json(output/(name+'.json'),{'sheet':s.title,'state':s.sheet_state,'cells':cells,'formulas':formulas})
                    with (output/(name+'.csv')).open('w',newline='') as out:
                        writer=csv.writer(out)
                        for row in s.iter_rows(values_only=True): writer.writerow([str(v) if v is not None else '' for v in row])
                    record['sheets'].append({'name':s.title,'state':s.sheet_state,'rows':s.max_row,'columns':s.max_column,'formula_count':len(formulas),'extracted':str((output/(name+'.json')).relative_to(ROOT)),'formula_examples':formulas[:8]})
                w.close()
                with zipfile.ZipFile(p) as z:
                    record['has_vba']='xl/vbaProject.bin' in z.namelist()
                    record['external_links']=[n for n in z.namelist() if n.startswith('xl/externalLinks/')]
                record['calculated']=False
            except Exception as e: record['error']=str(e)
            workbooks.append(record)
        elif suffix=='.pdf':
            rec={'path':str(rel)}
            try:
                if p.read_bytes()[:5]!=b'%PDF-': raise ValueError('Downloaded response is not PDF (HTML or other content)')
                reader=PdfReader(p); rec['pages']=len(reader.pages)
                dest=ROOT/'extracted/pdf'/rel.with_suffix('.txt');dest.parent.mkdir(parents=True,exist_ok=True)
                texts=[]
                for i,page in enumerate(reader.pages): texts.append(f'\n--- Side {i+1} ---\n'+(page.extract_text() or ''))
                dest.write_text('\n'.join(texts));rec['text_path']=str(dest.relative_to(ROOT));rec['text_characters']=sum(len(t) for t in texts)
            except Exception as e: rec['error']=str(e)
            pdfs.append(rec)
        elif suffix in ('.dyn','.dyf'):
            text=p.read_text(errors='replace');rec={'path':str(rel),'format':'json' if text.lstrip().startswith('{') else 'xml','python_fragments':[]}
            try:
                if rec['format']=='json':
                    data=json.loads(text);nodes=data.get('Nodes',[]);rec['node_count']=len(nodes)
                    for node in nodes:
                        if node.get('Code'):rec['python_fragments'].append(node['Code'])
                else:
                    import xml.etree.ElementTree as ET
                    tree=ET.fromstring(text)
                    for n in tree.iter():
                        if n.tag.lower().endswith('script') and n.text: rec['python_fragments'].append(n.text)
            except Exception as e:rec['error']=str(e)
            if rec['python_fragments']:
                dest=ROOT/'extracted/dynamo'/rel.with_suffix('.txt');dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text('\n\n'.join(f'# Fragment {i+1}\n{s}' for i,s in enumerate(rec.pop('python_fragments'))));rec['extracted_code']=str(dest.relative_to(ROOT))
            graphs.append(rec)
    write_json(ROOT/'catalog/workbooks.json',workbooks);write_json(ROOT/'catalog/pdfs.json',pdfs);write_json(ROOT/'catalog/dynamo.json',graphs)
    inventory=[]
    for group in ['archive','upstream','unpacked','extracted']:
        for p in sorted((ROOT/group).rglob('*')):
            if not p.is_file():continue
            sha=hashlib.sha256()
            with p.open('rb') as src:
                for block in iter(lambda:src.read(1024*1024),b''):sha.update(block)
            inventory.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha.hexdigest(),'extension':p.suffix.lower()})
    write_json(ROOT/'catalog/files.json',inventory)
    write_json(ROOT/'catalog/summary.json',{'files':len(inventory),'bytes':sum(f['bytes'] for f in inventory),'extensions':dict(collections.Counter(f['extension'] for f in inventory)),'archives':len(archives),'workbooks':len(workbooks),'pdfs':len(pdfs),'dynamo_files':len(graphs),'archive_errors':[x for x in archives if x.get('error') or x.get('crc_error')],'workbook_errors':[x for x in workbooks if x.get('error')],'pdf_errors':[x for x in pdfs if x.get('error')]})
    print((ROOT/'catalog/summary.json').read_text())

if __name__=='__main__':main()
