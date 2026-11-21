"""One parametric facade sample: native SolidCraft quantities, pinned Rust climate, Python prices.

No whole-building LCA or technical approval. The fixed display grid is not a product specification.
"""
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile

import pricing

NAMESPACE = 'com.fremtidenstegnestue.facade'
MATERIALS = {'timber': 'br18:t7:B1370:row12', 'plywood': 'br18:t7:B1496:row35',
             'windboard': 'br18:t7:D1531:row73', 'slate': 'br18:t7:G1128:row463',
             'steel': 'br18:t7:G0499:row287'}
MODULES = ('A1-A3', 'C3', 'C4', 'D')
PARAMS = {'Facade_bredde': (2400, 'mm'), 'Facade_hoejde': (2400, 'mm'),
          'Trae_tykkelse': (22, 'mm'), 'Krydsfiner_tykkelse': (22, 'mm'),
          'Beklaedning': (0, ''), 'Indkoebstillæg_procent': (5, ''),
          'Skifer_indkoebstillæg_procent': (10, ''),
          'Pris_skelet_m': (-1, ''), 'Pris_ventlaegte_m': (-1, ''),
          'Pris_krydsfiner_m2': (-1, ''), 'Pris_vindplade_m2': (-1, ''),
          'Pris_skifer_m2': (-1, ''), 'Pris_skiferlaegte_m': (-1, ''),
          'Pris_trae_m2': (-1, ''), 'Pris_skruer_stk': (-1, ''),
          'Pris_trae_gaelder_mm': (22, 'mm'), 'Pris_krydsfiner_gaelder_mm': (22, 'mm'),
          'Pris_clips_stk': (-1, ''), 'Timer_skifer_pr_m2': (-1, ''),
          'Timer_trae_pr_m2': (-1, ''), 'Timepris': (-1, ''), 'Levering': (-1, ''),
          'Prisgrundlag': ('Ikke oplyst', 'text'), 'Pris_dato': ('2026-11-21', 'text')}
LIMITS = {'Facade_bredde': (1200, 2400), 'Facade_hoejde': (1800, 3000),
          'Trae_tykkelse': (18, 32), 'Krydsfiner_tykkelse': (18, 22),
          'Beklaedning': (0, 1), 'Indkoebstillæg_procent': (0, 50),
          'Skifer_indkoebstillæg_procent': (0, 50)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
        temp = Path(f.name)
    temp.replace(path)


def validate_params(values):
    if set(values) != set(PARAMS):
        raise ValueError('Facadeparametre mangler eller er ændret; afstem modellen')
    for key, (_, unit) in PARAMS.items():
        if unit == 'text':
            if not isinstance(values[key], str):
                raise ValueError('Tekst mangler: '+key)
            continue
        x = float(values[key])
        if not math.isfinite(x):
            raise ValueError('Ugyldigt tal: '+key)
        if key in LIMITS:
            lo, hi = LIMITS[key]
            if not lo <= x <= hi:
                raise ValueError(f'{key} skal være mellem {lo} og {hi} i denne prøve')
        elif x < 0 and x != -1:
            raise ValueError(key+': brug -1 for ukendt eller et ikke-negativt tal')
    if values['Beklaedning'] not in (0, 1):
        raise ValueError('Beklædning skal være 0 (skifer) eller 1 (træ)')
    date.fromisoformat(values['Pris_dato'])


def model_script(project_id):
    """Uses documented command contracts; expressions place every box parametrically."""
    commands = []
    def add(command, **params):
        commands.append({'command': command, 'params': params})
    add('document.metadata.set', values={NAMESPACE: {'schema': 1, 'project_id': project_id,
        'element_id': 'facade-01', 'scope': 'Afgrænset åben facadeprøve; ikke et opvarmet rum',
        'grid': '5 stolpelinjer, 4x8 visningssten eller16 visningsbrædder; ikke standardvareformat'},
        'description': 'Live facadeprøve. Ret mål/materiale i Parameters. Regnskab følger via lokal facade_live.'})
    for name, (value, unit) in PARAMS.items():
        add('parameters.add', name=name, expression=str(value), unit=unit, favorite=True,
            comment=('0=skifer, 1=træ' if name == 'Beklaedning' else
                     '-1=ukendt; priser DKK ekskl.moms, egne daterede skøn' if value == -1 else
                     'Afgrænset facadeprøve; regnskab i lokal beregningsvisning'))
    for key, color, density in [('timber',[186,137,89],.456),('plywood',[216,188,133],.480),
                                ('windboard',[177,152,119],.255),('slate',[69,78,88],2.7)]:
        add('material.create', name='FT56_'+key, color=color, density_g_cm3=density)
    groups = {k: [] for k in ('frame','vent','plywood','windboard','slate','slate_battens','wood')}
    features = []
    def box(group, name, length, width, height, corner):
        add('solid.box', name=name, body_name=name, length=str(length), width=str(width),
            height=str(height), corner=[str(x) for x in corner])
        groups[group].append(name)
        features.append({'name': name, 'group': group})
    W, H = 'Facade_bredde', 'Facade_hoejde'
    box('plywood','F56_Krydsfiner', W,'Krydsfiner_tykkelse',H,[0,145,0])
    box('windboard','F56_Vindplade',W,12,H,[0,-12,0])
    for i in range(5):
        x = '0' if i == 0 else f'{W}-45' if i == 4 else f'({W}-45)*{i}/4'
        box('frame',f'F56_Stolpe_{i}',45,145,H+'-90',[x,0,45])
        box('vent',f'F56_Vent_{i}',45,28,H,[x,-40,0])
    for i, z in enumerate(['0', H+'-45']):
        box('frame',f'F56_Rem_{i}',W,145,45,[0,0,z])
    for r in range(8):
        for c in range(4):
            box('slate',f'F56_Skifer_{r}_{c}',W+'/4-10',8,H+'/8-10',
                [f'{W}*{c}/4+5',-73,f'{H}*{r}/8+5'])
        box('slate_battens',f'F56_Skiferlaegte_{r}',W,25,45,
            [0,-65,f'{H}*({r}+.5)/8-22.5'])
    for r in range(16):
        box('wood',f'F56_Braet_{r}',W,'Trae_tykkelse',H+'/16-2',
            [0,'-40-Trae_tykkelse',f'{H}*{r}/16+1'])
    add('document.metadata.set', key=NAMESPACE, value={'schema':1,'project_id':project_id,
        'element_id':'facade-01','bindings':{str(i+1):f['group'] for i,f in enumerate(features)},
        'scope':'Åben facadeprøve; faste5 stolpelinjer og visningsgrid, ikke produktformat'})
    for group, names in groups.items():
        material = group if group in ('plywood','windboard','slate') else 'timber'
        add('material.assign', bodies=names, material='FT56_'+material)
    add('config.column', param='Beklaedning')
    alternatives=[f for f in features if f['group'] in ('slate','slate_battens','wood')]
    for f in alternatives:
        add('config.column', feature=f['name'])
    for value,label in [(0,'Skifer'),(1,'Træ')]:
        cells={'param:Beklaedning':str(value)}
        for f in alternatives:
            cells['suppress:'+f['name']]=str(value==0 if f['group']=='wood' else value==1).lower()
        add('config.row', name=label, values=cells)
    rules = []
    for f in features:
        if f['group'] not in ('slate','slate_battens','wood'):
            continue
        for value in (0, 1):
            rules.append({'id':f['name']+str(value),'name':f['name']+' valg '+str(value),'enabled':True,
                'condition':{'type':'parameter','parameter':'Beklaedning','operator':'eq','expression':str(value)},
                'effect':{'type':'drive_suppression','feature':features.index(f)+1,
                          'value':(value == 0 if f['group'] == 'wood' else value == 1)}})
    add('config.rule', rules=rules)
    add('parameters.change', name='Beklaedning', expression=1)
    add('parameters.change', name='Beklaedning', expression=0)
    return {'commands':commands}, groups


def collect(export, inspect, project_id):
    """Bind logical groups to feature IDs, surviving body rename; refuse unsupported edits."""
    meta = inspect.get('metadata',{}).get(NAMESPACE,{})
    if meta.get('project_id') != project_id:
        raise ValueError('Den aktive model tilhører ikke dette facadeprojekt')
    model = json.loads(export['text'])
    values = {}
    for row in model.get('text_params',[]):
        if row['name'] in PARAMS:
            values[row['name']]=row['text']
    for row in inspect['params']:
        if row['name'] in PARAMS:
            if row.get('error'):
                raise ValueError('Parameterfejl: '+row['name'])
            values[row['name']] = row.get('text',row.get('value')) if PARAMS[row['name']][1]=='text' else row.get('value')
            if PARAMS[row['name']][1]=='text' and not isinstance(values[row['name']],str):
                values[row['name']] = row['expression'].strip('"')
    validate_params(values)
    if any(f.get('error') or f.get('rolled_back') for f in inspect['timeline']):
        raise ValueError('Modellen har fejl eller en tilbagerullet tidslinje')
    # The model's persisted features, not editable names, own the body mapping.
    features = model.get('features')
    if features is None:
        raise ValueError('Ukendt SolidCraft-format: features mangler')
    bindings = meta.get('bindings')
    if not bindings:
        raise ValueError('Facadens revisionsbundne delkoblinger mangler')
    groups = {k: [] for k in ('frame','vent','plywood','windboard','slate','slate_battens','wood')}
    mapped = set()
    for feature in features:
        fid = str(feature.get('id'))
        if fid not in bindings:
            raise ValueError('Ny eller ukendt feature kræver afstemning')
        if feature.get('type') != 'box':
            raise ValueError('Denne facadeversion understøtter kun sine bundne boksdele')
        if feature.get('suppressed'):
            continue
        names = feature.get('body_names',[])
        groups[bindings[fid]].extend(names)
        mapped.update(names)
    bodies = {b['name']:b for b in inspect['bodies']}
    if set(bodies) != mapped:
        raise ValueError('Modelinventaret har ændret sig; afstem delkoblingerne')
    for b in bodies.values():
        if not b.get('closed') or not math.isfinite(b.get('volume_mm3',0)) or b['volume_mm3'] <= 0:
            raise ValueError('Et facadelegeme er ikke et gyldigt lukket volumen')
    for group,names in groups.items():
        material=group if group in ('plywood','windboard','slate') else 'timber'
        for name in names:
            if model.get('materials',{}).get(name) != 'FT56_'+material:
                raise ValueError('Materialeændring uden kildekobling kræver afstemning: '+name)
    active = 'skifer' if values['Beklaedning'] == 0 else 'trae'
    if bool(groups['wood']) != (active == 'trae') or bool(groups['slate']) != (active == 'skifer'):
        raise ValueError('Geometrien svarer ikke til materialevalget')
    volumes = {k:sum(bodies[n]['volume_mm3'] for n in names)/1e9 for k,names in groups.items()}
    W,H,t,p = [values[k]/1000 for k in ('Facade_bredde','Facade_hoejde','Trae_tykkelse','Krydsfiner_tykkelse')]
    expected = {'frame':5*.045*.145*(H-.09)+2*W*.145*.045, 'vent':5*.045*.028*H,
                'plywood':W*H*p,'windboard':W*H*.012,
                'wood':16*W*t*(H/16-.002) if active=='trae' else 0,
                'slate':32*(W/4-.01)*.008*(H/8-.01) if active=='skifer' else 0,
                'slate_battens':8*W*.025*.045 if active=='skifer' else 0}
    for k,v in volumes.items():
        if not math.isclose(v,expected[k],rel_tol=1e-7,abs_tol=1e-10):
            raise ValueError('Geometri udenfor mængdereglerne: '+k)
    # Include geometry in the key: a direct feature edit cannot reuse a parameter-only result.
    return {'params':values,'volumes':volumes,'groups':groups,'bodies':len(bodies),
            'active':active,'element_id':meta['element_id'],'geometry_sha256':digest(model)}


class RustClimate:
    def __init__(self, config):
        self.config = config
        self.cache = {}
        self.calls = 0
        self.sources = {}
        self.verify()
        for key,mid in MATERIALS.items():
            source=self.command(['lookup',mid])
            self.sources[key]=source

    def verify(self):
        for path, expected in self.config['bound_files'].items():
            if file_hash(path) != expected:
                raise ValueError('Motor-/datagrundlag har ændret sig: '+str(Path(path).name))

    def command(self, args):
        c=self.config
        result=subprocess.run([c['binary'],'--root',c['root'],'--store',c['store'],
            '--snapshot',c['snapshot']]+list(map(str,args)),capture_output=True,text=True,timeout=60)
        if result.returncode:
            raise RuntimeError('Rust-beregning fejlede: '+result.stderr[-1200:])
        return json.loads(result.stdout)

    def calculate(self, source, quantity, unit):
        values={}
        refs={}
        for o in self.sources[source]['observations']:
            module=o.get('module')
            if module not in MODULES or o.get('property_id') != 'property:gwp_total':
                continue
            if module in values:
                raise ValueError('Flere klimakilder for samme modul kræver eksplicit valg')
            req={'kind':'climate','material_id':MATERIALS[source],
                 'gwp_observation_id':o['id'],'quantity':{'value':quantity,'unit':unit}}
            key=digest(req)
            if key not in self.cache:
                with tempfile.TemporaryDirectory(prefix='ft-facade-') as d:
                    path=Path(d)/'request.json';path.write_text(json.dumps(req))
                    result=self.command(['calculate',path])
                if result['status']!='ok' or result['snapshot']!=self.config['snapshot']:
                    raise ValueError('Uventet Rust-resultat')
                self.cache[key]=result;self.calls+=1
            result=self.cache[key]
            values[module]=result['value']
            refs[module]={'observation_id':o['id'],'source':result['inputs']['source_observation']}
        if set(values)!=set(MODULES):
            raise ValueError('Klimakilden mangler et forventet modul; ukendt er ikke nul')
        return values,refs


def evaluate(sample, climate):
    climate.verify()
    p,v=sample['params'],sample['volumes']
    W,H=p['Facade_bredde']/1000,p['Facade_hoejde']/1000
    area=W*H
    rows=[]
    def row(key,label,source,quantity,unit,display,display_unit,price_param,rate=0):
        modules,refs=climate.calculate(source,quantity,unit)
        rows.append({'id':key,'label':label,'source_key':source,'quantity':quantity,'unit':unit,
            'display_quantity':display,'display_unit':display_unit,'price_param':price_param,
            'purchase_allowance':rate,'modules':modules,'sources':refs})
    allowance=p['Indkoebstillæg_procent']/100
    row('frame','Skelet 45×145 mm','timber',v['frame'],'m3',5*(H-.09)+2*W,'m','Pris_skelet_m',allowance)
    row('vent','Ventilationslægter 28×45 mm','timber',v['vent'],'m3',5*H,'m','Pris_ventlaegte_m',allowance)
    row('plywood',f"Krydsfiner {p['Krydsfiner_tykkelse']:g} mm",'plywood',v['plywood'],'m3',area,'m2','Pris_krydsfiner_m2',allowance)
    densities=[o for o in climate.sources['windboard']['observations'] if o.get('property_id')=='property:density' and o.get('unit')=='kg/m³']
    if len(densities)!=1 or densities[0]['value']<=0:
        raise ValueError('Vindpladens kildebaserede densitet skal afstemmes')
    density=densities[0]
    row('windboard','Vindplade12 mm; kildebaseret densitet','windboard',v['windboard']*density['value'],'kg',area,'m2','Pris_vindplade_m2',allowance)
    rows[-1]['quantity_conversion']={'volume_m3':v['windboard'],'density_kg_m3':density['value'],'density_observation_id':density['id']}
    row('common_screws','140 fælles skruer; antaget6 g/stk','steel',.840,'kg',140,'stk','Pris_skruer_stk')
    if sample['active']=='skifer':
        row('slate','Skifer, dækket kontur; kildens30 kg/m²','slate',area,'m2',area,'m2','Pris_skifer_m2',p['Skifer_indkoebstillæg_procent']/100)
        row('battens','Skiferlægter25×45 mm','timber',v['slate_battens'],'m3',8*W,'m','Pris_skiferlaegte_m',allowance)
        row('clips','64 clips; antaget3 g/stk','steel',.192,'kg',64,'stk','Pris_clips_stk')
        row('slate_screws','64 stenskruer +80 lægteskruer; antaget6 g/stk','steel',.864,'kg',144,'stk','Pris_skruer_stk')
    else:
        row('wood',f"Træbrædder {p['Trae_tykkelse']:g} mm; konstruktionstræ som proxy",'timber',v['wood'],'m3',v['wood']/(p['Trae_tykkelse']/1000),'m2','Pris_trae_m2',allowance)
        row('wood_screws','160 beklædningsskruer; antaget4 g/stk','steel',.640,'kg',160,'stk','Pris_skruer_stk')
    # Pure estimating contract: no external quote fields, orders, discounts or supplier matching.
    # Several screw applications intentionally share one purchase product and are grouped first.
    lines={}
    for r in rows:
        key=r['price_param']
        if key not in lines:
            lines[key]={'id':key,'label':r['label'],'product_id':key,'unit':r['display_unit'],
                'net_quantity':0,'waste_rate':0,'origin':'nyt','orders':[],
                'selection':{'supplier_id':'internal','account_id':'facade','sku':key}}
        lines[key]['net_quantity']+=r['display_quantity']*(1+r['purchase_allowance'])
    offers=[]
    lines['Levering']={'id':'Levering','label':'Leveringsoverslag','product_id':'Levering','unit':'job',
        'net_quantity':1,'waste_rate':0,'origin':'nyt','orders':[],
        'selection':{'supplier_id':'internal','account_id':'facade','sku':'Levering'}}
    provenance=p['Prisgrundlag'].strip()
    valid_provenance=bool(provenance and provenance!='Ikke oplyst')
    for key,line in lines.items():
        if p[key] < 0 or not valid_provenance:
            continue
        if key=='Pris_trae_m2' and p['Pris_trae_gaelder_mm']!=p['Trae_tykkelse']:
            continue
        if key=='Pris_krydsfiner_m2' and p['Pris_krydsfiner_gaelder_mm']!=p['Krydsfiner_tykkelse']:
            continue
        raw={'supplier_id':'internal','supplier_name':'Eget overslag','account_id':'facade',
            'sku':key,'product_id':key,'mapping_reference':provenance,'unit':line['unit'],
            'origin':'nyt','price_quantity':'1','purchase_step':'0.000001','minimum_quantity':'0',
            'currency':'DKK','amount':str(p[key]),'tax_basis':'excl_vat','price_basis':'net',
            'observed_on':p['Pris_dato'],'review_on':p['Pris_dato'],'kind':'estimate',
            'availability':'unknown','source_reference':provenance}
        offers.append(dict(pricing.normalize_offer(raw),received_at=p['Pris_dato']+'T00:00:00+00:00'))
    hours_per_m2=p['Timer_skifer_pr_m2' if sample['active']=='skifer' else 'Timer_trae_pr_m2']
    hours=-1 if hours_per_m2<0 else hours_per_m2*area
    known=lambda value: None if value<0 or not valid_provenance else str(value)
    project={'schema':1,'scope_id':sample['element_id'],'account_id':'facade','currency':'DKK',
        'tax_basis':'excl_vat','lines':list(lines.values()),
        'delivery':{'internal':{'amount_excl_vat':'0','reference':'Levering er særskilt overslagspost, ikke medregnet igen'}},
        'labor':[{'id':'mount','label':'Montageoverslag, persontimer','hours':known(hours),
            'hourly_rate':known(p['Timepris']),'rate_basis':'contractor_rate','reference':provenance or 'Ikke oplyst'}]}
    budget=pricing.assess(project,{'schema':1,'offers':offers,'imports':[]},date.fromisoformat(p['Pris_dato']))
    totals={m:sum(r['modules'][m] for r in rows) for m in MODULES}
    return {'schema':1,'scope':'Én åben facadeprøve; kendt materialedelsum, ikke bygnings-LCA',
        'element_id':sample['element_id'],'active':sample['active'],'params':p,'area_m2':area,
        'body_count':sample['bodies'],'geometry_sha256':sample['geometry_sha256'],'rows':rows,
        'climate':{'modules':totals,'known_subtotal':sum(totals[m] for m in MODULES if m!='D'),
                   'snapshot':climate.config['snapshot'],'status':'partial_reference'},
        'budget':budget,'native_calculations_so_far':climate.calls,
        'unresolved':['Produktvalg, bæreevne/fastgørelse, brand og fugt er ikke eftervist.',
            'Isolering, lufttæt lag, tape, kanter og øvrige bygningsdele indgår ikke i denne åbne prøve.',
            'A4/A5, vedligehold, udskiftninger, energi og spildets klimafølger er uafklarede.',
            'Indkøbstillæg påvirker overslaget; ekstra produktion/affald er ikke med i klimadelsummen.',
            'Træets konstruktionstræreference og stålets pladereference er generiske produktproxyer.',
            'Fastgørelsesantal og masser er eksplicitte, faste prøveantagelser, ikke dimensionering.']}


def main():
    import argparse
    import uuid
    parser=argparse.ArgumentParser(description='Opret en selvstændig parametrisk facadeprøve uden at ændre det åbne dokument')
    parser.add_argument('directory',type=Path)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--snapshot',required=True)
    parser.add_argument('--solidcraft-cli',type=Path,required=True)
    args=parser.parse_args()
    target=args.directory.resolve()
    if target.exists() and any(target.iterdir()):
        raise ValueError('Vælg en ny eller tom projektmappe')
    if args.snapshot=='latest':
        raise ValueError('Angiv en fastholdt dataudgave, ikke latest')
    manifest=args.store.resolve()/args.snapshot/'manifest.json'
    config={'schema':1,'project_id':str(uuid.uuid4()),'project_directory':str(target),
        'engine':{'binary':str(args.engine.resolve()),'root':str(Path(__file__).resolve().parent),
        'store':str(args.store.resolve()),'snapshot':args.snapshot,
        'bound_files':{str(args.engine.resolve()):file_hash(args.engine),str(manifest):file_hash(manifest)}}}
    target.mkdir(parents=True,exist_ok=True)
    script,_=model_script(config['project_id'])
    atomic_json(target/'model-script.json',script)
    subprocess.run([str(args.solidcraft_cli.resolve()),'run',str(target/'model-script.json'),
        '--save',str(target/'facade.sc'),'--quiet'],check=True,capture_output=True,text=True)
    atomic_json(target/'projekt.json',config)
    print('Åbn i SolidCraft: '+str(target/'facade.sc'))
    print('Start lokal beregning: python3 facade_live.py '+str(target/'projekt.json'))


if __name__=='__main__':main()
