"""Reusable, bounded beam comparisons. Physical screening, never a building design approval."""
import argparse
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess

import pricing
import report_io

MODULES = ('A1-A3', 'C3', 'C4', 'D')
GAPS = [
    'Styrke, lastkombinationer, krybning og produktvalg er ikke eftervist.',
    'Kipning, rumlig afstivning, samlinger, anlæg og fundering er åbne.',
    'Brand, fugt, vibrationer og øvrige relevante funktioner kræver egne kontroller.',
    'Følgekomponenter, transport, spild, montage og øvrig livscyklus er ikke beregnet.',
    'Priser gælder kun netto bjælkemateriale; indkøb, levering og arbejde er åbne.',
]


def write(path, value):
    report_io.write_report(value, path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError('Inputfelter passer ikke til denne afgrænsede bjælkeopskrift')


def positive(value, name, minimum=0, maximum=1e9):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum < value <= maximum:
        raise ValueError('Ugyldigt tal: '+name)


def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError('Angiv et læsbart grundlag eller en reference')


def validate(s):
    fields(s, 'schema project_id title model_revision basis_reference span_mm external_line_load_N_mm load_reference include_self_weight material limits sensitivity candidates reference_candidate')
    if type(s['schema']) is not int or s['schema'] != 1:
        raise ValueError('Ukendt inputversion')
    for key in ('project_id', 'title', 'model_revision', 'basis_reference', 'load_reference'):
        text(s[key])
    positive(s['span_mm'], 'spænd', maximum=20000)
    positive(s['external_line_load_N_mm'], 'nedadrettet linjelast', minimum=-1e-20, maximum=1000)
    if s['external_line_load_N_mm'] < 0:raise ValueError('Linjelasten må ikke være negativ')
    if type(s['include_self_weight']) is not bool:
        raise ValueError('Egenvægt skal vælges udtrykkeligt')
    if not s['include_self_weight'] and s['external_line_load_N_mm'] == 0:
        raise ValueError('Denne opskrift kræver en positiv nedadrettet last')
    m = s['material']
    fields(m, 'E0_MPa E90_MPa G_MPa density_kg_m3 poisson reference')
    for key in ('E0_MPa', 'E90_MPa', 'G_MPa', 'density_kg_m3'):
        positive(m[key], key)
    positive(m['poisson'], 'Poisson-antagelse', minimum=-1e-20, maximum=.45)
    if m['poisson'] < 0:raise ValueError('Poisson-antagelsen skal være mindst nul i denne opskrift')
    text(m['reference'])
    fields(s['limits'], 'deflection_mm max_height_mm reference')
    for key in ('deflection_mm', 'max_height_mm'):
        if s['limits'][key] is not None:
            positive(s['limits'][key], key)
            text(s['limits']['reference'])
    fields(s['sensitivity'], 'stiffness_factor reference')
    positive(s['sensitivity']['stiffness_factor'], 'stivhedsfaktor', maximum=1)
    text(s['sensitivity']['reference'])
    if not isinstance(s['candidates'], list) or not 1 <= len(s['candidates']) <= 12:
        raise ValueError('Vælg 1–12 kandidater')
    ids = set()
    for c in s['candidates']:
        fields(c, 'id label width_mm height_mm price')
        if not isinstance(c['id'], str) or not re.fullmatch('[a-z0-9_-]{1,40}', c['id']) or c['id'] in ids:
            raise ValueError('Kandidat-ID skal være sikkert og entydigt')
        ids.add(c['id']); text(c['label'])
        for key in ('width_mm', 'height_mm'):
            positive(c[key], key, maximum=2000)
        if s['span_mm']/c['height_mm'] < 8:
            raise ValueError('Referencekontrollen er afgrænset til spænd/højde mindst 8')
        if c['price'] is not None:
            fields(c['price'], 'amount_excl_vat_per_m section_mm observed_on reference')
            pricing.number(c['price']['amount_excl_vat_per_m'])
            pricing.iso_day(c['price']['observed_on']); text(c['price']['reference'])
            if not isinstance(c['price']['section_mm'], list) or len(c['price']['section_mm']) != 2:
                raise ValueError('Prisens tværsnit mangler')
            for value in c['price']['section_mm']:
                positive(value, 'prisens tværsnit')
    if s['reference_candidate'] not in ids:
        raise ValueError('Referencekandidaten mangler')
    return s


def mechanical(s, c, factor=1):
    b, h, L = c['width_mm'], c['height_mm'], s['span_mm']
    m = s['material']; A = b*h; I = b*h**3/12
    volume = A*L/1e9
    mass = volume*m['density_kg_m3']
    own = A/1e6*m['density_kg_m3']*9.81/1000 if s['include_self_weight'] else 0
    q = s['external_line_load_N_mm']+own
    bending = 5*q*L**4/(384*m['E0_MPa']*factor*I)
    shear = q*L**2/(8*(5/6)*m['G_MPa']*factor*A)
    return {'length_m':L/1000, 'volume_m3':volume, 'structural_mass_kg':mass,
            'own_line_load_N_mm':own, 'total_line_load_N_mm':q,
            'beam_theory_mm':bending+shear, 'reaction_N':q*L/2,
            'gross_bending_stress_MPa':q*L**2/(8*(b*h*h/6))}


def recipe(s, c, factor, nx, ny, folder):
    """Reuse the checked XY quad8 approach: grain X, vertical Y, width is plane-stress thickness."""
    b,h,L = c['width_mm'],c['height_mm'],s['span_mm']; m=s['material']
    commands=[];nodes={};elements=[]
    def add(command, **params):commands.append({'command':command,'params':params})
    def node(x,y):
        key=(round(x,8),round(y,8))
        if key not in nodes:
            nodes[key]=len(nodes)+1;add('mesh.node.add',label=nodes[key],xyz=[x,y,0])
        return nodes[key]
    add('model.units',system='mm-t-s-N-MPa')
    for i in range(nx):
        for j in range(ny):
            x0,x1=L*i/nx,L*(i+1)/nx;y0,y1=h*j/ny,h*(j+1)/ny
            coords=[(x0,y0),(x1,y0),(x1,y1),(x0,y1),((x0+x1)/2,y0),(x1,(y0+y1)/2),((x0+x1)/2,y1),(x0,(y0+y1)/2)]
            elements.append(len(elements)+1)
            add('mesh.element.add',label=elements[-1],kind='quad8',nodes=[node(x,y) for x,y in coords])
    add('model.set.create',name='All',nodes=list(nodes.values()),elements=elements)
    for x,name in [(0,'Left'),(L,'Right')]:
        add('model.set.create',name=name,nodes=[n for (xx,yy),n in nodes.items() if abs(xx-x)<1e-6])
        add('model.boundary_condition.create',name=name,type='displacement',target={'set':name},values=[None,0,None,None,None,None])
    add('model.set.create',name='Anchor',nodes=[nodes[(0,round(h/2,8))]])
    add('model.boundary_condition.create',name='Datum',type='displacement',target={'set':'Anchor'},values=[0,None,None,None,None,None])
    add('model.material.create',name='DirectionalReference',elastic={'type':'engineering_constants',
        'young':[m['E0_MPa']*factor,m['E90_MPa']*factor,m['E90_MPa']*factor],
        'poisson':[m['poisson']]*3,'shear':[m['G_MPa']*factor,m['G_MPa']*factor,m['G_MPa']*factor/10]},density=m['density_kg_m3']*1e-12)
    add('model.section.create',name='Section',set='All',material='DirectionalReference',kind={'type':'plane_stress','thickness':b})
    add('model.load.create',name='Uniform',type='body_force',set='All',vector=[0,-mechanical(s,c,factor)['total_line_load_N_mm']/(b*h),0])
    add('model.step.create',name='Screening',procedure={'type':'static'},boundary_conditions=['Left','Right','Datum'],loads=['Uniform'])
    add('model.check');add('solve.static',step='Screening',threads=1,max_dofs=40000)
    add('results.export.csv',what='probe',path=str(folder/'nodes.csv'),step='Screening',set='All')
    add('results.export.csv',what='reactions',path=str(folder/'reactions.csv'),step='Screening',sets=['Left','Right','Anchor'])
    add('file.save_as',path=str(folder/'model.fieldcraft'))
    return commands, nodes[(round(L/2,8),round(h/2,8))]


def parse_analysis(folder, s, c, factor, mid):
    with (folder/'nodes.csv').open() as f:rows=list(csv.DictReader(f))
    with (folder/'reactions.csv').open() as f:rr={r['set']:r for r in csv.DictReader(f)}
    values=[float(r['uy [mm]']) for r in rows]
    if not all(math.isfinite(v) for v in values):raise ValueError('Ugyldigt native resultat')
    reference=mechanical(s,c,factor);q=reference['total_line_load_N_mm'];L=s['span_mm']
    # Native total uses unique nodes: Anchor also belongs to Left, so do not sum these sets.
    if abs(float(rr['total']['fy [N]'])-q*L)>max(.001,q*L*1e-7):raise ValueError('Ligevægt fejler')
    for side in ('Left','Right'):
        if abs(float(rr[side]['fy [N]'])-q*L/2)>max(.001,q*L*1e-7):raise ValueError('Reaktionsfordeling fejler')
    if not math.isclose(max(float(r['x [mm]']) for r in rows),L,abs_tol=1e-6):raise ValueError('Forkert analyselængde')
    if not math.isclose(max(float(r['y [mm]']) for r in rows),c['height_mm'],abs_tol=1e-6):raise ValueError('Forkert analysehøjde')
    if abs(float(rr['total']['mz [N·mm]'])-q*L*L/2)>max(.01,q*L*L*1e-7):raise ValueError('Momentbalance fejler')
    u=-float(next(r for r in rows if int(r['node'])==mid)['uy [mm]'])
    error=u/reference['beam_theory_mm']-1
    if abs(error)>.01:raise ValueError('Afvigelse fra uafhængig bjælkereference over 1 %')
    return dict(reference,deflection_mm=u,theory_relative_error=error,left_reaction_N=float(rr['Left']['fy [N]']),right_reaction_N=float(rr['Right']['fy [N]']))


def call(args, output, cwd=None):
    result=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=180)
    output.with_suffix('.stdout.txt').write_text(result.stdout)
    output.with_suffix('.stderr.txt').write_text(result.stderr)
    if result.returncode:raise RuntimeError('Native kald fejlede; se '+str(output.with_suffix('.stderr.txt')))
    return result.stdout


def analyse(s,c,factor,folder,cli):
    results=[]
    for label,nx,ny in [('coarse',24,4),('fine',48,8)]:
        d=folder/label;d.mkdir(parents=True,exist_ok=True)
        commands,mid=recipe(s,c,factor,nx,ny,d);write(d/'script.json',commands)
        info=json.loads(call([cli,'run',d/'script.json'],d/'run'))
        if info['display_units']!='mm-t-s-N-MPa':raise ValueError('Forkerte native enheder')
        results.append(parse_analysis(d,s,c,factor,mid))
    change=results[1]['deflection_mm']/results[0]['deflection_mm']-1
    if abs(change)>.005:raise ValueError('Netfølsomhed over 0,5 %')
    return dict(results[1],mesh_relative_change=change)


def beam_price(s,c):
    p=c['price']
    if p is None:return {'net_material_excl_vat':None,'reason':'Pris og kilde er ikke oplyst'}
    if p['section_mm']!=[c['width_mm'],c['height_mm']]:
        return {'net_material_excl_vat':None,'reason':'Pris gælder et andet tværsnit; afstem igen'}
    raw={'supplier_id':'internal','supplier_name':'Eget overslag','account_id':s['project_id'],
         'sku':c['id'],'product_id':c['id'],'mapping_reference':p['reference'],'source_reference':p['reference'],
         'observed_on':p['observed_on'],'review_on':p['observed_on'],'currency':'DKK','unit':'m','kind':'estimate',
         'origin':'nyt','availability':'unknown','price_basis':'net','tax_basis':'excl_vat',
         'amount':str(p['amount_excl_vat_per_m']),'price_quantity':'1','purchase_step':'.000001','minimum_quantity':'0'}
    offer=pricing.normalize_offer(raw)
    purchase,cost=pricing.cost_for(offer,Decimal(str(s['span_mm']))/1000)
    return {'net_material_excl_vat':pricing.cash(cost),'net_length_m':str(purchase),
            'source_reference':p['reference'],'observed_on':p['observed_on'],'scope':'Kun netto bjælkemateriale, ikke samlet pris'}


def geometry(s, folder, cli):
    commands=[]
    for i,c in enumerate(s['candidates']):
        commands.append({'command':'solid.box','params':{'name':c['id'],'body_name':c['id'],
            'length':str(s['span_mm']),'width':str(c['width_mm']),'height':str(c['height_mm']),
            'corner':[0,i*1000,0]}})
    write(folder/'cad-script.json',{'commands':commands})
    call([cli,'run',folder/'cad-script.json','--save',folder/'kandidater.sc','--quiet'],folder/'cad-build')
    call([cli,'eval','--in',folder/'kandidater.sc','--json-out',folder/'cad-measured.json'],folder/'cad-eval')
    measured=json.loads((folder/'cad-measured.json').read_text())
    bodies={b['name']:b for b in measured['bodies']}
    if set(bodies)!={c['id'] for c in s['candidates']}:raise ValueError('Native CAD-inventar afviger')
    volumes={}
    for c in s['candidates']:
        b=bodies[c['id']];v=b['volume_mm3']/1e9
        if not b['closed'] or not math.isclose(v,mechanical(s,c)['volume_m3'],rel_tol=1e-8):
            raise ValueError('Native CAD-volumen matcher ikke beregningsgeometrien')
        volumes[c['id']]=v
    return volumes


def climate(volume,runtime,folder):
    e=runtime['engine'];source=runtime['climate_source'];values={};executions=[]
    requests={'mass':{'kind':'mass','material_id':source['material_id'],'density_observation_id':source['density_observation_id']}}
    for phase,oid in source['gwp_observations'].items():
        if oid is not None:requests[phase]={'kind':'climate','material_id':source['material_id'],'gwp_observation_id':oid}
    for name,req in requests.items():
        req['quantity']={'value':volume,'unit':'m3'};path=folder/('rust-'+name+'.json');write(path,req)
        value=json.loads(call([e['binary'],'--root',e['root'],'--store',e['store'],'--snapshot',e['snapshot'],'calculate',path],folder/('rust-'+name)))
        if value.get('status')!='ok' or value.get('snapshot')!=e['snapshot'] or not math.isfinite(value.get('value',float('nan'))):
            raise ValueError('Rust-resultat eller dataudgave afviger')
        observation=value['inputs']['density' if name=='mass' else 'source_observation']
        expected_id=source['density_observation_id'] if name=='mass' else source['gwp_observations'][name]
        if observation['id']!=expected_id or observation['material_id']!=source['material_id']:
            raise ValueError('Rust-svaret tilhører en anden materialekilde')
        if name=='mass':
            if observation['property_id']!='property:density' or value['unit']!='kg':
                raise ValueError('Forkert masse-/densitetsgrundlag')
        elif (observation['property_id']!='property:gwp_total' or observation['module']!=name
              or value['module']!=name or value['inputs']['declared_basis']['dimension']!='volume'):
            raise ValueError('Forkert GWP-modul/indikator eller kilde uden volumenbasis')
        values[name]=value['value'];executions.append({'request':req,'result':value})
    write(folder/'rust-executions.json',executions)
    modules={m:values.get(m) for m in MODULES}
    known=[modules[m] for m in MODULES[:3] if modules[m] is not None]
    return {'source_reference_mass_kg':values['mass'],'modules':modules,
            'known_subtotal_kgCO2e':sum(known) if known else None,
            'missing_modules':[m for m in MODULES if modules[m] is None],
            'snapshot':e['snapshot'],'source':source,'status':'partial_reference'}


def checks(s,c,base,sensitive):
    limit=s['limits']['deflection_mm'];height=s['limits']['max_height_mm']
    return {'baseline_deflection':None if limit is None else base['deflection_mm']<=limit,
            'sensitivity_deflection':None if limit is None else sensitive['deflection_mm']<=limit,
            'height_envelope':None if height is None else c['height_mm']<=height,
            'whole_design_verified':False,'unresolved':list(GAPS)}


def verify_runtime(r):
    fields(r,'fieldcraft_cli solidcraft_cli engine climate_source bound_files')
    for path,digest in r['bound_files'].items():
        if sha(path)!=digest:raise ValueError('Runtime/data er ændret: '+Path(path).name)
    required=[r['fieldcraft_cli'],r['solidcraft_cli'],r['engine']['binary'],str(Path(r['engine']['store'])/r['engine']['snapshot']/'manifest.json')]
    if any(str(Path(path).resolve()) not in r['bound_files'] for path in required):raise ValueError('Program eller manifest mangler versionsbinding')
    if r['engine']['snapshot']=='latest':raise ValueError('Fasthold en konkret dataudgave')
    if set(r['climate_source']['gwp_observations'])!=set(MODULES):raise ValueError('Angiv modulerne eksplicit; ukendt kan være null')
    text(r['climate_source']['reference'])


def render(report):
    esc=html.escape
    fmt=lambda v:'Ukendt' if v is None else f'{float(v):.2f}'.replace('.',',')
    state=lambda v:'Ukendt' if v is None else ('Inden for testkriteriet' if v else 'Overskrider testkriteriet')
    rows=[]
    for c in report['candidates']:
        rows.append(f"""<tr><td><b>{esc(c['label'])}</b><br>{fmt(c['width_mm'])} × {fmt(c['height_mm'])} mm<br>Højde: {esc(state(c['checks']['height_envelope']))}</td><td data-label="Mængde">{fmt(c['baseline']['length_m'])} m<br>{c['volume_m3']:.5f} m³ træ<br>{fmt(c['volume_delta_percent'])} % mod reference</td><td data-label="Basis · nedbøjning">{fmt(c['baseline']['deflection_mm'])} mm<br>{esc(state(c['checks']['baseline_deflection']))}</td><td data-label="Følsomhed · nedbøjning">{fmt(c['sensitivity']['deflection_mm'])} mm<br>{esc(state(c['checks']['sensitivity_deflection']))}</td><td data-label="Kendt klimadelsum">{fmt(c['climate']['known_subtotal_kgCO2e'])} kg CO₂e<br>Forskel: {fmt(c['known_climate_delta_kgCO2e'])} kg<br>D separat: {fmt(c['climate']['modules']['D'])}</td><td data-label="Netto materiale · ekskl. moms">{fmt(c['price']['net_material_excl_vat'])} kr.<br>Kun netto materiale</td></tr>""")
    details=esc(json.dumps(report['input'],ensure_ascii=False,indent=2))
    return f'''<!doctype html><html lang="da"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bjælke · sammenligning</title><style>body{{font:16px/1.5 system-ui;background:#f6f4ef;color:#263b32;margin:0}}main{{max-width:1250px;margin:auto;padding:28px}}h1{{font-size:34px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:16px;text-align:left;vertical-align:top;border-bottom:1px solid #ddd}}small{{color:#53665b}}.note{{background:#fff0ce;padding:18px}}.scroll{{overflow:auto}}pre{{white-space:pre-wrap}}a{{color:#235d5a}}@media(max-width:760px){{main{{padding:16px}}h1{{font-size:28px}}.scroll{{overflow:visible}}table{{background:transparent}}tr:first-child{{display:none}}tr{{display:grid;grid-template-columns:1fr 1fr;margin-bottom:16px;background:white;border:1px solid #ddd;border-radius:8px;overflow:hidden}}td{{padding:12px;font-size:14px;min-width:0;overflow-wrap:anywhere}}td:first-child{{grid-column:1/-1;font-size:16px}}td[data-label]:before{{content:attr(data-label);font-weight:650;display:block;margin-bottom:6px;color:#53665b}}}}</style><main><small>Gemt beregningsforløb · {esc(report['created_at'])}</small><h1>{esc(report['input']['title'])}</h1><p>Tre spørgsmål: Hvor meget materiale bruger vi? Hvordan bøjer bjælken? Hvor følsom er løsningen?</p><p class="note">Afgrænset fysisk undersøgelse. Ingen kandidat er samlet godkendt. Kriterierne er angivne projekt-/testvalg. Klimatallet er en kendt bjælkedelsum af de tilgængelige A1–A3/C3/C4-moduler; se kildegrundlag og mangler. D er separat.</p><div class="scroll"><table><tr><th>Valg</th><th>Mængde</th><th>Basis<br>Grænse {fmt(report['input']['limits']['deflection_mm'])} mm</th><th>Følsomhed</th><th>Kendt klima</th><th>Ekskl. moms</th></tr>{''.join(rows)}</table></div><p>{esc(report['input']['sensitivity']['reference'])}</p><p>Laveste træmængde blandt de undersøgte kandidater: <b>{esc(report['lowest_volume_candidate'])}</b>. Samlet teknisk valg: <b>Afventer</b>.</p><details><summary>Det mangler før et konstruktionsvalg</summary><ul>{''.join('<li>'+esc(g)+'</li>' for g in GAPS)}</ul></details><details><summary>Grundlag og kilder</summary><pre>{details}</pre><pre>{esc(json.dumps(report['candidates'][0]['climate']['source'],ensure_ascii=False,indent=2))}</pre><p>Statisk densitet styrer egenlast. Klimakildens masse er en særskilt kildereference og erstatter ikke egenlasten.</p></details><details><summary>Kontrol og genåbning</summary><p>Native CAD-volumen, ligevægt, bjælketeori og to net er kontrolleret. Gemte input, kode, programmer, datamanifest og resultatfiler er hashbundet. En ændring kræver genberegning; kontrollér med beam_study.py --check.</p></details><p><a href="kandidater.sc">Åbn de tre geometrier i SolidCraft</a> · <a href="resultat.json">Beregningsdata</a></p></main></html>'''


def run(study_path,runtime_path,out):
    s=validate(json.loads(study_path.read_text()));r=json.loads(runtime_path.read_text());verify_runtime(r)
    out=out.resolve()
    initial={str(p.resolve()):sha(p) for p in [study_path,runtime_path,Path(__file__),Path(pricing.__file__),Path(report_io.__file__)]}
    if out.exists() and any(out.iterdir()):
        old=json.loads((out/'status.json').read_text())
        if old.get('project_id')!=s['project_id']:raise ValueError('Mappen tilhører et andet forløb')
    out.mkdir(parents=True,exist_ok=True)
    write(out/'status.json',{'status':'running','project_id':s['project_id']})
    (out/'rapport.html').write_text('<meta charset="utf-8"><h1>Beregningen opdateres</h1><p>Tidligere resultater er ikke aktuelle.</p>')
    try:
        volumes=geometry(s,out,r['solidcraft_cli']);candidates=[]
        for c in s['candidates']:
            folder=out/c['id'];folder.mkdir(exist_ok=True)
            base=analyse(s,c,1,folder/'basis',r['fieldcraft_cli'])
            factor=s['sensitivity']['stiffness_factor']
            sensitive=analyse(s,c,factor,folder/'sensitivity',r['fieldcraft_cli'])
            if abs(sensitive['deflection_mm']*factor/base['deflection_mm']-1)>1e-6:
                raise ValueError('Lineær stivhedsfølsomhed fejler')
            candidates.append(dict(c,volume_m3=volumes[c['id']],baseline=base,sensitivity=sensitive,
                climate=climate(volumes[c['id']],r,folder),price=beam_price(s,c),checks=checks(s,c,base,sensitive)))
        reference=next(c for c in candidates if c['id']==s['reference_candidate'])
        for c in candidates:
            c['volume_delta_percent']=100*(c['volume_m3']/reference['volume_m3']-1)
            a,b=c['climate']['known_subtotal_kgCO2e'],reference['climate']['known_subtotal_kgCO2e']
            c['known_climate_delta_kgCO2e']=None if a is None or b is None else a-b
        verify_runtime(r)
        if any(sha(path)!=digest for path,digest in initial.items()):raise ValueError('Input/kode ændret under kørsel')
        paths=[study_path,runtime_path,Path(__file__),Path(pricing.__file__),Path(report_io.__file__)]+[Path(p) for p in r['bound_files']]
        paths += [p for p in out.rglob('*') if p.is_file() and p.name not in ('status.json','rapport.html','resultat.json')]
        report={'schema':1,'status':'partial_screening','created_at':datetime.now().astimezone().isoformat(),
                'input':s,'input_sha256':sha(study_path),'candidates':candidates,'winner':None,
                'lowest_volume_candidate':min(candidates,key=lambda c:c['volume_m3'])['label'],
                'bound_files':{str(p.resolve()):sha(p) for p in paths}}
        write(out/'resultat.json',report);(out/'rapport.html').write_text(render(report))
        write(out/'status.json',{'status':'partial_screening','project_id':s['project_id'],
            'result_sha256':sha(out/'resultat.json'),'html_sha256':sha(out/'rapport.html')})
        return report
    except Exception as e:
        write(out/'status.json',{'status':'failed','project_id':s['project_id'],'error':str(e)})
        (out/'rapport.html').write_text('<meta charset="utf-8"><h1>Beregningen fejlede</h1><p>'+html.escape(str(e))+'</p>')
        raise


def check(out):
    state=json.loads((out/'status.json').read_text());report=json.loads((out/'resultat.json').read_text())
    if state['status']!='partial_screening' or state['result_sha256']!=sha(out/'resultat.json') or state['html_sha256']!=sha(out/'rapport.html'):
        raise ValueError('Resultat eller sidste kørsel er ikke aktuelt')
    for path,digest in report['bound_files'].items():
        if sha(path)!=digest:raise ValueError('Grundlag ændret: '+Path(path).name)
    return {'current':True,'status':'partial_screening','whole_design_verified':False}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('study',type=Path,nargs='?');ap.add_argument('--runtime',type=Path)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    if a.check:print(json.dumps(check(a.out.resolve())))
    else:
        if a.study is None or a.runtime is None:ap.error('Angiv input og --runtime')
        result=run(a.study.resolve(),a.runtime.resolve(),a.out)
        print(json.dumps({'status':result['status'],'candidates':len(result['candidates']),'winner':None,'report':str(a.out/'rapport.html')}))
