#!/usr/bin/env python3
"""Build the Lisbjerg evidence summary, element CSV and printable report.

Reads preserved evidence only. Does not modify original models or material DB.
Run from any directory: python3 /absolute/path/to/build_report.py
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import html
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'unpacked/archive/opensource.vandkunsten.com/07_FBABLisbjerg/VK_FBABLisbjerg/VK_FBABLisbjerg'

def read(p):
    return json.loads(p.read_text())

def save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def sha(p):
    return hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()

def fmt(x, n=0):
    return f'{x:,.{n}f}'.replace(',', '_').replace('.', ',').replace('_', '.')

def table(headers, rows, widths=None):
    return '<table><thead><tr>' + ''.join('<th>'+html.escape(x)+'</th>' for x in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'

summary = {'schema_version': 1, 'analysis_date': '2026-11-17', 'status': 'partial',
           'scope': 'Archived project evidence and BIMcraft-derived quantities; no verified whole-building LCA or as-built statement.',
           'model_combination': 'ARK and KON kept separate; no cross-model spatial overlap analysis.', 'models': {}}
element_rows = []
for key in ('ark', 'kon'):
    normalized = read(HERE / f'data/{key}-normalized.json')
    source = read(HERE / f'raw/ifc-source-audit/results/{key}/summary.json')
    products = [json.loads(s) for s in (HERE / f'raw/ifc-source-audit/results/{key}/products.jsonl').read_text().splitlines()]
    by_guid = {e['source_ref']['guid']: e for e in normalized['elements']}
    physical = [p for p in products if p['is_ifc_element'] and p['ifc_class'] != 'IfcOpeningElement']
    imported = [by_guid[p['guid_uuid']] for p in physical if p['guid_uuid'] in by_guid]
    missing = [p for p in physical if p['guid_uuid'] not in by_guid]
    warn_by_id = defaultdict(list)
    for w in normalized['warnings']:
        if w.get('element_id'):
            warn_by_id[w['element_id']].append(w['code'])
    positive = [e for e in imported if (e.get('volume_m3') or 0) > 0]
    homogeneous = [e for e in positive if e.get('material_name') and e['material_name'] not in ('<Unnamed>', 'Default Wall')]
    floors = [e for e in imported if e['category'] == 'floor']
    volume_groups = defaultdict(lambda: {'elements': 0, 'volume_m3': 0})
    for e in floors:
        group = volume_groups[e['material_name'] or '<mixed_or_unresolved>']
        group['elements'] += 1
        group['volume_m3'] += e['volume_m3']
    for g in volume_groups.values():
        g['volume_m3'] = round(g['volume_m3'], 3)
        g['rounding_bound_m3'] = g['elements'] * 0.0005
    imp = normalized['extraction']['import_summary']
    src_path = Path(normalized['model']['path'])
    assert sha(src_path) == normalized['model']['sha256'] == source['sha256']
    summary['models'][key] = {
        'model_path': str(src_path.relative_to(ROOT)), 'sha256': sha(src_path),
        'source_unchanged': True, 'source_schema': source['schema'],
        'source_ifc_elements': source['element_count'], 'source_elements_excluding_openings': len(physical),
        'source_material_definitions': source['material_definition_count'],
        'source_elements_without_named_material_excluding_openings': sum(not p['material_names'] for p in physical),
        'source_multi_material_elements': source['element_products_with_multiple_named_materials'],
        'source_quantity_sets': source['explicit_element_quantity_set_count'],
        'normalized_elements_including_nonphysical': len(normalized['elements']),
        'source_physical_elements_matched_to_import': len(imported),
        'source_physical_elements_not_matched': len(missing),
        'unmatched_by_source_class': dict(Counter(p['ifc_class'] for p in missing)),
        'import_reported_skipped': len(imp['skipped']), 'import_reported_generic': imp['generic'],
        'import_rebase_mm': imp['moved'], 'inspect_warnings': sum(w['code'] == 'bimcraft_model_warning' for w in normalized['warnings']),
        'physical_elements_with_positive_reported_volume': len(positive),
        'physical_elements_with_volume_and_homogeneous_name': len(homogeneous),
        'floor_groups': dict(volume_groups),
        'floor_area_sum_m2': round(sum(e.get('area_m2') or 0 for e in floors), 2),
        'category_counts': dict(Counter(e['category'] for e in imported)),
        'quantity_precision': 'floor volumes reported to 0.001 m3; worst-case rounding bound 0.0005 m3 per floor, not total uncertainty',
    }
    for p in physical:
        e = by_guid.get(p['guid_uuid'])
        element_rows.append({
            'model': key.upper(), 'source_step_id': p['entity_id'], 'source_global_id': p['global_id'],
            'guid_uuid': p['guid_uuid'], 'source_class': p['ifc_class'], 'source_name': p['name'],
            'source_material_names': json.dumps(p['material_names'], ensure_ascii=False),
            'imported_element_id': e['id'] if e else '', 'imported_category': e['category'] if e else '',
            'homogeneous_name_in_adapter': e.get('material_name') if e else '',
            'reported_volume_m3': e.get('volume_m3') if e else '',
            'reported_area_m2': e.get('area_m2') if e else '',
            'volume_rounding_bound_m3': 0.0005 if e and e['category'] == 'floor' and e.get('volume_m3') is not None else '',
            'status': 'imported' if e else 'source_not_matched_to_import',
            'adapter_warning_codes': json.dumps(warn_by_id[e['id']] if e else [], ensure_ascii=False),
            'verified_product_or_epd_binding': False,
        })

with (HERE / 'data/element-inventory.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(element_rows[0])); writer.writeheader(); writer.writerows(element_rows)

gaps = [
('G01','1','Modelansvarlig + projekterende','Udført revision og omfang','Bekræft hvilke modeller, blokke, tegninger og revisioner der beskriver det udførte byggeri.','Alle projektkonklusioner','input'),
('G02','1','Udvikler + BIM-ansvarlig','Import og nettomængder','Gennemgå 342/6 importudeladelser, 145 generiske ARK-objekter og 382/6 kildeobjekter uden GUID-match. Verificér nettoprofilvolumener og åbninger.','Komplet materialemængde','implementation_and_validation'),
('G03','1','BIM-ansvarlig + ingeniør','Overlap og samlinger','Afstem koordinater, faggrænser og delobjekter mellem ARK/KON; angiv hvilken model der ejer hver mængde.','Summer uden dobbeltregning','input_and_validation'),
('G04','1','Projekterende + leverandør','Materiale- og produktkort','Bind hver type/GUID til præcis vare, producent, sammensætning, dokument og EPD-id eller begrundet generisk reference.','Masse og miljøbidrag','input'),
('G05','1','Projekterende + leverandør','Træ og densitet','Træart, massivtræ/limtræ/CLT-produkt, densitetens fugtgrundlag, lag-/fiberretning og dokumenteret fugtinterval. C35 alene er utilstrækkeligt.','Trævægt og fugtbevægelse','input'),
('G06','1','Ingeniør + betonleverandør','Beton og armering','Betonstyrke, eksponering, recept/EPD, densitet og faktisk armeringsmængde. Afklar om 2% Steel er masse- eller volumenandel.','Beton- og stålspecifik masse/klima','input'),
('G07','1','Projekterende + leverandør','Lag og tegningskobling','Knyt lokale opbygninger til modelobjekter. Afklar T1-varianter og Y2 220/240 mm; dokumentér skeletandel og åbninger.','Isolering, beklædning, membraner','input_and_validation'),
('G08','2','LCA-ansvarlig','Beregningsgrundlag','Referenceareal, periode, afgrænsning, valgte indikatorer/metoder og sammenlignelige data med geografi/tidsgrundlag.','Sammenligneligt samlet regnskab','input'),
('G09','2','LCA-ansvarlig + entreprenør','Transport og byggeplads','Transportmidler/-afstande, spild, energiforbrug, emballage og øvrige byggepladsdata.','Transport-/udførelsesbidrag','input'),
('G10','2','Drift + projekterende','Drift, udskiftning og slutning','Energimodel/forbrug, vedligehold, levetider, udskiftninger, demontering, affald og slutscenarier.','Livscyklus og livscyklusøkonomi','input'),
('G11','2','Bygningsfysiker + udvikler','Varme og fugt','Verificeret λ, μ/sd, sorption, samlinger, kuldebroer, klima og randbetingelser; implementér/validér relevante metoder.','R/U-værdier og fugtanalyse','input_and_implementation'),
('G12','2','Ingeniør / brand / akustik','Faglige beregningsmodeller','Laster, understøtninger, samlinger, sikkerhedsfaktorer, brand- og akustikdokumentation for den konkrete opbygning.','Styrke, brand og lyd','input_and_implementation'),
('G13','2','Miljøspecialist + udvikler','Øvrige miljøindikatorer','Vælg sammenlignelig indikator, metode og modul. Tilføj beregningsmetoder ud over nuværende GWP-skalering.','Vand, ressourcer, affald og andre miljøpåvirkninger','input_and_implementation'),
('G14','2','Bygherre + drift','Økonomi og genbrug','Enhedspriser, arbejdsløn, diskontering, tilstand, demonterbarhed og restlevetid.','Pris, LCC og genbrugspotentiale','input_and_implementation'),
]
fields=['id','priority','owner','topic','missing_or_action','unlocks','gap_kind']
with (HERE/'data/missing-data.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(fields);w.writerows(gaps)
save(HERE/'data/missing-data.json',[dict(zip(fields,g)) for g in gaps])

mass = read(HERE/'data/concrete-reference-mass-result.json')
climate = read(HERE/'data/concrete-reference-climate-result.json')
context = read(HERE/'data/concrete-reference-context.json')
assert sha(ROOT / mass['inputs']['density']['citation']['local_path']) == mass['inputs']['density']['citation']['sha256']
assert sha(ROOT / climate['inputs']['source_observation']['citation']['local_path']) == climate['inputs']['source_observation']['citation']['sha256']
expected_groups = {
    'ark': {'<mixed_or_unresolved>': (86, 919.030), '_gulv_beton (100mm)': (4, 13.929), '_gulv_beton (200mm)': (10, 19.099)},
    'kon': {'Wood - C35': (75, 354.568), 'Beton In Situ - Dæk': (20, 209.709), 'Plywood, Sheathing': (2, 0.096)},
}
# Fail on changed quantities rather than reprinting static explanatory numbers.
for key in ('ark', 'kon'):
    actual = {name: (g['elements'], g['volume_m3']) for name, g in summary['models'][key]['floor_groups'].items()}
    assert actual == expected_groups[key], 'Changed floor groups: recheck report prose and scenario requests.'
summary['reference_scenario'] = {**context, 'material_id': 'br18:t7:B1433:row25',
    'mass_kg': mass['value'], 'gwp_A1_A3_kg_CO2eq': climate['value'],
    'mass_rounding_bound_kg': context['rounding_bound_m3'] * mass['inputs']['density_normalized']['value'],
    'gwp_rounding_bound_kg_CO2eq': context['rounding_bound_m3'] * climate['inputs']['source_observation']['value']}
summary['verified_project_product_bindings'] = 0
summary['original_drawings'] = {'files': 6, 'pages': 132, 'pages_visually_reviewed': 4,
    'method': 'All pages text-extracted and targeted-searched; selected critical pages visually reviewed; not a complete engineering drawing check.'}
save(HERE/'data/summary.json',summary)
ark, kon = summary['models']['ark'], summary['models']['kon']

def section(title, body, tag='Undersøgelse'):
    return f'<section class="report-page"><div class="eyebrow">{tag}</div><h1>{title}</h1>{body}</section>'

pages = []
pages.append('''<section class="cover"><div class="eyebrow">Fremtidens Tegnestue · materialedata i praksis</div>
<h1>Lisbjerg Bakke<br><em>Hvad kan vi beregne?</em></h1>
<p class="subtitle">En gennemgang af de åbne modeller og tegninger: konkrete mængder, synlige begrænsninger og de oplysninger, der åbner for flere beregninger.</p>
<img class="hero" src="assets/lisbjerg-fbab-village-gallery.jpg" alt="Træbeklædte boliger i Lisbjerg Bakke">
<p class="caption">Foto fra Vandkunstens delte projektpakke. Fotomappen er krediteret Helene Høyer Mikkelsen.</p>
<div class="meta">17. november 2026<br>ARK + KON · seks tegningssæt · sporbare beregninger</div></section>''')

pages.append(section('Et brugbart grundlag — med synlige huller', '''
<p class="lead">Vi kan allerede læse modellerne, finde materialer og udtrække konkrete mængder. Vi kan også beregne vægt og klimabidrag for et afgrænset referencescenarie. Et dokumenteret regnskab for hele det udførte byggeri kræver flere oplysninger og bedre mængdeudtræk.</p>
<div class="metrics"><div><b>2</b><span>originale IFC-modeller</span></div><div><b>132</b><span>sider i seks PDF’er</span></div><div><b>75</b><span>trædæk med beregnet volumen</span></div></div>
<h2>Det mest konkrete resultat</h2>
<p>KON-modellen indeholder 75 dæk med ét lag mærket <strong>Wood - C35</strong>, type <em>140mm - Massiv trædæk</em>. BIMcraft rapporterer tilsammen <strong>354,568 m³</strong>. Originalens materialetildeling er kontrolleret; volumen er beregnet af importprogrammet og afrundet. Det er en delmængde af modellen, ikke alt træ i byggeriet.</p>
<p>Samme udtræk giver 20 betondæk med <strong>209,709 m³</strong> og to krydsfinerdæk med <strong>0,096 m³</strong>. Der findes også mange vægge, bjælker, søjler og forbindelser, som den undersøgte CLI-adgang ikke giver et nettovolumen for.</p>
<div class="callout"><strong>Hvorfor giver 355 m³ træ ikke straks en vægt?</strong><br>Volumen fortæller, hvor meget plads materialet fylder. Vægt kræver også densitet, altså kilo pr. kubikmeter. C35 er en styrkemærkning; den dokumenterer ikke træart, fugt eller den densitet, som vi skal gange med.</div>
<h2>Hvad rapportens tal betyder</h2>
<p><span class="label">Kildeoplysning</span> kommer direkte fra model eller tegning. <span class="label">Programberegnet</span> er BIMcrafts fortolkning af modellen. <span class="label">Referencescenarie</span> bruger et eksplicit valgt datasæt, som endnu ikke er bekræftet for projektet. <span class="label">Uafklaret</span> betyder, at et nødvendigt input eller en metode mangler.</p>
<p class="caption">Modelmængder kan være præcise som softwareoutput uden at dokumentere faktisk leverance eller udført byggeri. Kilder: [F1–F2], [M1–M3].</p>''', 'Konklusion'))

coverage_rows = [
('Oprindelige IFC-elementer, inklusive åbninger',fmt(ark['source_ifc_elements']),fmt(kon['source_ifc_elements'])),
('Kildeelementer, når åbninger udelades',fmt(ark['source_elements_excluding_openings']),fmt(kon['source_elements_excluding_openings'])),
('Heraf med GUID-match i udtrækket',fmt(ark['source_physical_elements_matched_to_import']),fmt(kon['source_physical_elements_matched_to_import'])),
('Heraf uden GUID-match i udtrækket',fmt(ark['source_physical_elements_not_matched']),fmt(kon['source_physical_elements_not_matched'])),
('Udeladelser angivet af selve importen',fmt(ark['import_reported_skipped']),fmt(kon['import_reported_skipped'])),
('Importeret som generiske repræsentationer','145','0'),
('Kildeelementer uden navngivet materiale, ekskl. åbninger','186','0'),
('Deklarerede Qto-mængdesæt i originalen','0','0')]
pages.append(section('To modeller, som skal afstemmes', '''
<p>ARK beskriver arkitektens model; KON beskriver konstruktionerne. Begge er IFC2X3. De beskriver forskellige faglige sider af projektet og kan indeholde samme fysiske bygningsdel med forskellige identifikatorer.</p>'''+table(['Kontrol','ARK','KON'],coverage_rows)+'''
<p class="caption">Elementoptællinger er ikke vægt- eller dækningsprocenter for bygningen. ARK indeholder også samlingsobjekter og delobjekter: 31 elementer har børn, og 44 har forældre. De er ikke automatisk indbyrdes adskilte materialemængder. [M1]</p>
<h2>Tre forhold skal med i enhver sum</h2>
<ol><li><strong>Fagligt overlap:</strong> ingen fælles element-GUID’er blev fundet. Det beviser ikke, at der ikke er fysisk overlap. Der er ikke udført en rumlig overlapkontrol.</li>
<li><strong>Placering:</strong> BIMcraft flytter ARK og KON med forskellige oprindelser. Importens flytninger er henholdsvis [223348000; −198970000] og [223345000; −198971000] mm. Koordinater skal afstemmes før en geometrisk sammenligning.</li>
<li><strong>Importtab:</strong> importens antal udeladelser og antallet af kildeobjekter uden GUID-match tæller forskellige forhold. Originale samlinger, børn og omklassificeringer skal undersøges i deres relationer.</li></ol>
<div class="callout">Ingen ARK-mængde er lagt oven i en KON-mængde i denne rapport. Der er heller ikke beregnet en samlet bygningsvægt eller et samlet CO₂-aftryk.</div>''', 'Modeller og dækning'))

quantity_rows = [
('KON · Wood - C35','75','354,568','±0,0375 m³','140 mm massivtrædæk; produkt og densitet mangler'),
('KON · Beton In Situ - Dæk','20','209,709','±0,0100 m³','Betonklasse, recept og armering mangler'),
('KON · Plywood','2','0,096','±0,0010 m³','Krydsfinerprodukt og densitet mangler'),
('ARK · beton, homogent navn','14','33,028','±0,0070 m³','Generisk materiale; overlap med KON uafklaret'),
('ARK · blandet/uafklaret opbygning','86','919,030','±0,0430 m³','Samlet lagvolumen; kan ikke tildeles ét materiale')]
pages.append(section('Mængder, vi kan udtrække nu', '''
<p>Tabellen viser gulv-/dækobjekter, hvor BIMcraft udstiller et positivt volumen. Materialenavnene er bevaret. Tal for forskellige modeller står særskilt.</p>'''+table(['Model og materiale','Antal','Volumen m³','Kun afrunding','Begrænsning'],quantity_rows)+'''
<p class="caption">Afrundingsgrænserne er antal × 0,0005 m³ og gælder alene rapportering til 0,001 m³. De dækker ikke importfejl, geometrisk usikkerhed, overlap, manglende objekter eller usikkerhed i materialedata. [M2]</p>
<h2>Arealer er også tilgængelige</h2>
<p>ARK rapporterer 3.813,49 m² gulv-/dækareal, 2.160,26 m² loftareal og 1.872,30 m² tagareal. KON rapporterer 4.904,69 m² gulv-/dækareal. Arealerne har kategoriens programbetydning; de er ikke her dokumenteret som opvarmet etageareal, nettofacadeareal eller LCA-referenceareal. De lægges ikke sammen.</p>
<h2>Tre vigtige fravalg</h2>
<ul><li>Rumvolumen er luftvolumen og indgår ikke som materialemængde. Åbninger og skakte behandles heller ikke som materiale.</li>
<li>Væggenes længde × højde × tykkelse kan højst være et bruttooverslag. Det er ikke et kontrolleret nettovolumen med åbninger, samlinger og profilform.</li>
<li>80 stålbjælker har en samlet programberegnet vægt på 18.648,97 kg. CLI’en antager her ståldensitet 7.850 kg/m³. Det er en begrænset profilreference, ikke alle ståldele eller en uafhængigt bekræftet projektvægt.</li></ul>
<p>Kun 14 ARK-elementer og 97 KON-elementer har både et positivt rapporteret materialeelementvolumen og et entydigt materialenavn i den nuværende adapter. Det er en teknisk parathedsmåling pr. objekt, ikke en procentdel af byggeriets materialer. [M2–M4]</p>''', 'Beregnet udtræk'))

pages.append(section('Materialer: navn er første led', table(['Materialefamilie og konkrete spor','Hvad vi kan gøre','Det næste nødvendige input'],[
('Træ, massivtræ og limtræ: Wood - C35, C18/C24 og GL24C/GL32H/GL32C; ARK-navne med CLT','Sortere typer og læse dimensioner/lag. Beregne vægt efter godkendt densitet.','Produktstruktur, træart, fugtgrundlag, densitet og konkret EPD/reference. C35 må ikke automatisk blive til CLT.'),
('Beton: dæk, fundamenter og vægelementer; nogle KON-navne indeholder “2% Steel”','Separere dæk og betontyper; lave tydeligt valgt referencescenarie.','Recept, styrke, eksponering, armering og definition af 2 %. Undgå at regne armering både inde i komposit og igen separat.'),
('Stål: profiler og samlinger; kildeetiketter med bl.a. S235, S460 og 345 MPa','Søge relevante data for forskellige profil-/produktionsformer.','Nettoprofilvolumen, korrekt stålkvalitet, produktionsvej, behandling og dokumentation. En styrkeetiket er ikke en EPD.'),
('Isolering og plader: Rockwool kl.34, Cembrit Classic, krydsfiner og gips-/loftlag','Udtrække lokale lag og tykkelser fra tegningerne.','Type/GUID-kobling, nettoareal, skelet-/dækningsandel og verificeret produktdata.'),
('Membraner, tagpap, neopren, beslag og fastgørelser','Registrere produktspor, mål og lokale styktal.','Tykkelse/arealvægt, leveret produkt, globalt antal samlinger og faktisk mængde.'),
('Vinduer, døre, installationer og inventar','Katalogisere originalens objekter og importhuller.','Dækning, produktspecifikationer, sammensætning, mængder, levetider og miljødata.')])+'''
<div class="callout"><strong>Databasen giver kandidater; dokumentationen afgør valget.</strong> Der er ikke godkendt nogen projektprodukt-/EPD-binding i denne undersøgelse. Et tekstmatch på “træ” eller “beton” kan ikke i sig selv afgøre, hvilket datasæt der beskriver den faktiske leverance.</div>
<p class="caption">Materialefamilierne omfatter konstruktioner, klimaskærm, indvendige lag og øvrige produkter. Kildehenvisninger og kandidatvurderinger findes i material-candidates.json. [F1–F2], [D1–D6], [M3]</p>''', 'Materialeparathed'))

pages.append(section('Et fuldt spor gennem beregningen', '''
<p class="lead">Eksempel: Hvad ville de 20 KON-betondæk veje og bidrage med i produktionen, hvis deres rapporterede volumen blev beskrevet af den valgte betonreference?</p>
<div class="callout scenario"><strong>Udtrykkeligt referencescenarie.</strong> Originalmodellen angiver “Beton In Situ - Dæk”, men dokumenterer ikke C25/30 eller eksponeringsklasse X0/XC1. Datasættet er valgt til at demonstrere beregningen. Resultatet dokumenterer ikke projektets faktiske beton, armering eller samlede klimaaftryk.</div>
<ol><li><strong>Mængde:</strong> 20 identificerede dæk i KON, summeret til 209,709 m³. GUID’er og individuelle volumener er gemt sammen med modellens kontrolsum.</li>
<li><strong>Reference:</strong> BR18 tabel 7, post B1433, række 25: “Fabriksbeton (C25/30) i eksponeringsklasserne X0 og XC1”. Den downloadede originalfil og de valgte celler følger beregningssvaret.</li>
<li><strong>Densitet:</strong> 2.246 kg/m³. <strong>Klimafaktor A1–A3:</strong> 241 kg CO₂e pr. 1 m³. Det er to kildeobservationer fra samme reference.</li></ol>
<div class="formula">209,709 m³ × 2.246 kg/m³<br><b>471.006,414 kg ≈ 471 ton</b></div>
<div class="formula">209,709 m³ × 241 kg CO₂e/m³<br><b>50.539,869 kg CO₂e ≈ 50,5 ton CO₂e</b></div>
<p>A1–A3 beskriver produktionsfasen i den valgte kilde. Der er ikke lagt transport, byggeplads, drift, udskiftninger, slutning eller modul D oveni. Andre bygningsdele og særskilt armering er heller ikke med.</p>
<p>Alene volumenafrundingen kan give op til ±22,46 kg i vægt og ±2,41 kg CO₂e i dette scenarie. Det er ikke et samlet usikkerhedsinterval; valget af betonreference kan have langt større betydning.</p>
<p class="caption">Kan køres igen med de gemte calculate-requests. Kilde: [R1], Sheet1!E25 og K25:L25; modelmængder: [M2]. Referencevalget er ikke en vurdering af, hvilke data der skal anvendes i en bestemt myndighedsberegning.</p>''', 'Referencescenarie · ikke projektresultat'))

pages.append(section('Tegningerne lukker nogle huller', '''
<p>De seks PDF’er indeholder tilsammen 132 sider. Alle er tekstudtrukket og undersøgt med målrettet søgning; fire kritiske sider er visuelt kontrolleret. Det er ikke en fuld faglig kontrol af alle tegningsstreger.</p>
<h2>Eksempel: en ydervægskassette</h2>
<p>På <em>tværsnit og kassettedetaljer.pdf</em>, PDF-side 1, Snit-B, udskrevet 27.02.2017, beskrives Y1 blandt andet med:</p>
<ul><li>9 mm Cembrit Classic-vindplade.</li><li>45 × 295 mm C18-skelet pr. maksimalt 600 mm.</li><li>290 mm mineraluld, kl.34, Rockwool.</li><li>0,20 mm PE-folie samt 45 × 45 mm påforing; folie og påforing undlades udtrykkeligt i baderum.</li></ul>
<p>Det giver en lokal opskrift. Før den kan blive til en bygningsmængde, skal den kobles til de rigtige objekter og deres nettoareal; skelet, åbninger og lokale undtagelser skal behandles særskilt. [D6, PDF-side 1]</p>
<h2>Forskelle, som skal bevares</h2>'''+table(['Kilde','Oplysning','Konsekvens'],[
('T1 · Snit-B, PDF-side 1, 27.02.2017','320 mm ribbe og 265 mm isolering.','Kan ikke uden videre bruges på hele taget.'),
('T1 · Snit-A, PDF-side 2, 03.05.2017','340 mm ribbe og 290 mm isolering; desuden underpap Phønix PF3500.','Placering og revision skal afklares; ikke en global erstatning af side 1.'),
('Y2 · PDF-side 1 og 2','45 × 220 mm skelet og angivet 240 mm isolering.','Visuelt bekræftet forskel; må ikke rettes automatisk.')])+'''
<p>Konstruktionsdetaljerne tilføjer lokale limtræsdimensioner, stålprofiler, boltklasser og beslag. Facaderne angiver træbeklædning. Disse spor dokumenterer hverken træart, fugt, præcis EPD eller faktisk leveret produkt. Der er ikke fundet en eksplicit som-udført-erklæring i gennemgangen. [D1–D6]</p>''', 'Fra tegning til data'))

capability_rows = [
('Mængder og styktal','Delvist nu','Modeludtræk, materialetyper, nogle volumener og arealer.','Nettovolumen for flere kategorier, importkontrol og overlap.'),
('Vægt / materialemasse','Reference nu','CLI kan gange dokumenteret volumen og valgt densitet.','Projektgodkendt densitet, fugtgrundlag og fuld mængdedækning.'),
('Produktionsklima og øvrige GWP-moduler','Reference nu','CLI kan skalere én valgt GWP-observation og ét modul ad gangen.','Korrekt produkt/reference, mængdebasis og sammenlignelig metode.'),
('Samlet livscyklus for byggeriet','Uafklaret','Enkeltbidrag kan organiseres. Intet samlet resultat leveret.','Komplet omfang, areal, periode, drift, transport, udskiftninger og slutscenarier.'),
('Fugtbevægelse i råtræ','Metode findes','CLI har kildebaseret radial/tangential beregning i 6–14 % træfugt for valgte artskoefficienter.','Art, fiberretning, relevante emnemål og start/slutfugt. Metoden overføres ikke automatisk til CLT eller limtræ.'),
('Varmeledning og lagmodstand','Data-/metodeopgave','Lagtykkelser og kandidatdata kan findes.','Verificeret λ og geometri; beregningsmetode skal tilføjes og kontrolleres.'),
('U-værdi og bygningens varmebehov','Data-/metodeopgave','Enkle lag er et grundlag, ikke et færdigt resultat.','Skeletandel, kuldebroer, vinduer, samlinger, ventilation, klima og driftsforhold.'),
('Fugttransport, kondens og udtørring','Data-/metodeopgave','Kilder kan beskrive μ/sd, sorption og vandoptag.','Komplet opbygning, tidsafhængigt klima, fugtkilder og valideret beregningsmodel.')]
pages.append(section('Hvilke beregninger åbner det for?', '''
<p>“Data findes” og “kan beregnes sikkert i vores CLI” er to forskellige trin. I dag er masse, modulvis GWP-skalering og en afgrænset metode til træfugt implementeret. De øvrige muligheder kræver også beregningsmetoder og validering.</p>'''+table(['Område','Parathed','Det nuværende grundlag','Hvad mangler'],capability_rows)+'''
<p class="caption">Parathed beskriver dette projekt og den nuværende værktøjskæde. En række egenskaber i databasen er generiske eller stammer fra andre produkter/geografier og skal vælges udtrykkeligt. [M3], [M5]</p>''', 'Beregningsmuligheder · 1 af 2'))

pages.append(section('Bredere end CO₂ og træ', table(['Område','Muligt udbytte','Nødvendigt grundlag og metode'],[
('Andre miljøpåvirkninger','Eksempelvis ressourceforbrug, vand, affald, forsuring og næringsstofbelastning.','Samme indikator/metode, modul og referencegrundlag. Nye beregningsfunktioner ud over den nuværende GWP-skalering.'),
('Styrke, stivhed og deformation','Kontrollere bæreevne, nedbøjning, krybning og forbindelser.','Laster, understøtninger, tværsnit, dokumenterede egenskaber, samlinger og sikkerhedsgrundlag. Materialenavne alene er utilstrækkelige.'),
('Brand','Undersøge dokumenterede egenskaber for materialer og hele opbygninger.','Klassifikation/prøvning, beklædning, samlinger, eksponering og en fagligt egnet brandmodel. Lokal REI-tekst er ikke en samlet brandkontrol.'),
('Akustik','Undersøge luftlyd, trinlyd og absorption.','Dokumenterede lag og samlinger, masse, flanker, rum og prøvningsdata. Materialevægt kan ikke alene afgøre lydisolation.'),
('Indeklima og sundhed','Vurdere emissionsoplysninger og andre dokumenterede produktforhold.','Præcis vare, prøvningsbetingelser, eksponering og ventilationsgrundlag. En EPD er ikke i sig selv dokumentation for alle sundhedsforhold.'),
('Anlægspris og livscyklusøkonomi','Mængdebaseret prisoverslag, drift og udskiftninger.','Daterede priser, arbejdsløn, spild, levetider, vedligehold og økonomiske antagelser.'),
('Genbrug og demontering','Materialepas og oversigt over dele, som kan bevares eller udskiftes.','Tilstand, restlevetid, samlingsprincipper, adgang, forurening og faktisk demonterbarhed.'),
('Alternativer og optimering','Sammenligne materialer og løsninger på samme funktionelle grundlag.','Ens krav til styrke, varme, brand, lyd, levetid og beregningsomfang; en billig CO₂-værdi er ikke en ækvivalent løsning.')])+'''
<div class="callout">AI-agenten kan samle kilder, foreslå koblinger, køre de implementerede beregninger og forklare mangler. Den skal bevare antagelser og usikkerheder i resultatet. Nye faglige beregningsmodeller skal implementeres og verificeres, før agenten må bruge dem til projektkonklusioner.</div>
<p class="caption">Mulighedskataloget er en udviklingsretning. Disse øvrige analyser er ikke udført for Lisbjerg Bakke i denne rapport.</p>''', 'Beregningsmuligheder · 2 af 2'))

pages.append(section('De oplysninger, der giver mest værdi', '''
<p class="lead">Start med mængder, modelafstemning og materialekort. De tre ting afgør, om flere databasedata faktisk kan bruges på Lisbjerg Bakke.</p>'''+table(['Rækkefølge','Konkret leverance','Ansvar og effekt'],[
('1 · Afstem grundlaget','En liste over udførte revisioner og hvilke modeldele/blokke der indgår. Koordinater og ejerskab for mængder mellem ARK/KON.','Modelansvarlig og projekterende. Åbner for konsistente summer uden dobbeltregning.'),
('2 · Luk import- og mængdehuller','En gennemgået liste over udeladte objekter; verificerede nettomængder for vægge, bjælker, søjler, fundamenter, vinduer og øvrige kategorier.','Udvikler + BIM-ansvarlig. Flere originaldata kan måske udstilles; nogle mængdemetoder kræver udvikling.'),
('3 · Godkend materialekort','Én dokumenteret kobling pr. type/GUID: produkt, sammensætning, densitet, EPD/reference, kilde og gyldighed.','Projekterende og leverandører. Åbner for sporbar vægt og miljøberegning.'),
('4 · Bind tegninger til objekter','Y1/Y2/T1 og andre lokale detaljer knyttet til modelobjekter, med revisionsvalg og undtagelser.','Projekterende. Åbner for lagvise mængder og flere bygningsfysiske beregninger.'),
('5 · Definér den ønskede analyse','Areal, periode, afgrænsning, drifts-/slutscenarier og faglige randbetingelser.','LCA-ansvarlig, bygherre og relevante specialister. Åbner for sammenlignelige livscyklus- og funktionsanalyser.')])+'''
<h2>Et lille materialekort kan låse meget op</h2>
<div class="schema">Model + kontrolsum → GUID/type → placering og revision<br>→ produkt og materialesammensætning → mængde og enhed<br>→ densitet / EPD / øvrig egenskab + kilde og betingelser<br>→ godkendt kobling eller synligt referencescenarie</div>
<p>Den vedlagte mangelliste har 14 konkrete opgaver med prioritet, ansvar, det manglende input og den beregning, det åbner for. Den skelner også mellem manglende projektdata og manglende implementering i værktøjet. [M6]</p>''', 'Prioriteret handlingsliste'))

source_rows=[
('[F1] ARK-model.ifc','Original i Lisbjerg-pakken; SHA-256 nedenfor.','Arkitektmodel, IFC2X3.'),
('[F2] KON-model.ifc','Original i Lisbjerg-pakken; SHA-256 nedenfor.','Konstruktionsmodel, IFC2X3.'),
('[D1] etagekryds.pdf','2 sider.','Lokale arkitektdetaljer.'),
('[D2] etageplaner.pdf','17 sider.','Planer og revisionskontekst.'),
('[D3] facader.pdf','5 sider.','Facader og materialeforklaringer.'),
('[D4] konstruktionsdetaljer.pdf','48 sider.','Profiler, samlinger og befæstelser.'),
('[D5] situationsplan.pdf','1 side.','Situationsplan; rasterkontrolleret.'),
('[D6] tværsnit og kassettedetaljer.pdf','59 sider.','Lokale snit og lagopbygninger.'),
('[R1] BR18 tabel 7 · 2025','B1433, Sheet1!E25 og K25:L25.','Kun den udtrykkeligt valgte betonreference.')]
pages.append(section('Kilder og efterprøvelse', '''
<p>Projektmaterialet stammer fra <a href="https://opensource.vandkunsten.com/07_FBABLisbjerg/">Vandkunstens åbne Lisbjerg-side</a> og den arkiverede <a href="https://opensource.vandkunsten.com/07_FBABLisbjerg/VK_FBABLisbjerg.zip">originale Lisbjerg-pakke</a>. Originaler er bevaret lokalt; modellen blev åbnet uden at gemme ændringer.</p>'''+table(['Kilde','Omfang / lokation','Anvendelse'],source_rows)+f'''
<h2>Kontrolsummer for de to modeller</h2>
<p class="hash">ARK: {ark['sha256']}<br>KON: {kon['sha256']}</p>
<p>Referencefil [R1]: <a href="https://www.bygningsreglementet.dk/media/1o1nnozd/tabel-7-2025.xlsx">tabel-7-2025.xlsx</a>, hentet 17.11.2026. Lokal original: <code>data/raw/br18/table-7-2025.xlsx</code> i projektet. SHA-256: <span class="hash">3ac0babdd803cc688e058c9b1096c9871c849362014d4da80564000b73bcdb18</span>. Cellernes værdier er skaleret via den eksisterende materialeberegnings-CLI.</p>
<p class="caption">Filernes fulde lokale stier, PDF-kontrolsummer, sidetal og evidens findes i dossieret. Tegninger fra 2016–2017 og senere PDF-samlingsdatoer er bevaret uden at sidestille dem med som-udført-status.</p>''', 'Kilder · 1 af 2'))

pages.append(section('Det tekniske dossier', table(['Reference','Fil / mappe under reports/lisbjerg-bakke','Indhold'],[
('[M1] Originalinventar','raw/ifc-source-audit/results/','Alle originale produkt-ID’er, GlobalId, materialer, lag, profiler, egenskaber og relationer. Ingen geometri blev skabt eller beregnet af parseren.'),
('[M2] BIMcraft-udtræk','data/ark-normalized.json og kon-normalized.json','Komplet pagineret udtræk, kommandoer, modelhash, importadvarsler, flytninger og mængder.'),
('[M3] Materialevurdering','data/material-candidates.json og material-readiness.md','Kandidatdata, familiespecifikke mangler og kildehenvisninger.'),
('[M4] CLI-kontrol','raw/cli-quantity-summary.json og cli-findings.md','Undersøgte felter og programforudsætninger; originalt CLI-katalog gemt særskilt.'),
('[M5] Metoder','../../docs/CALCULATIONS.md','Eksisterende metoder for masse, modulvis GWP og træfugt samt begrænsninger.'),
('[M6] Mangler','data/missing-data.csv og missing-data.json','14 opgaver med prioritet, ansvar, databehov og effekt.'),
('Elementoversigt','data/element-inventory.csv','5.149 kildeelementer ekskl. åbninger. Hver række kan spores til originalens STEP-id og GUID; ingen tværgående mængdesum.'),
('Tegningsevidens','raw/drawing-evidence.json og drawing-findings.md','Fund med originalfil, SHA-256, 1-baseret PDF-side, observationsmetode og usikkerhed.'),
('Referencescenarie','data/concrete-reference-*.json','20 GUID’er, mængder, antagelser, requests og uændrede CLI-beregningssvar.'),
('Samlet resultat','data/summary.json og manifest.json','Maskinlæsbare hovedtal, kildekontrol og dossierets filkontrolsummer.')])+'''
<h2>Sådan blev det kontrolleret</h2>
<p>BIMcraft CLI 0.12.0 blev kørt på begge originaler med <code>inspect</code> og alle sider af <code>elements</code>. Originalerne blev analyseret semantisk med IfcOpenShell 0.9.0.post1 i et isoleret miljø; ingen geometri- eller CAD-motor blev kaldt af parseren. Kilde-GUID’er blev koblet til importens UUID’er.</p>
<p>De to originale IFC-filers kontrolsummer er uændrede. Den semantiske kontrol omfatter 6.067 produkter og GUID-roundtrips. Adapteren er rettet til også at bevare importens udeladelser og generiske repræsentationer, selv når modelinspektionens advarselsliste er tom. Alle 41 eksisterende og nye relevante tests bestod.</p>
<p class="caption">Kommandoer og reproduktion står i README.md. Ingen Solidcraft-model blev skabt i denne undersøgelse; originalerne er BIM-modeller, så mængdeafprøvningen er udført gennem BIMcraft. Resultaterne gælder de arkiverede filer og de dokumenterede værktøjsversioner.</p>''', 'Metode og bilag · 2 af 2'))

css='''
body{font-size:9.3pt;line-height:1.43}h1{font-size:25pt}h2{font-size:14pt;margin-top:1em}p{margin-bottom:.7em}
.report-page{break-before:page}.report-page>.eyebrow{margin-bottom:5mm}.report-page>h1{margin-bottom:6mm}
.cover{display:block;min-height:230mm;page:auto}.cover h1{font-size:35pt;margin-top:5mm}.cover .subtitle{max-width:none;font-size:12pt}
.cover .meta{margin-top:8mm;padding-top:0}.hero{width:100%;height:89mm;object-fit:cover;margin-top:7mm}
.caption{font-size:7.6pt;color:#68665e;line-height:1.4;margin-top:2mm}.lead{font-size:11.5pt;line-height:1.5}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:4mm;margin:6mm 0}.metrics>div{padding:4mm;background:#eef1e9}.metrics b{display:block;font-family:var(--font-serif);font-size:26pt;color:var(--color-accent)}.metrics span{font-size:8.5pt}
table{width:100%;font-size:8.3pt;line-height:1.38;border-collapse:collapse;margin:4mm 0;break-inside:auto}thead{display:table-header-group}th{text-align:left;font-weight:600;background:#eaf0e8;color:#2c4a3e}th,td{padding:2.5mm 2mm;border-bottom:1px solid #dddcd3;vertical-align:top}tr{break-inside:avoid}td:first-child{font-weight:500}li{margin-bottom:2mm}ul,ol{padding-left:5mm;margin-bottom:4mm}
.callout{background:#eef1e9;border-left:3px solid #2c4a3e;padding:4mm;margin:5mm 0;break-inside:avoid}.scenario{background:#f6efe1;border-color:#957440}
.label{font-weight:600;color:#2c4a3e}.formula{padding:4mm 5mm;margin:3mm 0;background:#eef1e9;font-size:12pt}.formula b{font-size:18pt;font-family:var(--font-serif)}.schema{padding:5mm;background:#eef1e9;line-height:1.8;font-size:10pt}.hash{font-family:monospace;font-size:6.7pt;overflow-wrap:anywhere}code{font-size:8pt;overflow-wrap:anywhere}
@media screen{.pagedjs_pages{display:flex;flex-direction:column;align-items:center;background:#e8e7e1}.pagedjs_page{background:#fdfbf7;margin:12px 0;box-shadow:0 2px 15px #0002}}
'''
document='''<!doctype html><html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lisbjerg Bakke — hvad kan vi beregne?</title><link rel="stylesheet" href="assets/rapport.css"><style>'''+css+'''</style><script>window.PagedConfig={auto:false};</script><script src="assets/paged.polyfill.js"></script></head><body>'''+''.join(pages)+'''<script>(async()=>{await document.fonts.ready;await Promise.all(Array.from(document.images).map(i=>i.complete?Promise.resolve():new Promise(r=>{i.onload=r;i.onerror=r})));await window.PagedPolyfill.preview();window.PagedPolyfill.ready=true;window.reportReady=true;})();</script></body></html>'''
(HERE/'rapport.html').write_text(document)
assert len(element_rows) == 5149
assert ark['source_physical_elements_matched_to_import'] == 2555
assert kon['source_physical_elements_matched_to_import'] == 2206
assert abs(mass['value']-471006.414) < 1e-6
assert abs(climate['value']-50539.869) < 1e-6
print('Wrote report HTML, summary, 5149-row element CSV and 14-item gap registry.')
