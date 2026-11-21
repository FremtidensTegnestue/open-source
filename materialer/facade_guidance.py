"""Small project goals and evidence register, separate from measured quantities and climate data."""
import copy
import math

AREAS = {
    'architecture': ('Arkitektur, brug og adgang', 'Fasthold rum, funktion, arkitektoniske kvaliteter og tilgængelighed. Dette eftervises ikke af facadeberegningen.'),
    'site': ('Sted, terræn og fundering', 'Afklar placering, terræn, jord, fundament, regnvand og relevante stedskrav for bygningen.'),
    'product': ('Produkter og materialer', 'Vælg konkrete produkter og afstem alle lag, beslag, fuger og behandlinger.'),
    'transport': ('Transport og spild', 'Afklar leverancer, afstande, indkøb, afskær og affald. Indkøbstillæg er ikke automatisk affald.'),
    'life': ('Levetid og vedligehold', 'Registrér levetid pr. del og afklar reparation, adgang og udskiftning.'),
    'energy': ('Energi og indeklima', 'Afklar brug, temperatur, termiske egenskaber og faktisk energibehov.'),
    'structure': ('Bæring og fastgørelse', 'Eftervis laster, understøtninger, samlinger og fastgørelse.'),
    'fire': ('Brand', 'Afklar krav og dokumentation for den konkrete samlede opbygning.'),
    'moisture': ('Fugt og tæthed', 'Afklar regn, tørring, lufttæthed, kanter og grænseflader.'),
    'sound': ('Lyd og akustik', 'Afklar lydkrav, opbygning og tilslutninger.'),
    'ventilation': ('Ventilation', 'Afklar luftveje og drift. Et oplukkeligt vindue alene efterviser ikke naturlig ventilation.'),
    'daylight': ('Dagslys og udsyn', 'Afklar orientering, åbninger, skygge, udsyn og eventuel overophedning.'),
    'installations': ('Installationer', 'Medtag varme, el, belysning, vand og afløb med materialer, drift og udskiftninger, hvor relevant.'),
    'circularity': ('Bevaring og genbrug', 'Afklar oprindelse, stand, reparationsbehov, restlevetid og faktisk videre brug.'),
    'delivery': ('Indkøb og leverancer', 'Afstem mængdeliste, pakninger, prisdato, tilbud, ansvar og levering. Der er ikke en aktiv leverandørforbindelse.'),
    'operation': ('Drift og aflevering', 'Afklar vedligehold, adgang, materialepas, kontrol og overdragelse til bygningens brugere.'),
    'disassembly': ('Adskillelse · frivilligt tilvalg', 'Afklar adgang, forbindelser, rækkefølge, tab og retablering.'),
}


def defaults():
    return {'schema':1,'revision':0,'budget_excl_vat':None,'climate_target_kg':None,
            'period_years':None,'dfd_requested':False,'lifetimes':{},'evidence':{}}


def nonnegative(value, label, maximum=None):
    if value is None:return None
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError(label+': indtast et gyldigt tal eller lad feltet stå tomt')
    if maximum is not None and value>maximum:raise ValueError(label+': tallet er for stort')
    return value


def validate(value):
    result=copy.deepcopy(value)
    if set(result)!=set(defaults()) or result['schema']!=1:
        raise ValueError('Ukendt format for projektets mål og grundlag')
    if type(result['revision']) is not int or result['revision']<0:raise ValueError('Ugyldig revision')
    nonnegative(result['budget_excl_vat'],'Budget',1e12)
    nonnegative(result['climate_target_kg'],'Klimamål',1e12)
    period=nonnegative(result['period_years'],'Betragtningsperiode',200)
    if period is not None and period<=0:raise ValueError('Betragtningsperioden skal være større end nul')
    if type(result['dfd_requested']) is not bool:raise ValueError('DfD skal være et udtrykkeligt tilvalg')
    if not isinstance(result['lifetimes'],dict) or not isinstance(result['evidence'],dict):
        raise ValueError('Ugyldigt grundlag')
    # IDs are the existing physical calculation rows, including alternatives not currently active.
    ids={'frame','vent','plywood','windboard','common_screws','slate','battens','clips','slate_screws','wood','wood_screws'}
    if set(result['lifetimes'])-ids:raise ValueError('Ukendt materialepost')
    for key,item in result['lifetimes'].items():
        if not isinstance(item,dict) or set(item)!={'years','reference'}:raise ValueError('Ugyldigt levetidsgrundlag')
        years=nonnegative(item['years'],'Levetid',200)
        if years is not None and years<1:raise ValueError('Levetid skal være mindst ét år i denne screening')
        if not isinstance(item['reference'],str) or len(item['reference'])>2000:raise ValueError('Ugyldig levetidsreference')
        if years is not None and not item['reference'].strip():raise ValueError('Angiv, hvor levetidsskønnet kommer fra')
    if set(result['evidence'])-set(AREAS):raise ValueError('Ukendt fagområde')
    for item in result['evidence'].values():
        if not isinstance(item,dict) or set(item)!={'status','reference'} or item['status'] not in ('unknown','recorded','not_applicable'):
            raise ValueError('Ugyldig grundlagsstatus')
        if not isinstance(item['reference'],str) or len(item['reference'])>2000:raise ValueError('Ugyldigt grundlagsnotat')
        if item['status']!='unknown' and not item['reference'].strip():raise ValueError('Notat eller begrundelse mangler')
    return result


def replacement_years(period, life):
    """Scenarios, not product guarantees; no replacement at the final instant."""
    if period is None or life is None:return None
    count=max(0,math.ceil(period/life-1e-12)-1)
    return [life*n for n in range(1,count+1)]


def overview(result, reference, settings):
    s=validate(settings);area=result['area_m2'];budget=result['budget']
    selected=sum(row['selected'] is not None for row in budget['lines'])
    total=len(budget['lines']);forecast=budget['forecast_excl_vat']
    amount=None if forecast is None else float(forecast)
    target=s['budget_excl_vat'];climate=result['climate']['known_subtotal']
    areas=[]
    for key,(label,action) in AREAS.items():
        if key=='disassembly' and not s['dfd_requested']:continue
        evidence=s['evidence'].get(key,{'status':'unknown','reference':''})
        areas.append({'id':key,'label':label,'action':action,**evidence})
    lifetimes=[]
    for row in result['rows']:
        item=s['lifetimes'].get(row['id'],{'years':None,'reference':''})
        years=replacement_years(s['period_years'],item['years'])
        lifetimes.append({'id':row['id'],'label':row['label'],**item,'replacement_years':years,
                          'replacement_count':None if years is None else len(years)})
    next_actions=[]
    if selected<total:
        next_actions.append({'label':'Få prisoverslaget på plads','detail':f'{total-selected} materialer/levering mangler pris. Tomme felter er ukendte.', 'target':'prices'})
    if any(x['hours'] is None or x['hourly_rate'] is None for x in budget['labor']):
        next_actions.append({'label':'Afklar montagearbejdet','detail':'Timer og timepris mangler eller er uafklarede.', 'target':'prices'})
    if s['period_years'] is None or any(x['years'] is None for x in lifetimes):
        next_actions.append({'label':'Undersøg levetid og udskiftning','detail':'Se hvilke dele der kan kræve nye indgreb i perioden.', 'target':'lifecycle'})
    if any(x['status']=='unknown' for x in areas):
        next_actions.append({'label':'Afklar det resterende grundlag','detail':'Transport, øvrig livscyklus og faglig dokumentation er fortsat åbne.', 'target':'coverage'})
    if not next_actions:
        next_actions.append({'label':'Gennemgå dokumentation og resten af livscyklussen','detail':'Registrerede notater og udskiftningsscenarier er ikke en faglig godkendelse eller en fuld LCA.', 'target':'coverage'})
    return {'settings_revision':s['revision'],'priced_lines':selected,'price_lines':total,
        'climate_per_m2':climate/area,'price_per_m2':None if amount is None else amount/area,
        'budget_difference':None if target is None or amount is None else amount-target,
        'known_above_budget':target is not None and float(budget['known_subtotal_excl_vat'])>target,
        'climate_target_difference':None if s['climate_target_kg'] is None else climate-s['climate_target_kg'],
        'areas':areas,'lifetimes':lifetimes,'next_actions':next_actions[:3],
        'notes':['Klimamålet gælder alene den viste materialedelsum, ikke hele bygningens LCA.',
                 'Levetider giver et udskiftningsscenarie. Dets klima, arbejde og følgeposter er endnu ikke beregnet.',
                 'Et registreret dokument eller et ikke-relevant-notat er ikke en teknisk godkendelse.']}
