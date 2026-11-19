#!/usr/bin/env python3
"""Collect Danish official BR18 tables 7–11 and their original downloadable files.

Original Excel/HTML values are retained. No lifecycle total, SI conversion or legal
compliance conclusion is computed. Reference/installation factors remain distinct.
"""
import concurrent.futures
import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.parse
import requests
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/br18'
STAGE = ROOT / 'data/staging/br18'
BASE = 'https://www.bygningsreglementet.dk'

class Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.table=None; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table': self.table=[]
        elif self.table is not None and tag=='tr': self.row=[]
        elif self.row is not None and tag in ('td','th'): self.cell=[]
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(''.join(self.cell).strip());self.cell=None
        elif tag=='tr' and self.row is not None:
            self.table.append(self.row);self.row=None
        elif tag=='table' and self.table is not None:
            self.tables.append(self.table);self.table=None
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)

def fetch(url, name, title=None):
    path=RAW/name;path.parent.mkdir(parents=True,exist_ok=True)
    metadata=path.with_name(path.name+'.http.json')
    if not path.exists():
        response=requests.get(url,headers={'User-Agent':'Mozilla/5.0 (material source archive)'},timeout=60)
        response.raise_for_status()
        if name.endswith('.pdf') and not response.content.startswith(b'%PDF-'):raise ValueError('Not a PDF')
        if name.endswith('.xlsx') and not response.content.startswith(b'PK'):raise ValueError('Not an Excel archive')
        path.write_bytes(response.content)
        metadata.write_text(json.dumps({'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'final_url':response.url,'media_type':response.headers.get('Content-Type','')}))
    meta=json.loads(metadata.read_text())
    return dict(id='br18:source:'+name,title=title or name,publisher='Social- og Boligstyrelsen' if urllib.parse.urlsplit(url).netloc.endswith('bygningsreglementet.dk') else urllib.parse.urlsplit(url).netloc,url=url,retrieved_at=meta['retrieved_at'],local_path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),media_type=meta['media_type'],license='No explicit reuse license identified in this download; preserve publisher terms and third-party rights',license_status='unknown')

def numeric(value):
    if isinstance(value,(float,int)) and not isinstance(value,bool):return value
    if isinstance(value,str) and re.fullmatch(r'[-+]?\d+(?:[.,]\d+)?(?:[Ee][-+]?\d+)?',value.strip()):return float(value.strip().replace(',','.'))
    return None

def category(name):
    name=name.casefold()
    for cat, terms in [('insulation',['isolering','uld','eps','xps','mineral wool']),('wood',['træ','træfiber','kork','spån','krydsfiner','osb','mdf']),('concrete',['beton','cement','mørtel','puds']),('masonry',['tegl','mursten','klinker','natursten','kalksand','pimpsten']),('metal',['stål','aluminium','zink','metal','kobber','jern']),('glass',['glas','vindue']),('gypsum',['gips']),('polymer',['plast','pvc','poly','bitumen','tagpap','membran'])]:
        if any(t in name for t in terms):return cat
    return 'other'

def main():
    RAW.mkdir(parents=True,exist_ok=True);STAGE.mkdir(parents=True,exist_ok=True)
    sources=[];materials=[];observations=[];failures=[]
    pages={}
    for n in (7,8,9,10,11):
        src=fetch(f'{BASE}/bilag/b2/bilag_2/tabel_{n}/?ajax=1',f'table-{n}.html',f'BR18 bilag 2 tabel {n}, public website snapshot')
        sources.append(src);pages[n]=src
    xlsx=fetch(BASE+'/media/1o1nnozd/tabel-7-2025.xlsx','table-7-2025.xlsx','BR18 bilag 2 tabel 7 — generisk datagrundlag 2025')
    sources.append(xlsx)
    sheet=openpyxl.load_workbook(ROOT/xlsx['local_path'],data_only=False).active
    refs=set()
    for n,row in enumerate(sheet.iter_rows(min_row=2,values_only=True),2):
        row=list(row[:14]);sid,typ,foreign,name,*_=row
        if not isinstance(sid,str) or not sid.startswith('#'):continue
        mid='br18:t7:'+sid.lstrip('#')+f':row{n}'
        standard=sid.startswith('#S')
        materials.append(dict(id=mid,name=str(name).strip(),kind='assembly' if standard else 'generic',category=category(str(name)),aliases=[str(foreign)] if foreign and foreign!='-' else [],source_id=xlsx['id'],source_locator=f'Sheet1!A{n}:N{n}',description='Official reference record; subtype/material classification is heuristic',original_id=sid,source_data_type=typ))
        conditions={'reference_amount':row[8],'reference_unit':row[9],'original_data_type':typ,'underlying_source_url':row[12],'source_comment':row[13],'record_scope':'installation_area_reference_factor' if standard else 'official_material_or_construction_reference'}
        if standard:
            conditions.update(reference_area='total heated floor area plus heated basement area', basis_source_id=pages[7]['id'], basis_source_locator='HTML paragraph under Standardværdier for installationer: samlet opvarmede etageareal plus opvarmede kælderareal')
        if isinstance(row[12],str) and '.pdf' in row[12].lower():refs.add(row[12])
        for col,mod in [(5,'A1-A3'),(6,'C3'),(7,'C4'),(8,'D')]:
            v=row[col-1];value=numeric(v)
            if value is None:raise ValueError(f'Unexpected GWP in row {n}: {v!r}')
            observations.append(dict(id=f'{mid}:gwp:{mod}',material_id=mid,property='global_warming_potential',value=value,value_text=str(v),unit='kg CO2-eq/(m2 year)' if standard else 'kg CO2-eq',declared_unit='1 m2 year (heated floor area plus heated basement area)' if standard else str(row[8])+' '+str(row[9]),module=mod,source_id=xlsx['id'],source_locator=f'Sheet1!{openpyxl.utils.get_column_letter(col)}{n}',basis='BR18 reference factor; no lifecycle modules summed',conditions=conditions,data_status='reported'))
        mass=numeric(row[10])
        if mass is not None:
            prop='density' if row[11]=='kg/m³' else 'mass_factor'
            observations.append(dict(id=mid+':mass',material_id=mid,property=prop,value=mass,value_text=str(row[10]),unit=row[11],source_id=xlsx['id'],source_locator=f'Sheet1!K{n}:L{n}',conditions=conditions,data_status='reported'))
    # Download primary EPD documents linked by the official reference table.
    def pdf(url):
        name='references/'+hashlib.sha256(url.encode()).hexdigest()[:12]+'-'+urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/',1)[-1])
        try:return fetch(url,name,'Original EPD referenced by BR18 table 7')
        except Exception as exc:return {'url':url,'error':str(exc)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(pdf,sorted(refs)):
            if 'error' in result:failures.append(result)
            else:sources.append(result)
    # Table 8 provides explicit fuel/energy factors as two separate workbooks.
    for url in sorted(set(re.findall(r'href=[\"\']([^\"\']+\.xlsx)',(ROOT/pages[8]['local_path']).read_text()))):
        src=fetch(urllib.parse.urljoin(BASE,url),urllib.parse.urlsplit(url).path.rsplit('/',1)[-1]);sources.append(src)
    # Original table 8 energy and fuel factors, preserving each year or basis.
    for src in list(sources):
        if not src['local_path'].endswith('.xlsx') or '/tabel-8' not in src['local_path']:
            continue
        ws=openpyxl.load_workbook(ROOT/src['local_path'],data_only=False).active
        if 'tabel-81' in src['local_path']:
            for col in (2,3,4):
                name=ws.cell(2,col).value
                mid=f'br18:t81:col{col}'
                materials.append(dict(id=mid,name=name,kind='generic',category='energy',aliases=[],source_id=src['id'],source_locator=f'Ark1!{openpyxl.utils.get_column_letter(col)}2',description='Energy carrier emissions reference, not building material'))
                for ri in range(5,ws.max_row+1):
                    year=ws.cell(ri,1).value;v=ws.cell(ri,col).value
                    if not isinstance(year,int) or not (1900<year<2200):continue
                    if numeric(v) is None:raise ValueError(f'Unexpected energy factor at row {ri}')
                    observations.append(dict(id=f'{mid}:year{year}',material_id=mid,property='energy_supply_reference_gwp',value=numeric(v),value_text=str(v),unit=ws.cell(4,col).value,source_id=src['id'],source_locator=f'Ark1!{openpyxl.utils.get_column_letter(col)}{ri}',conditions={'year':year,'scope':'official energy supply reference factor; not material embodied carbon'},data_status='reported'))
        else:
            for ri in range(3,ws.max_row+1):
                name=ws.cell(ri,1).value
                if not isinstance(name,str) or numeric(ws.cell(ri,2).value) is None:continue
                mid=f'br18:t82:row{ri}'
                materials.append(dict(id=mid,name=name.strip(),kind='generic',category='energy',aliases=[],source_id=src['id'],source_locator=f'Ark1!A{ri}:E{ri}',description='Fuel emissions factor, not building material'))
                for col in (2,4):
                    v=ws.cell(ri,col).value
                    if numeric(v) is None:continue
                    observations.append(dict(id=f'{mid}:col{col}',material_id=mid,property='fuel_reference_gwp',value=numeric(v),value_text=str(v),unit=ws.cell(ri,col+1).value,source_id=src['id'],source_locator=f'Ark1!{openpyxl.utils.get_column_letter(col)}{ri}',conditions={'scope':'official fuel emissions reference factor'},data_status='reported'))

    # Original HTML tables 9, 10, 11: parse cells and keep row/header context.
    for n in (9,10,11):
        parser=Tables();parser.feed((ROOT/pages[n]['local_path']).read_text())
        for ti,table in enumerate(parser.tables,1):
            if not table:continue
            for ri,row in enumerate(table[1:],2):
                if not row:continue
                vi=next((i for i in range(len(row)-1,-1,-1) if numeric(row[i]) is not None),None)
                if vi is None:continue
                value=numeric(row[vi]);mid=f'br18:t{n}:table{ti}:row{ri}'
                name=' — '.join(row[:vi]);unit=(row[vi+1] if len(row)>vi+1 else 'kgCO2e/kg' if n==10 and ti==1 else 'kgCO2e/(m2 year)' if n==10 else 'kg CO2/kg')
                materials.append(dict(id=mid,name=name,kind='assembly' if n==9 or (n==10 and ti>1) else 'generic',category=category(name),aliases=[],source_id=pages[n]['id'],source_locator=f'HTML table[{ti}]/tr[{ri}]',description='Official process/construction reference factor, not a product EPD'))
                module='A4' if n==10 and ti==1 else row[0] if n==10 and ti>1 else None
                prop={9:'construction_reference_gwp',10:'transport_reference_gwp',11:'waste_treatment_reference_gwp'}[n]
                observations.append(dict(id=mid+':gwp',material_id=mid,property=prop,value=value,value_text=row[vi],unit=unit,module=module,source_id=pages[n]['id'],source_locator=f'HTML table[{ti}]/tr[{ri}]/td[{vi+1}]',conditions={'headers':table[0],'row':row,'scope':'official reference process factor'},data_status='reported'))
    for name,records in [('sources',sources),('materials',materials),('observations',observations)]:
        with (STAGE/(name+'.jsonl')).open('w') as out:
            for record in records:out.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
    summary=dict(dataset='br18',sources=len(sources),materials=len(materials),observations=len(observations),primary_epd_links=len(refs),failed_downloads=failures,coverage='All 507 reference records of table 7 including standard installations; all numeric rows of HTML tables 9–11; all numeric annual energy-supply and fuel factors in original Excel tables 8.1 and 8.2',limitations=['Original table 7 repeats some sorting IDs; row-specific IDs preserve all records without merging','Categories are heuristic, not authoritative classification','Reference tables are snapshots, not a legal compliance engine','Source rights not inferred; table and underlying EPD rights remain distinct','Installation factors per building area/year are not product EPD values'])
    (STAGE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
