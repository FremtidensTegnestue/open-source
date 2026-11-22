"""Small revision-bound work and review overview. Records work; never grants authority."""
import argparse
from datetime import date
import hashlib
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets

from report_io import write_report

GROUPS = {'work':'Vores næste arbejde', 'technical_review':'Afventer faglig kontrol',
          'formal_approval':'Afventer formel godkendelse / erklæring', 'clarify':'Afklar ansvar og krav'}
STATES = {'open':'Åben', 'prepared':'Underlag udarbejdet', 'completed':'Registreret afsluttet'}
ROUTES = {'us':'Eget arbejde', 'specialist':'Særskilt fagperson', 'undecided':'Udførende ikke afklaret'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context_key(s, item):
    values={key:item[key] for key in ('id','title','scope','work_by','responsible_role','requirement','basis')}
    values['project_id']=s['project_id']
    values['sources']={key:s['sources'][key]['sha256'] for key in item['sources']}
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def validate(s):
    if not isinstance(s,dict) or set(s)!={'schema','project_id','scope','sources','items'} or type(s['schema']) is not int or s['schema']!=1:
        raise ValueError('Ukendt format for arbejdsoversigten')
    def text(value):
        if not isinstance(value,str) or not value.strip() or len(value)>4000:raise ValueError('Tekst/grundlag mangler')
    text(s['project_id']);text(s['scope'])
    if not isinstance(s['sources'],dict) or not s['sources'] or not isinstance(s['items'],list) or not s['items']:raise ValueError('Kilder eller poster mangler')
    for key,source in s['sources'].items():
        text(key)
        if not isinstance(source,dict) or set(source)!={'path','sha256'}:raise ValueError('Ugyldig kildebinding')
        text(source['path'])
        if not isinstance(source['sha256'],str) or len(source['sha256'])!=64 or any(x not in '0123456789abcdef' for x in source['sha256']):
            raise ValueError('Kildens SHA256 mangler')
    ids=set()
    for item in s['items']:
        if not isinstance(item,dict) or set(item)!={'id','title','scope','work_by','responsible_role','requirement','state','basis','next_action','sources','completion'}:
            raise ValueError('Ugyldig arbejdspost')
        for key in ('id','title','scope','responsible_role','basis','next_action'):text(item[key])
        if item['id'] in ids:raise ValueError('Dubleret post-ID')
        ids.add(item['id'])
        if any(not isinstance(item[key],str) for key in ('work_by','requirement','state')) or item['work_by'] not in ROUTES or item['requirement'] not in GROUPS or item['state'] not in STATES:
            raise ValueError('Ukendt arbejds-/kontrolstatus')
        if not isinstance(item['sources'],list) or not item['sources'] or any(not isinstance(k,str) or k not in s['sources'] for k in item['sources']) or len(set(item['sources']))!=len(item['sources']):
            raise ValueError('Posten skal have kendte grundlagsbindinger')
        completion=item['completion']
        if item['state']=='completed':
            if not isinstance(completion,dict) or set(completion)!={'by','date','reference','context_key','evidence'}:
                raise ValueError('Afslutning kræver dokumenteret registrering')
            for key in ('by','reference','context_key'):text(completion[key])
            text(completion['date']);date.fromisoformat(completion['date'])
            if not isinstance(completion['evidence'],list) or not completion['evidence'] or any(not isinstance(k,str) or k not in item['sources'] for k in completion['evidence']):
                raise ValueError('Afslutningens bilag skal indgå i postens grundlag')
        elif completion is not None:raise ValueError('En åben post må ikke bære en skjult afslutning')
    return s


def view(path):
    path=Path(path).resolve();s=validate(json.loads(path.read_text()));sources={}
    for key,value in s['sources'].items():
        source=Path(value['path'])
        if not source.is_absolute():source=path.parent/source
        try:current=source.is_file() and sha(source)==value['sha256']
        except OSError:current=False
        sources[key]={'path':str(source.resolve()),'current':current}
    items=[]
    for item in s['items']:
        stale=any(not sources[k]['current'] for k in item['sources'])
        if item['state']=='completed' and item['completion']['context_key']!=context_key(s,item):stale=True
        derived='recheck' if stale else item['state']
        items.append(dict(item,derived_state=derived,
                          state_label='Grundlag ændret · genvurder' if stale else STATES[derived]))
    opened=[i for i in items if i['derived_state']!='completed']
    return {'schema':1,'project_id':s['project_id'],'scope':s['scope'],'sources':sources,'items':items,
            'counts':{key:sum(i['requirement']==key for i in opened) for key in GROUPS},
            'recorded_completions':len(items)-len(opened),'open_items':len(opened),
            'current':all(x['current'] for x in sources.values()) and not any(i['derived_state']=='recheck' for i in items),
            'note':'Registrerede afslutninger er kildebundne oplysninger. Programmet verificerer ikke personers kompetence, certificering eller en erklærings retlige gyldighed.'}


def state_key(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()


def render(v, live=False):
    e=html.escape;sections=[]
    for group,label in GROUPS.items():
        cards=[]
        for i in v['items']:
            if i['requirement']!=group or i['derived_state']=='completed':continue
            cards.append(f"<article class='{group}'><p class='tag'>{e(i['state_label'])} · {e(ROUTES[i['work_by']])}</p><h3>{e(i['title'])}</h3><p><b>Næste handling:</b> {e(i['next_action'])}</p><p><b>Ansvarlig rolle:</b> {e(i['responsible_role'])}</p><details><summary>Omfang og grundlag</summary><p>{e(i['scope'])}</p><p>{e(i['basis'])}</p><p>Grundlags-ID: {e(', '.join(i['sources']))}</p></details></article>")
        empty='Ingen konkrete erklæringskrav er registreret som afklarede. Se »Afklar ansvar og krav«.' if group=='formal_approval' else 'Ingen åbne poster i denne gruppe.'
        sections.append(f"<section id='{group}'><h2>{e(label)} · {v['counts'][group]}</h2>{''.join(cards) or '<p>'+empty+'</p>'}</section>")
    nav=''.join(f"<a class='{group}' href='#{group}'>{e(label)} · {v['counts'][group]}</a>" for group,label in GROUPS.items())
    completed=''.join(f"<li><b>{e(i['title'])}</b> — {e(i['scope'])}<br>{e(i['completion']['by'])}, {e(i['completion']['date'])}: {e(i['completion']['reference'])}</li>" for i in v['items'] if i['derived_state']=='completed')
    warning='Grundlaget matcher de registrerede kilder' if v['current'] else 'Grundlag er ændret eller mangler · berørte poster skal genvurderes'
    source_list=''.join(f"<li><b>{e(key)}</b> · {'matcher' if source['current'] else 'ændret/mangler'}<br>{e(source['path'])}</li>" for key,source in v['sources'].items())
    # Only reload when the rendered content actually changes; preserve open details while reading.
    poll=("<script>const key="+json.dumps(state_key(v))+";const notice=document.querySelector('.notice');const original=notice.textContent;async function check(){try{const r=await fetch(location.pathname+'/state',{cache:'no-store'});if(!r.ok)throw Error();const v=await r.json();if(key!==v.key){location.reload();return}notice.textContent=original;notice.style.background='';}catch(e){notice.textContent='Kontrol afbrudt eller ugyldig registrering — viste poster er ikke genkontrolleret. Genindlæs for at kontrollere fejlen.';notice.style.background='#ffd9d0';}}setInterval(check,2000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)check()});check();</script>") if live else ''
    return f'''<!doctype html><html lang="da"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Arbejde, mangler og godkendelser</title><style>body{{font:16px/1.5 system-ui;background:#f6f4ef;color:#243b32;margin:0}}main{{max-width:1000px;margin:auto;padding:24px;overflow-wrap:anywhere}}h1{{font-size:32px}}h2{{font-size:23px;margin-top:36px}}h3{{font-size:19px;margin:6px 0}}article{{background:white;border-left:5px solid #497a9a;padding:16px 20px;margin:12px 0;border-radius:4px}}article.technical_review{{border-color:#a86408}}article.formal_approval{{border-color:#ac4136}}article.clarify{{border-color:#8361a2}}.tag{{font-size:13px;color:#53675c;margin:0}}.notice{{background:#fff0ce;padding:16px}}.counter{{font-weight:700;font-size:20px}}details{{margin-top:12px}}nav{{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}}nav a{{color:inherit;background:white;border:1px solid #c9d2cc;border-left:5px solid #497a9a;padding:8px 12px;text-decoration:none}}nav .technical_review{{border-left-color:#a86408}}nav .formal_approval{{border-left-color:#ac4136}}nav .clarify{{border-left-color:#8361a2}}@media(max-width:600px){{main{{padding:16px}}article{{padding:14px}}h1{{font-size:27px}}}}</style><main><p>Projektets arbejds- og kontroloversigt</p><h1>Vi udfører selv det arbejde, vi kan og må</h1><p class="notice" role="status">{e(warning)}. Status er en arbejdsregistrering, ikke et samlet godkendelsesstempel.</p><p class="counter">{v['open_items']} åbne poster · {v['recorded_completions']} registrerede afslutninger</p><nav aria-label="Opgavetyper">{nav}</nav><details><summary>Omfang og arbejdsdeling</summary><p>{e(v['scope'])}</p><p>Uafklarede kompetence- eller myndighedskrav afklares konkret. De bliver ikke automatisk bestilt hos andre. Programkontrol og faglig/formel kontrol holdes adskilt.</p></details>{''.join(sections)}<details><summary>Registreret afsluttet for det angivne omfang · {v['recorded_completions']}</summary><ul>{completed or '<li>Ingen registrerede afslutninger.</li>'}</ul><p>{e(v['note'])}</p></details><details><summary>Bundne grundlagsfiler · {len(v['sources'])}</summary><ul>{source_list}</ul></details><p><small>{'Lokal visning genkontrollerer grundlag og registrering ca. hvert 2. sekund, mens forbindelsen er aktiv.' if live else 'Gemt oversigt. Kontrollér og gendan efter ændringer; denne fil genkontrollerer ikke sig selv.'}</small></p></main>{poll}</html>'''


def build(path,out):
    path=Path(path).resolve();out=Path(out).resolve()
    s=validate(json.loads(path.read_text()))
    protected=[path]+[(path.parent/Path(v['path'])).resolve() for v in s['sources'].values()]
    if out.suffix.casefold()!='.html':raise ValueError('Oversigten kræver en .html-fil')
    if out in protected or out.with_suffix('.json') in protected:raise ValueError('Bevar input og kilder')
    v=view(path);out.parent.mkdir(parents=True,exist_ok=True)
    write_report(v,out.with_suffix('.json'),protected_paths=protected)
    out.write_text(render(v),encoding='utf-8')
    return v


def serve(path):
    prefix='/'+secrets.token_urlsafe(20)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port):self.send_error(403);return
            try:
                v=view(path)
                key=state_key(v)
                if self.path==prefix:
                    body=render(v,live=True);kind='text/html'
                elif self.path==prefix+'/state':body=json.dumps({'key':key});kind='application/json'
                else:self.send_error(404);return
                raw=body.encode();self.send_response(200);self.send_header('Content-Type',kind+'; charset=utf-8')
                self.send_header('Cache-Control','no-store');self.send_header('X-Frame-Options','DENY')
                self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            except (ValueError,OSError,KeyError) as error:
                raw=('Oversigten skal afstemmes: '+str(error)).encode();self.send_response(409);self.end_headers();self.wfile.write(raw)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    print('http://127.0.0.1:'+str(server.server_port)+prefix,flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('registry',type=Path)
    ap.add_argument('--out',type=Path);ap.add_argument('--check',action='store_true');ap.add_argument('--serve',action='store_true');a=ap.parse_args()
    if a.serve:serve(a.registry.resolve())
    else:
        v=build(a.registry,a.out) if a.out else view(a.registry)
        print(json.dumps({key:v[key] for key in ('current','open_items','recorded_completions','counts')},ensure_ascii=False))
        if a.check and not v['current']:raise SystemExit(1)
