"""Local budget scenarios using pricing.py. Binds only loopback; source project stays unchanged."""
import argparse
import copy
from datetime import date
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import parse_qs

import pricing


def summary_html(reference, report):
    def fmt(value):
        return 'Uafklaret' if value is None else f'{pricing.Decimal(str(value)):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')+' kr.'
    c=report.get('comparison',pricing.compare_reports(reference,report))
    budget='Ikke fastlagt' if report['budget'] is None else fmt(report['budget']['amount_excl_vat'])
    values=[('Reference, kendt delsum',fmt(reference['known_subtotal_excl_vat'])),('Variant, kendt delsum',fmt(report['known_subtotal_excl_vat'])),('Samlet ændring',fmt(c['whole_forecast_delta_excl_vat'])),('Budgetramme',budget)]
    cards=''.join('<div class="card">'+html.escape(label)+'<strong>'+html.escape(value)+'</strong></div>' for label,value in values)
    note=f"Nye prissatte poster: {len(c['newly_priced'])}. Manglende poster er ikke nul. Alle beløb ekskl. moms."
    return '<div class="cards">'+cards+'</div><p><small>'+note+'</small></p>'


class BudgetEditor:
    def __init__(self, project_path, store_path, variant_path, as_of, allow_test=False):
        self.project_path, self.store_path, self.variant_path = map(Path, (project_path, store_path, variant_path))
        if self.variant_path.resolve() in (self.project_path.resolve(), self.store_path.resolve()):
            raise ValueError('En variant må ikke overskrive reference eller prislager')
        self.as_of, self.allow_test = as_of, allow_test
        self.project = json.loads(self.project_path.read_text())
        self.store = json.loads(self.store_path.read_text())
        self.reference_path=self.project_path
        if self.project.get('_scenario'):
            saved=self.project['_scenario'];self.reference_path=Path(saved['reference_file'])
            if pricing.digest(self.reference_path.read_bytes()) != saved['reference_sha256']:
                raise ValueError('Den gemte variants reference har ændret sig')
        reference_project=json.loads(self.reference_path.read_text())
        self.reference = pricing.assess(reference_project, self.store, as_of, allow_test)
        self.initial_report = pricing.assess(self.project, self.store, as_of, allow_test)
        self.initial_report['comparison']=pricing.compare_reports(self.reference,self.initial_report)
        self.token = secrets.token_urlsafe(24)
        paths = [self.project_path, self.reference_path, self.store_path, Path(__file__), Path(pricing.__file__)]
        paths += [Path(x['original']) for x in self.store['imports']]
        self.hashes = {p.resolve(): pricing.digest(p.read_bytes()) for p in paths}
        for name, expected in self.project.get('_bound_files', {}).items():
            p=Path(name).resolve()
            if pricing.digest(p.read_bytes()) != expected: raise ValueError('Projektets model-/beregningsgrundlag er forældet')
            self.hashes[p]=expected

    def current(self):
        if any(pricing.digest(p.read_bytes()) != h for p, h in self.hashes.items()):
            raise ValueError('Grundlaget har ændret sig. Genstart budgetvisningen før en ny beregning.')

    def evaluate(self, fields, save=False):
        self.current()
        variant = copy.deepcopy(self.project)
        allowed = set()
        for i, item in enumerate(variant.get('labor', [])):
            for key in ('hours', 'hourly_rate', 'employer_addon_percent', 'rate_basis'):
                name = f'l{i}_{key}';allowed.add(name)
                if name in fields:
                    value = fields[name]
                    item[key] = value if key == 'rate_basis' else (None if value.strip() == '' else str(pricing.number(value)))
            if item != self.project['labor'][i]:
                item['reference'] = 'Budgetvariant: brugerens time-/prisforudsætning; ikke et leverandørtilbud'
        for i, item in enumerate(variant['lines']):
            name = f'm{i}';allowed.add(name)
            if name in fields:
                options = self.initial_report['lines'][i]['options']
                if fields[name] == '':
                    item['selection'] = None
                else:
                    index = int(fields[name])
                    if index < 0 or index >= len(options):
                        raise ValueError('Ukendt leverandørvalg')
                    option = options[index]
                    item['selection'] = {k:option[k] for k in ('supplier_id', 'account_id', 'sku')}
        if set(fields) - allowed:
            raise ValueError('Ukendt budgetfelt')
        report = pricing.assess(variant, self.store, self.as_of, self.allow_test)
        report['comparison'] = pricing.compare_reports(self.reference, report)
        if save:
            variant['_scenario'] = {'reference_sha256':self.hashes[self.reference_path.resolve()],
                                    'reference_file':str(self.reference_path.resolve()),
                                    'note':'Særskilt budgetvariant; hverken fast budgetramme eller model er ændret.'}
            pricing.write_report(variant, self.variant_path, protected_paths=list(self.hashes))
        return variant, report

    def page(self):
        self.current()
        e = lambda v: html.escape(str(v), quote=True)
        labor_rows = []
        labels = {'contractor_rate':'Faktureret timepris ekskl. moms', 'employer_cost':'Samlet lønomkostning', 'gross_wage':'Bruttotimeløn + tillæg'}
        for i, item in enumerate(self.project.get('labor', [])):
            cells = []
            for key in ('hours', 'hourly_rate', 'employer_addon_percent'):
                value = '' if item.get(key) is None else item[key]
                cells.append(f'<td data-label="{e(dict(hours="Persontimer",hourly_rate="Kr. pr. time",employer_addon_percent="Tillæg ved bruttoløn %")[key])}"><input aria-label="{e(item["label"])} {key}" name="l{i}_{key}" type="number" min="0" step="any" value="{e(value)}"></td>')
            options = ''.join(f'<option value="{k}" {"selected" if item["rate_basis"]==k else ""}>{v}</option>' for k,v in labels.items())
            labor_rows.append(f'<tr class="labor-row" data-work="{i}" {"hidden" if i else ""}><td>{e(item["label"])}<br><small>Persontimer, ikke holdets kalendertimer</small></td>{cells[0]}{cells[1]}<td data-label="Prisgrundlag"><select name="l{i}_rate_basis">{options}</select></td>{cells[2]}</tr>')
        selections = []
        for i, row in enumerate(self.initial_report['lines']):
            if not row['options']:
                continue
            options = ['<option value="">Ikke valgt</option>']
            for j, option in enumerate(row['options']):
                chosen = row['selected'] and option['offer_id'] == row['selected']['offer_id']
                options.append(f'<option value="{j}" {"selected" if chosen else ""}>{e(option["supplier_name"])} · {e(option["sku"])} · {e(option["goods_excl_vat"])} kr. varebeløb</option>')
            selections.append(f'<label>{e(row["label"])}<select name="m{i}">{"".join(options)}</select></label>')
        frame = e(pricing.render(self.initial_report))
        work_options=''.join(f'<option value="{i}">{e(x["label"])}</option>' for i,x in enumerate(self.project.get('labor',[])))
        summary=summary_html(self.reference,self.initial_report)
        return f'''<!doctype html><html lang="da"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Juster budgetvariant</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#f6f4ef;color:#25382f}}main{{max-width:1300px;margin:auto;padding:24px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;text-align:left}}input{{width:110px}}select{{max-width:100%}}input,select{{box-sizing:border-box}}tr[hidden]{{display:none!important}}.cards{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}.card{{padding:12px;background:white;border-radius:6px;font-size:13px}}strong{{display:block;font-size:21px}}@media(max-width:700px){{#budget table,#budget tbody{{display:block}}#budget tr:first-child:not(.labor-row){{display:none}}#budget .labor-row{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}}#budget td{{display:block;padding:0;min-width:0}}#budget td:first-child{{grid-column:1/-1}}#budget td[data-label]:before{{content:attr(data-label);display:block;font-size:12px}}#budget td:nth-child(4){{grid-column:1/-1}}#budget input,#budget select{{width:100%}}}}input,select,button{{font:inherit;padding:8px;border:1px solid #aebcb3;border-radius:5px}}label{{display:block;margin:12px 0}}button{{background:#244f40;color:white;cursor:pointer}}#status{{min-height:24px}}iframe{{width:100%;height:900px;border:1px solid #ddd;background:white}}small{{font-size:12px}}.scroll{{overflow:auto}}</style><main><h1>Afprøv budgetvalg</h1><p>Justér timer, prisgrundlag eller leverandør og se resultatet mod referencen. Alle beløb er ekskl. moms. Tomme felter betyder uafklaret. Den faste budgetramme og modellen bevares.</p><p>To personer i fire timer er otte persontimer. Bruttotimeløn kræver særskilt afstemt tillæg til arbejdsgiveromkostninger; faktureret timepris indeholder allerede leverandørens prisopbygning.</p><div id="summary" aria-live="polite">{summary}</div><form id="budget"><h2>Arbejde</h2><label>Vælg arbejdspost<select id="workchoice">{work_options}</select></label><div class="scroll"><table><tr><th>Arbejdspost</th><th>Persontimer</th><th>Kr. pr. time</th><th>Prisgrundlag</th><th>Arbejdsgivertillæg % ved bruttoløn</th></tr>{''.join(labor_rows)}</table></div><h2>Leverandørvalg</h2>{''.join(selections)}<button type="submit">Beregn variant</button> <button type="button" id="save">Gem særskilt variant</button> <button type="reset">Fortryd ændringer</button></form><p id="status" role="status">Referencen er gemt uændret.</p><details><summary>Se hele beregningen og leverandørsammenligningen</summary><iframe id="result" title="Budgetberegning" sandbox="" srcdoc="{frame}"></iframe></details><p>Arbejdstimer giver ikke i sig selv en CO₂faktor. Materialer, byggepladsenergi, transport og øvrige følgeposter skal afstemmes ved ændret løsning. En gemt variant aktiveres ikke som projektets budget eller materiale-/klimavalg.</p></main><script>const form=document.querySelector('#budget'),status=document.querySelector('#status'),frame=document.querySelector('#result');let timer,revision=0;document.querySelector('#workchoice').addEventListener('change',event=>{{document.querySelectorAll('.labor-row').forEach(row=>row.hidden=row.dataset.work!==event.target.value)}});async function calculate(save=false){{const rev=++revision;frame.style.opacity='.5';status.textContent='Beregner…';try{{const response=await fetch(location.pathname+(save?'/save':'/preview'),{{method:'POST',body:new URLSearchParams(new FormData(form))}});const data=await response.json();if(rev!==revision)return;if(!response.ok)throw Error(data.error);frame.srcdoc=data.html;document.querySelector('#summary').innerHTML=data.summary;frame.style.opacity='1';status.textContent=save?'Varianten er gemt særskilt. Referencen er uændret.':'Varianten er beregnet. Referencen er uændret.'}}catch(err){{if(rev===revision){{frame.srcdoc='<p>Visningen er forældet. Ret input eller genstart.</p>';status.textContent=err.message}}}}}}form.addEventListener('submit',event=>{{event.preventDefault();clearTimeout(timer);calculate()}});form.addEventListener('input',()=>{{clearTimeout(timer);frame.style.opacity='.5';status.textContent='Input ændret — afventer beregning…';timer=setTimeout(()=>calculate(),500)}});form.addEventListener('reset',()=>{{clearTimeout(timer);setTimeout(()=>{{document.querySelector('#workchoice').dispatchEvent(new Event('change'));calculate()}},0)}});document.querySelector('#save').addEventListener('click',()=>{{clearTimeout(timer);calculate(true)}});</script></html>'''


def server_for(editor, port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, data, kind='application/json'):
            raw = data.encode() if isinstance(data, str) else json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind+'; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Frame-Options','SAMEORIGIN')
            self.end_headers();self.wfile.write(raw)

        def allowed(self):
            expected = f'127.0.0.1:{self.server.server_port}'
            return self.headers.get('Host') == expected and self.headers.get('Origin') in (None, 'http://'+expected)

        def do_GET(self):
            if not self.allowed() or self.path != '/'+editor.token:
                return self.reply(403,{'error':'Adgang afvist'})
            try:self.reply(200,editor.page(),'text/html')
            except (ValueError,OSError) as exc:self.reply(409,{'error':str(exc)})

        def do_POST(self):
            if not self.allowed() or self.path not in ('/'+editor.token+'/preview','/'+editor.token+'/save'):
                return self.reply(403,{'error':'Adgang afvist'})
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 65536 or not self.headers.get('Content-Type','').startswith('application/x-www-form-urlencoded'):
                    raise ValueError('Ugyldig formular')
                fields = parse_qs(self.rfile.read(length).decode(),keep_blank_values=True)
                if any(len(v)!=1 for v in fields.values()):raise ValueError('Dubleret felt')
                _, report = editor.evaluate({k:v[0] for k,v in fields.items()}, self.path.endswith('/save'))
                self.reply(200,{'html':pricing.render(report),'summary':summary_html(editor.reference,report),'comparison':report['comparison']})
            except (ValueError,KeyError,OSError) as exc:self.reply(400,{'error':str(exc)})
    return HTTPServer(('127.0.0.1',port),Handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--variant',type=Path,required=True)
    parser.add_argument('--as-of',type=pricing.iso_day,required=True)
    parser.add_argument('--allow-test-data',action='store_true')
    args=parser.parse_args()
    editor=BudgetEditor(args.project,args.store,args.variant,args.as_of,args.allow_test_data)
    server=server_for(editor)
    print(f'http://127.0.0.1:{server.server_port}/{editor.token}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
