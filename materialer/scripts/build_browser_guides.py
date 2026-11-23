#!/usr/bin/env python3
"""Publish two existing reading examples on Pages, without a GitHub file view."""
import argparse
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs'
CASE = ROOT / 'materialer/examples/integrated-workflow'
REPO = 'https://github.com/FremtidensTegnestue/open-source/blob/main/'


def page(title, intro, content):
    return f'''<!doctype html>
<html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'self'; form-action 'self'">
<title>{escape(title)} — Fremtidens Tegnestue</title><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="style.css"></head>
<body><a class="skip" href="#indhold">Gå til indhold</a>
<header class="header wrap"><a class="brand" href="./"><img src="favicon.svg" width="40" height="40" alt=""><span class="brand-name">Fremtidens Tegnestue</span><span class="brand-sub">Åbne værktøjer</span></a>
<nav aria-label="Hovedmenu"><a href="./">Til forsiden</a><a href="./#materialer">Materialer</a><a href="./#boeger">Fagbøger</a></nav></header>
<main id="indhold" class="guide wrap"><p class="eyebrow">Læs direkte i browseren</p><h1>{escape(title)}</h1><p class="lead">{intro}</p>
{content}
</main><footer class="footer wrap"><a href="./">Tilbage til alle opgaver</a><p class="muted">Fremtidens Tegnestue. Vores egne tekster og kode er åbne; kildernes egne vilkår følger materialet.</p></footer></body></html>
'''


def number(value):
    return format(value, 'f').rstrip('0').rstrip('.').replace('.', ',') if '.' in format(value, 'f') else format(value, 'f')


def references():
    result = {}
    verification = json.loads((CASE / 'verification.json').read_text())
    if verification['status'] != 'passed':
        raise ValueError('The recorded example does not have passed status')
    for key in ['base', 'revised']:
        rows = json.loads((CASE / key / 'independent-reference.json').read_text(), parse_float=Decimal)
        if set(rows) != {'ConcretePanel', 'Rail_A', 'Rail_B'}:
            raise ValueError('Unexpected example parts')
        expected_thickness = {'base': 100, 'revised': 120}[key]
        if verification[key]['thickness_mm'] != expected_thickness:
            raise ValueError('The reading page expects the recorded 100/120 mm example')
        area = Decimal('1.5') * Decimal('1.0') - Decimal('0.3') * Decimal('0.2')
        if rows['ConcretePanel']['volume_m3'] != area * expected_thickness / 1000:
            raise ValueError('Recorded concrete quantity does not match the explained net geometry')
        for part, row in rows.items():
            if part != 'ConcretePanel' and row['volume_m3'] != Decimal('0.0008'):
                raise ValueError('Recorded rail quantity does not match the explained geometry')
            density = Decimal('2246') if part == 'ConcretePanel' else Decimal('7850')
            if row['mass_kg'] != row['volume_m3'] * density:
                raise ValueError('Recorded mass does not match the density in the explanation')
            climate = row['volume_m3'] * 241 if part == 'ConcretePanel' else row['mass_kg'] / 1000 * 1639
            if row['gwp_A1_A3_kg_CO2eq'] != climate:
                raise ValueError('Recorded climate does not match the explained reference unit')
        result[key] = {
            'volume': rows['ConcretePanel']['volume_m3'],
            'mass': sum(row['mass_kg'] for row in rows.values()),
            'climate': sum(row['gwp_A1_A3_kg_CO2eq'] for row in rows.values()),
        }
    return result, verification


def build():
    original = (ROOT / 'transformation-og-genbrug/fagordbog/vindue/ark.html').read_text()
    fragment = original[original.index('<section class="sheet"'):]
    if fragment.count('<section class="sheet"') != 3 or len(re.findall(r'id="ord-\d+"', fragment)) != 10:
        raise ValueError('Unexpected window sheet structure')
    if re.search(r'<(?:script|iframe|object)\b|\son\w+\s*=', fragment, re.I):
        raise ValueError('The window reading page must not contain active embedded content')
    if any(not url.startswith(('#', 'https://')) for url in re.findall(r'href="([^"]+)"', fragment)):
        raise ValueError('Unexpected window link protocol')
    fragment = fragment.replace('<h1>Vinduet</h1>', '')
    fragment = re.sub(r'<header>[^<]+</header>', '', fragment)
    terms = ['Karm', 'Ramme', 'Post', 'Sprosse', 'Bundstykke', 'Sålbænk', 'Forsatsramme', 'Fals', 'Kitfals', 'Glasliste']
    index = '<nav class="term-links" aria-label="Find en del på vinduet">' + ''.join(f'<a href="#ord-{i}">{i} · {word}</a>' for i, word in enumerate(terms, 1)) + '</nav>'
    window = page('Forstå delene i et vindue', 'Se tegningen, vælg en del og læs forklaringen. De samme ord gør det lettere at beskrive et vindue og tale om, hvad der kan undersøges eller bevares.',
        '<p class="reference-note">Illustrerede principper uden mål. Tegningerne forklarer bygningsdele; de er ikke et udførelses- eller dimensioneringsgrundlag.</p>' + index + fragment +
        f'<p class="guide-source">Tegninger og forklaringer er gengivet fra vores illustrerede fagordbog. <a href="{REPO}transformation-og-genbrug/fagordbog/vindue/ark.pdf?raw=true">Hent vinduesarket som PDF</a>. Originalkilderne står ved hver forklaring. <a href="./#boeger">Find hele fagordbogen</a>.</p>')
    values, verification = references()
    rows = ''.join(f'<tr><th scope="row">{label}</th><td>{number(values["base"][key])} {unit}</td><td>{number(values["revised"][key])} {unit}</td></tr>' for key, label, unit in [
        ('volume', 'Betonens nettovolumen', 'm³'), ('mass', 'Samlet masse, alle tre dele', 'kg'), ('climate', 'Klima fra produktionen · A1–A3', 'kg CO₂e')])
    added_mass = values['revised']['mass'] - values['base']['mass']
    added_climate = values['revised']['climate'] - values['base']['climate']
    case_content = '<nav class="term-links" aria-label="Find rundt i regneeksemplet"><a href="#forskel">Se forskellen</a><a href="#regnestykke">Følg regnestykket</a><a href="#kilder">Kilder</a></nav>' + f'''<figure class="case-figure"><img src="assets/betonplade.png" alt="Den reviderede model: en betonplade med en gennemgående rektangulær udsparing og to stålskinner på oversiden." width="900"><figcaption>Den faktiske model fra det dokumenterede forsøg. Pladen er her 120 mm tyk.</figcaption></figure>
<section><h2>Begynd med ét valg</h2><p>En betonplade gøres tykkere: fra 100 til 120 mm. Pladens længde og bredde er de samme, og de to stålskinner ændrer ikke størrelse. Hvad betyder det for mængder, masse og produktionsklima?</p>
<p>Det er et gemt, kontrolleret regneeksempel. Du kan læse det uden at installere modelprogrammer eller beregningsværktøjer.</p></section>
<section id="forskel"><h2>Se forskellen</h2><div class="raw-wrap" tabindex="0" role="region" aria-label="Sammenligning af den oprindelige og tykkere plade"><table class="raw-table"><caption>Samme model og materialereferencer før og efter ændringen.</caption><thead><tr><th scope="col">Det, vi undersøger</th><th scope="col">100 mm plade</th><th scope="col">120 mm plade</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="reference-note">Ændringen giver <strong>{number(added_mass)} kg mere masse</strong> og <strong>{number(added_climate)} kg CO₂e mere fra produktionen</strong> i dette eksempel.</p></section>
<section id="regnestykke"><h2>Følg regnestykket</h2><ol class="reading-steps"><li><h3>Find den faktiske mængde</h3><p>Pladen er 1,5 × 1,0 m. Udsparingen er 0,3 × 0,2 m og trækkes fra, før arealet ganges med tykkelsen:</p><p class="calculation">(1,5 × 1,0 − 0,3 × 0,2) × 0,100 = 0,144 m³ beton.</p><p>Ved 120 mm bliver den sidste faktor 0,120 m, og mængden bliver 0,1728 m³. De to skinner er hver 1,0 × 0,08 × 0,01 m, i alt 0,0016 m³ stål.</p></li>
<li><h3>Brug det rigtige referencegrundlag</h3><p>Den valgte betonreference har en densitet på 2.246 kg/m³ og et produktionsbidrag på 241 kg CO₂e pr. m³. Stålreferencen har en densitet på 7.850 kg/m³, men klimatallet er 1.639 kg CO₂e <strong>pr. ton</strong>. Stålets masse omregnes derfor til ton, før klimatallet bruges.</p><p>Kildevalgene er generiske referencer fra BR18 tabel 7, 2025. De dokumenterer ikke bestemte leverede produkter.</p></li>
<li><h3>Hold resultatets omfang tydeligt</h3><p>Tabellen summerer de tre deles produktion i den samme klimafase, A1–A3. Transport, montage, drift, vedligehold, udskiftning og slutbehandling indgår ikke. Resultatet er en del af et klimaregnskab.</p></li></ol></section>
<section><h2>Hvad kan du bruge eksemplet til?</h2><p>Se, hvordan et ændret mål følger videre til mængde, masse og klimabidrag. Brug samme spørgsmål til dit eget projekt: Er mængden netto? Hvad gælder kildens tal for? Hvilke faser og materialer mangler?</p><p>Forsøget undersøger mængder og dataoverførsel. Skinnerne er mængdeprøver; det er ikke dokumentation for bæreevne eller for, at denne konstruktion kan udføres.</p></section>
<section id="kilder" class="guide-source"><h2>Kilder og efterprøvelse</h2><p>Originale materialetal: <a href="https://www.bygningsreglementet.dk/media/1o1nnozd/tabel-7-2025.xlsx">BR18 tabel 7, 2025 (Excel)</a>, beton på række 25 og stål på række 129. Kontrol af de viste resultater er bevaret i <a href="{REPO}materialer/examples/integrated-workflow/README.md">det dokumenterede model- og beregningsforsøg på GitHub</a>.</p><p>Forsøgets gemte kontrol er dateret {escape(verification['checked_at'][:10])}. Denne læseside gengiver de gemte resultater; den kører ikke modeller eller en ny beregning, når du åbner den.</p><p><a href="./#materialer">Undersøg selv en materialereference</a> eller <a href="./#boeger">find mere læsestof</a>.</p></section>'''
    return {'vinduet.html': window.encode(), 'regneeksempel.html': page('Hvad gør en tykkere plade ved klimatallet?', 'Følg ét konkret valg fra modelmål til materialemængde, masse og produktionsklima. Tallene er fra vores dokumenterede beton- og ståleksempel.', case_content).encode(), 'assets/betonplade.png': (CASE / 'revised/model.png').read_bytes()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = build()
    for name, contents in files.items():
        target = DOCS / name
        if args.check:
            if not target.exists() or target.read_bytes() != contents:
                raise SystemExit(f'Not current: {target.relative_to(ROOT)}')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
    print(f'{len(files)} source-bound reading files {"checked" if args.check else "written"}')


if __name__ == '__main__':
    main()
