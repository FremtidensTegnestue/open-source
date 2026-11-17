#!/usr/bin/env python3
"""Archive the public Vandkunsten open-source site and its directly linked files.

Original downloads are never executed. External websites are recorded as references;
direct documents and GitHub repository snapshots are downloaded separately.
"""
import concurrent.futures, datetime, hashlib, json, pathlib, re, shutil, time
import urllib.request, urllib.parse
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
BASE = 'https://opensource.vandkunsten.com/'
HOST = urllib.parse.urlsplit(BASE).netloc

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.text=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag in ('script','style'): self.hidden+=1
        for key in ('href','src'):
            if a.get(key): self.links.append(a[key])
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
        if tag in ('p','h1','h2','h3','h5','li','div','br'): self.text.append('\n')
    def handle_data(self, data):
        if not self.hidden: self.text.append(data)

def local_path(url):
    u=urllib.parse.urlsplit(url)
    bits=[p for p in urllib.parse.unquote(u.path).split('/') if p and p not in ('.','..')]
    if not bits or u.path.endswith('/'): bits.append('index.html')
    return pathlib.Path('archive') / u.netloc / pathlib.Path(*bits)

def fetch(url):
    rel=local_path(url); dest=ROOT/rel; dest.parent.mkdir(parents=True,exist_ok=True)
    record={'url':url,'path':str(rel),'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    tmp=dest.with_name(dest.name+'.part')
    for attempt in range(3):
        try:
            u=urllib.parse.urlsplit(url)
            request_url=urllib.parse.urlunsplit((u.scheme,u.netloc,urllib.parse.quote(u.path,safe='/%:@'),u.query,''))
            req=urllib.request.Request(request_url,headers={'User-Agent':'FremtidensTegnestue-ResearchArchive/1.0'})
            with urllib.request.urlopen(req,timeout=90) as response, tmp.open('wb') as out:
                record.update(status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type',''))
                shutil.copyfileobj(response,out)
            tmp.replace(dest)
            sha=hashlib.sha256()
            with dest.open('rb') as inp:
                for chunk in iter(lambda:inp.read(1024*1024),b''): sha.update(chunk)
            record.update(bytes=dest.stat().st_size,sha256=sha.hexdigest())
            print(json.dumps({'url':url,'bytes':record['bytes']},ensure_ascii=False),flush=True)
            return record
        except Exception as e:
            if attempt<2: time.sleep(1+attempt)
            else:
                tmp.unlink(missing_ok=True); record.update(status='error',error=str(e))
                print(json.dumps(record,ensure_ascii=False),flush=True)
    return record

def main():
    cachepath=ROOT/'catalog/downloads.json'
    cache={r['url']:r for r in json.loads(cachepath.read_text())} if cachepath.exists() else {}
    def cached_fetch(url):
        old=cache.get(url)
        return old if old and old['status']==200 and (ROOT/old['path']).exists() else fetch(url)
    pending={BASE}; seen=set(); records=[]; external=set(); repos=set()
    while pending:
        batch=sorted(pending-seen); pending=set()
        if not batch: break
        seen.update(batch)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(cached_fetch,batch))
        records.extend(results)
        for r in results:
            if r['status']=='error': continue
            path=ROOT/r['path']; typ=r['content_type']
            links=[]
            if urllib.parse.urlsplit(r['url']).netloc!=HOST: continue
            if 'text/html' in typ:
                parser=Page(); parser.feed(path.read_text(errors='replace')); links=parser.links
                textpath=ROOT/'extracted'/path.relative_to(ROOT/'archive')
                textpath=textpath.with_suffix('.txt'); textpath.parent.mkdir(parents=True,exist_ok=True)
                textpath.write_text(re.sub(r'\n[ \t]*\n+', '\n\n',''.join(parser.text)).strip()+'\n')
            elif 'text/css' in typ:
                links=re.findall(r'url\([\'\"]?([^\)\'\"]+)',path.read_text(errors='replace'))
            for link in links:
                url=urllib.parse.urldefrag(urllib.parse.urljoin(r['url'],link))[0]
                u=urllib.parse.urlsplit(url)
                if u.scheme not in ('http','https'): continue
                if u.netloc==HOST:
                    url=urllib.parse.urlunsplit(('https',u.netloc,u.path,u.query,''))
                    if url not in seen: pending.add(url)
                else:
                    external.add(url)
                    if re.search(r'\.(pdf|zip|xlsx?|xlsm|dyn|gh|rvt|ifc|mp4|webm)(?:$|\?)',url,re.I):
                        if url not in seen: pending.add(url)
                    if u.netloc=='github.com':
                        parts=u.path.strip('/').split('/')
                        if len(parts)>=2: repos.add('/'.join(parts[:2]))
        (ROOT/'catalog').mkdir(exist_ok=True)
        (ROOT/'catalog/downloads.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'catalog/external-links.json').write_text(json.dumps(sorted(external),ensure_ascii=False,indent=2)+'\n')
    (ROOT/'catalog/github-repositories.json').write_text(json.dumps(sorted(repos),indent=2)+'\n')
    print(json.dumps({'files':len(records),'errors':sum(r['status']=='error' for r in records),'repositories':sorted(repos)}),flush=True)

if __name__=='__main__': main()
