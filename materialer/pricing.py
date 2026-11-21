"""Supplier observations and VAT-exclusive project budgets. No CAD writes or purchases."""
import argparse
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP
import hashlib
import html
import io
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from report_io import write_report

UNITS = {'m2', 'm3', 'm', 'stk', 'kg', 'L', 'job'}
MAX_BYTES = 10 * 1024 * 1024


def number(value, positive=False):
    if isinstance(value, bool):
        raise ValueError('Boolean er ikke et beløb eller en mængde')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Ugyldigt tal') from exc
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError('Tal skal være endelige og ikke-negative; enheder skal være positive')
    return result


def cash(value):
    return format(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP), '.2f')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(record, key):
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{key} mangler')
    return value


def iso_day(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError('Dato skal være YYYY-MM-DD')
    return date.fromisoformat(value)


def normalize_offer(raw):
    """Never infer identity, VAT, discounts or pack size from a product name."""
    r = dict(raw)
    for key in ('supplier_id', 'supplier_name', 'account_id', 'sku', 'product_id',
                'mapping_reference', 'observed_on', 'review_on'):
        identifier(r, key)
    if r.get('currency') != 'DKK' or r.get('unit') not in UNITS:
        raise ValueError('Kun DKK og eksplicit understøttet fysisk enhed')
    if r.get('kind') not in ('budget_reference', 'quote', 'test', 'estimate'):
        raise ValueError('Ukendt priskildetype')
    if r.get('origin') not in ('nyt', 'genbrug', 'eksisterende'):
        raise ValueError('Oprindelse skal angives')
    if r.get('availability') not in ('available', 'unknown', 'unavailable', 'quote_required'):
        raise ValueError('Tilgængelighed skal angives')
    observed, review = iso_day(r['observed_on']), iso_day(r['review_on'])
    if review < observed:
        raise ValueError('Kontroldato før prisobservation')
    if r.get('valid_until'):
        if iso_day(r['valid_until']) < observed:
            raise ValueError('Gyldighed slutter før prisobservation')
    amount = number(r['amount'])
    tax = r.get('tax_basis')
    if tax == 'incl_vat':
        rate = number(r.get('vat_rate'))
        if rate > 1:
            raise ValueError('Momssats angives som andel, fx 0.25')
        amount /= 1 + rate
    elif tax != 'excl_vat':
        raise ValueError('Ukendt momsgrundlag')
    discount = r.get('discount_percent')
    if r.get('price_basis') == 'list':
        identifier(r, 'discount_reference')
        discount = number(discount)
        if discount > 100:
            raise ValueError('Rabat skal være 0–100 procent')
        amount *= 1 - discount / 100
    elif r.get('price_basis') != 'net' or discount not in (None, '', 0, '0'):
        raise ValueError('Nettopris må ikke få rabat igen; listepris kræver rabatgrundlag')
    if r['kind'] == 'estimate':
        identifier(r, 'source_reference')
        if r.get('source_url'):
            https_url(r['source_url'])
    else:
        https_url(identifier(r, 'source_url'))
    for key in ('price_quantity', 'purchase_step'):
        number(r.get(key), positive=True)
    number(r.get('minimum_quantity'))
    # The raw observation and its own basis remain immutable alongside the net price.
    key = digest(json.dumps(r, sort_keys=True, ensure_ascii=False, allow_nan=False).encode())
    return {'id': key, 'raw': r, 'amount_excl_vat': str(amount)}


def import_bytes(raw, fmt, store_path, source, received_at=None):
    """Append observations, idempotently. File imports are observations, never deltas/deletes."""
    store_path = Path(store_path)
    if len(raw) > MAX_BYTES:
        raise ValueError('Prisfil er større end 10 MiB')
    text = raw.decode('utf-8-sig')
    if fmt == 'csv':
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('CSV-kolonnenavne mangler eller er dubleret')
        records = list(reader)
        if any(None in row for row in records):
            raise ValueError('CSV-række har ekstra værdier')
    elif fmt == 'json':
        payload = json.loads(text)
        if payload.get('schema') != 1 or payload.get('mode') != 'observations':
            raise ValueError('Brug schema=1/mode=observations; rå leverandør-delta kræver sin egen kontrakt')
        records = payload['offers']
    else:
        raise ValueError('Kun JSON og UTF-8 CSV')
    if not isinstance(records, list) or not records:
        raise ValueError('Tom prisfil aktiveres ikke')
    offers = [normalize_offer(row) for row in records]  # Validate the entire batch before writes.
    if any(Path(p).resolve() == store_path.resolve() for p in [source] if not str(p).startswith('https://')):
        raise ValueError('Lageret må ikke overskrive inputfilen')
    current = json.loads(store_path.read_text()) if store_path.exists() else {'schema': 1, 'offers': [], 'imports': []}
    if current.get('schema') != 1:
        raise ValueError('Ukendt lagerformat')
    file_hash = digest(raw)
    if any(x['sha256'] == file_hash for x in current['imports']):
        return {'added': 0, 'duplicate': True, 'sha256': file_hash}
    stamp = received_at or datetime.now(timezone.utc).isoformat()
    known = {o['id'] for o in current['offers']}
    added = 0
    for offer in offers:
        if offer['id'] not in known:
            offer.update(received_at=stamp, import_sha256=file_hash)
            current['offers'].append(offer)
            known.add(offer['id'])
            added += 1
    archive = store_path.parent / (store_path.stem + '-originals') / (file_hash + '.' + fmt)
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists() and archive.read_bytes() != raw:
        raise ValueError('Arkivkontrol fejlede')
    archive.write_bytes(raw)
    current['imports'].append({'sha256': file_hash, 'source': str(source), 'received_at': stamp,
                               'original': str(archive.resolve())})
    write_report(current, store_path, protected_paths=[archive])
    return {'added': added, 'duplicate': False, 'sha256': file_hash}


def https_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('Hentning kræver HTTPS uden loginoplysninger eller fragment i URL')
    return value


def fetch(url, fmt, store_path):
    """Fetch the documented interchange format, not arbitrary webshop HTML or private APIs."""
    https_url(url)
    request = Request(url, headers={'User-Agent': 'FT-PriceImport/1.0', 'Accept': 'application/json,text/csv'})
    with urlopen(request, timeout=20) as response:
        https_url(response.geturl())
        raw = response.read(MAX_BYTES + 1)
    return import_bytes(raw, fmt, store_path, url)


def current_offers(store, account_id, as_of, allow_test=False):
    latest = {}
    for source in store.get('imports', []):
        if digest(Path(source['original']).read_bytes()) != source['sha256']:
            raise ValueError('Original prisfil matcher ikke den gemte kontrolsum')
    for stored in store['offers']:
        checked = normalize_offer(stored['raw'])
        if checked['id'] != stored['id'] or checked['amount_excl_vat'] != stored['amount_excl_vat']:
            raise ValueError('Prisobservationens indhold matcher ikke kontrolsum/normalisering')
        r = stored['raw']
        if r['account_id'] not in ('public', account_id) or (r['kind'] == 'test' and not allow_test):
            continue
        if iso_day(r['observed_on']) > as_of:
            continue
        key = tuple(r[k] for k in ('supplier_id', 'account_id', 'sku', 'product_id', 'unit', 'origin'))
        order = (r['observed_on'], stored['received_at'], stored['id'])
        if key not in latest or order > latest[key][0]:
            latest[key] = (order, stored)
    # Check validity AFTER choosing latest: never resurrect an old price after withdrawal/expiry.
    return [o for _, o in latest.values()]


def cost_for(offer, quantity):
    r = offer['raw']
    if quantity == 0:
        units = Decimal(0)
    else:
        units = (max(quantity, number(r['minimum_quantity'])) / number(r['purchase_step'])).to_integral_value(rounding=ROUND_CEILING)
    purchase = units * number(r['purchase_step'])
    cost = purchase / number(r['price_quantity']) * number(offer['amount_excl_vat'])
    return purchase, cost



def delivery_climate(entry):
    value = entry.get('transport_kg_co2e') if entry else None
    if value is None:
        return None
    identifier(entry, 'climate_reference')
    return str(number(value))


def supplier_baskets(project, lines):
    """One-supplier proposals for the unordered scope; price coverage is not stock coverage."""
    pending = [row for row in lines if row['unordered_quantity'] is None or number(row['unordered_quantity']) > 0]
    suppliers = {o['supplier_id'] for row in pending for o in row['options'] if o['goods_excl_vat'] is not None}
    result = []
    for supplier in sorted(suppliers):
        goods, chosen, missing, skus, issues = Decimal(0), [], [], set(), []
        for row in pending:
            options = [o for o in row['options'] if o['supplier_id'] == supplier and o['goods_excl_vat'] is not None]
            if not options:
                missing.append(row['id'])
                continue
            option = options[0]  # Sorted price alternatives within the explicitly matched product.
            group = (option['account_id'], option['sku'])
            if group in skus:
                issues.append('Saml samme SKU før købsmængde beregnes')
            skus.add(group)
            chosen.append({'line_id': row['id'], **option})
            goods += number(option['goods_excl_vat'])
        entry = project.get('delivery', {}).get(supplier)
        shipping = None if not entry or entry.get('amount_excl_vat') is None else number(entry['amount_excl_vat'])
        if shipping is not None:
            identifier(entry, 'reference')
        transport = delivery_climate(entry)
        if shipping is None:
            issues.append('Levering/gebyrer mangler')
        if transport is None:
            issues.append('Leverandørspecifik transport-CO2 mangler')
        result.append({'supplier_id': supplier, 'supplier_name': chosen[0]['supplier_name'],
          'priced_lines': len(chosen), 'required_lines': len(pending), 'confirmed_available_lines': sum(o['availability'] == 'available' for o in chosen),
          'missing_line_ids': missing, 'offers': chosen, 'known_goods_excl_vat': cash(goods),
          'delivery_excl_vat': None if shipping is None else cash(shipping),
          'rest_purchase_total_excl_vat': None if missing or shipping is None or len(skus) != len(chosen) else cash(goods + shipping),
          'transport_kg_co2e': transport, 'issues': issues})
    result.sort(key=lambda x: (-x['priced_lines'], x['supplier_id']))
    return result



def assess_labor(entries, line_ids):
    result, ids = [], set()
    for item in entries:
        key = identifier(item, 'id')
        if key in ids:
            raise ValueError('Dubleret arbejdspost')
        ids.add(key)
        label = identifier(item, 'label')
        basis = item.get('rate_basis')
        if basis not in ('contractor_rate', 'employer_cost', 'gross_wage'):
            raise ValueError('Angiv faktureret timepris, samlet lønomkostning eller bruttotimeløn')
        linked = item.get('linked_line_ids', [])
        if set(linked) - line_ids:
            raise ValueError('Arbejdspost refererer til ukendt materialepost')
        hours = None if item.get('hours') is None else number(item['hours'])
        rate = None if item.get('hourly_rate') is None else number(item['hourly_rate'])
        addon = None if item.get('employer_addon_percent') is None else number(item['employer_addon_percent'])
        included = item.get('included_in_line_id')
        issues = []
        if included:
            if included not in line_ids:
                raise ValueError('Montage er angivet indeholdt i en ukendt post')
            identifier(item, 'reference')
        else:
            if hours is None: issues.append('Arbejdstimer mangler')
            if rate is None: issues.append('Timepris/løn mangler')
            if basis == 'gross_wage' and addon is None:
                issues.append('Arbejdsgiveromkostninger ud over bruttoløn mangler')
            if not issues:
                identifier(item, 'reference')
        effective_rate = None if rate is None else rate * (1 + (addon / 100 if basis == 'gross_wage' and addon is not None else 0))
        if basis == 'gross_wage' and addon is None:
            effective_rate = None
        cost = None if hours is None or effective_rate is None else cash(hours * effective_rate)
        additional = '0.00' if included else (None if issues else cost)
        result.append({'id':key, 'label':label, 'hours':None if hours is None else str(hours),
          'hourly_rate':None if rate is None else str(rate), 'rate_basis':basis,
          'employer_addon_percent':None if addon is None else str(addon),
          'effective_hourly_cost':None if effective_rate is None else str(effective_rate),
          'estimated_excl_vat':cost, 'additional_excl_vat':additional,
          'included_in_line_id':included, 'linked_line_ids':linked, 'reference':item.get('reference'), 'issues':issues})
    return result


def compare_reports(reference, variant):
    if any(reference[k] != variant[k] for k in ('scope_id', 'currency', 'tax_basis')):
        raise ValueError('Reference og variant skal have samme omfang/valuta/momsgrundlag')
    def costs(report):
        values = {('material', x['id']):None if x['issues'] else x['known_excl_vat'] for x in report['lines']}
        values.update({('labor', x['id']):x['additional_excl_vat'] for x in report['labor']})
        values.update({('delivery', x['supplier_id']):x['amount_excl_vat'] for x in report['delivery']})
        return values
    before, after = costs(reference), costs(variant)
    common = before.keys() & after.keys()
    matched = [{'category':k[0], 'id':k[1], 'before_excl_vat':before[k], 'after_excl_vat':after[k],
                'delta_excl_vat':cash(number(after[k])-number(before[k]))} for k in sorted(common)
               if before[k] is not None and after[k] is not None]
    whole_delta = None
    if {k for k in before if k[0] != 'delivery'} == {k for k in after if k[0] != 'delivery'} and reference['forecast_excl_vat'] is not None and variant['forecast_excl_vat'] is not None:
        whole_delta = cash(number(variant['forecast_excl_vat'])-number(reference['forecast_excl_vat']))
    return {'matched':matched,
      'newly_priced':[list(k) for k in sorted(common) if before[k] is None and after[k] is not None],
      'lost_prices':[list(k) for k in sorted(common) if before[k] is not None and after[k] is None],
      'scope_added':[list(k) for k in sorted(after.keys()-before.keys())],
      'scope_removed':[list(k) for k in sorted(before.keys()-after.keys())],
      'whole_forecast_delta_excl_vat':whole_delta,
      'note':'Nye prissatte poster og ændret omfang er adskilt fra prisændring. Budgetrammen ændres ikke af varianten.'}


def assess(project, store, as_of, allow_test=False):
    if project.get('schema') != 1 or project.get('currency') != 'DKK' or project.get('tax_basis') != 'excl_vat':
        raise ValueError('Projekt skal have schema=1 og DKK ekskl. moms')
    identifier(project, 'scope_id')
    account = identifier(project, 'account_id')
    offers = current_offers(store, account, as_of, allow_test)
    budget = project.get('budget')
    if budget:
        number(budget['amount_excl_vat'])
        identifier(budget, 'revision')
        iso_day(budget['set_on'])
    if not project.get('lines'):
        raise ValueError('Projektomfang må ikke være tomt')
    lines, ids, order_ids, suppliers = [], set(), set(), set()
    purchase_groups = set()
    known = Decimal(0)
    gaps = list(project.get('unresolved_scope', []))
    for item in project['lines']:
        key = identifier(item, 'id')
        if key in ids:
            raise ValueError('Dubleret projektpost')
        ids.add(key)
        if item.get('unit') not in UNITS:
            raise ValueError('Ukendt fysisk enhed i projektpost')
        row = {'id': key, 'label': identifier(item, 'label'), 'unit': item['unit'],
               'options': [], 'selected': None, 'issues': [], 'actual_excl_vat': '0.00',
               'committed_remaining_excl_vat': '0.00', 'estimated_unordered_excl_vat': None}
        net = item.get('net_quantity')
        required = None if net is None else number(net) * (1 + number(item['waste_rate']))
        accounted, actual, committed = Decimal(0), Decimal(0), Decimal(0)
        for order in item.get('orders', []):
            oid = identifier(order, 'id')
            if oid in order_ids:
                raise ValueError('Dubleret ordre; en ordre må ikke tælles flere steder')
            order_ids.add(oid)
            if order.get('price_fixed') is not True:
                raise ValueError('Variabel ordrepris skal afklares før den kan behandles som fast')
            identifier(order, 'reference')
            suppliers.add(identifier(order, 'supplier_id'))
            quantity, invoiced = number(order['quantity']), number(order['invoiced_quantity'])
            if invoiced > quantity:
                raise ValueError('Faktureret mængde overstiger ordremængde')
            accounted += quantity
            actual += number(order['invoiced_excl_vat'])
            if order.get('remaining_excl_vat') is None:
                row['issues'].append('Resterende ordrepris mangler')
            else:
                committed += number(order['remaining_excl_vat'])
        row.update(actual_excl_vat=cash(actual), committed_remaining_excl_vat=cash(committed))
        if required is None:
            row['issues'].append('Mængde mangler')
            remaining = None
        else:
            remaining = max(required - accounted, Decimal(0))
            if accounted > required:
                row['issues'].append('Aftalt mængde overstiger behov; afstem overskud/annullering')
        row.update(required_quantity=None if required is None else str(required),
                   unordered_quantity=None if remaining is None else str(remaining))
        matching = [o for o in offers if o['raw']['product_id'] == item.get('product_id')
                    and o['raw']['unit'] == item['unit'] and o['raw']['origin'] == item.get('origin')]
        for offer in matching:
            raw = offer['raw']
            issues = []
            if iso_day(raw['review_on']) < as_of or (raw.get('valid_until') and iso_day(raw['valid_until']) < as_of):
                issues.append('Pris skal opdateres')
            if raw['availability'] in ('unavailable', 'quote_required'):
                issues.append('Vare utilgængelig eller kræver tilbud')
            purchase, cost = (None, None) if remaining is None else cost_for(offer, remaining)
            option = {'offer_id': offer['id'], 'supplier_id': raw['supplier_id'], 'supplier_name': raw['supplier_name'],
                      'sku': raw['sku'], 'account_id': raw['account_id'], 'kind': raw['kind'], 'availability': raw['availability'],
                      'observed_on': raw['observed_on'], 'review_on': raw['review_on'], 'source_url': raw.get('source_url'),
                      'source_reference': raw.get('source_reference'),
                      'purchase_quantity': None if purchase is None else str(purchase),
                      'goods_excl_vat': None if cost is None or issues else cash(cost), 'issues': issues}
            row['options'].append(option)
        row['options'].sort(key=lambda o: (o['goods_excl_vat'] is None, number(o['goods_excl_vat']) if o['goods_excl_vat'] is not None else Decimal(0), o['offer_id']))
        selection = item.get('selection')
        selected = [o for o in row['options'] if selection and all(o[k] == selection.get(k) for k in ('supplier_id', 'account_id', 'sku'))]
        if len(selected) > 1:
            raise ValueError('Valg matcher flere prisobservationer')
        if remaining == 0:
            estimated = Decimal(0)
        elif selected and selected[0]['goods_excl_vat'] is not None:
            purchase_group = tuple(selected[0][k] for k in ('supplier_id', 'account_id', 'sku'))
            if purchase_group in purchase_groups:
                raise ValueError('Saml behovet for samme leverandørvare før pakker og mindstekøb beregnes')
            purchase_groups.add(purchase_group)
            row['selected'] = selected[0]
            estimated = number(selected[0]['goods_excl_vat'])
            suppliers.add(selected[0]['supplier_id'])
        else:
            estimated = None
            row['issues'].append('Valgt pris mangler eller er uafklaret')
        row['estimated_unordered_excl_vat'] = None if estimated is None else cash(estimated)
        row['known_excl_vat'] = cash(actual + committed + (estimated or Decimal(0)))
        known += number(row['known_excl_vat'])
        if row['issues']:
            gaps.append(item['label'] + ': ' + '; '.join(row['issues']))
        lines.append(row)
    labor = assess_labor(project.get('labor', []), ids)
    labor_known = sum((number(x['additional_excl_vat']) for x in labor if x['additional_excl_vat'] is not None), Decimal(0))
    known += labor_known
    for row in labor:
        if row['issues']: gaps.append(row['label']+': '+'; '.join(row['issues']))
    delivery = []
    for supplier in sorted(suppliers):
        entry = project.get('delivery', {}).get(supplier)
        if not entry or entry.get('amount_excl_vat') is None:
            gaps.append(supplier + ': samlet levering/gebyrer mangler')
            delivery.append({**(entry or {}), 'supplier_id': supplier, 'amount_excl_vat': None})
        else:
            identifier(entry, 'reference')
            known += number(entry['amount_excl_vat'])
            delivery.append({'supplier_id': supplier, **entry})
    transport_values = [delivery_climate(d) for d in delivery]
    known_transport = sum((number(v) for v in transport_values if v is not None), Decimal(0))
    unknown_suppliers = any((row['unordered_quantity'] is None or number(row['unordered_quantity']) > 0) and row['selected'] is None for row in lines)
    transport_total = None if unknown_suppliers or any(v is None for v in transport_values) else str(known_transport)
    complete = not gaps
    total = known if complete else None
    budget_amount = None if not budget else number(budget['amount_excl_vat'])
    return {'schema': 1, 'scope_id': project['scope_id'], 'as_of': str(as_of), 'currency': 'DKK', 'tax_basis': 'excl_vat',
            'test_mode': allow_test, 'status': 'complete_for_declared_scope' if complete else 'partial_budget',
            'lines': lines, 'labor':labor, 'known_labor_excl_vat':cash(labor_known), 'delivery': delivery, 'supplier_baskets': supplier_baskets(project, lines),
            'purchasing_priority': 'Saml så mange passende varer som muligt hos én leverandør; sammenlign pris og CO2 før valg',
            'delivery_transport_kg_co2e': transport_total, 'delivery_transport_known_kg_co2e': str(known_transport),
            'climate_status': 'transport_missing' if transport_total is None else 'transport_scenario_only', 'unresolved': gaps, 'known_subtotal_excl_vat': cash(known),
            'forecast_excl_vat': None if total is None else cash(total), 'budget': budget,
            'variance_excl_vat': None if total is None or budget_amount is None else cash(total - budget_amount),
            'budget_status': 'not_set' if budget_amount is None else ('known_cost_above_budget' if known > budget_amount else ('within_budget' if complete else 'unresolved')),
            'note': 'Prioritér samlet indkøb før supplerende køb. Prisreferencedækning er ikke lagerbekræftelse. Varepris, samlet levering og CO2 vurderes særskilt; ingen automatisk vinder eller produktændring.'}



def render_comparison(comparison):
    if not comparison:
        return ''
    e = html.escape
    change = 'Uafklaret på grund af manglende poster' if comparison['whole_forecast_delta_excl_vat'] is None else e(comparison['whole_forecast_delta_excl_vat'])+' kr. ekskl. moms'
    rows = ''.join('<tr><td>'+e(x['category']+': '+x['id'])+'</td><td>'+e(x['before_excl_vat'])+'</td><td>'+e(x['after_excl_vat'])+'</td><td>'+e(x['delta_excl_vat'])+'</td></tr>' for x in comparison['matched'])
    return '<h2>Reference → variant</h2><p>Samlet ændring: <b>'+change+'</b>. Nye prissatte poster: '+str(len(comparison['newly_priced']))+'. Poster som har mistet pris: '+str(len(comparison['lost_prices']))+'.</p><details><summary>Se forskelle på sammenlignelige poster</summary><table><tr><th>Post</th><th>Reference</th><th>Variant</th><th>Forskel</th></tr>'+rows+'</table><p>'+e(comparison['note'])+'</p></details>'


def render(report):
    e = lambda value: html.escape(str(value))
    def fmt(value):
        return 'Uafklaret' if value is None else f'{Decimal(str(value)):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    availability = {'available':'Tilgængelig ifølge kilde', 'unknown':'Lagerstatus uafklaret', 'unavailable':'Utilgængelig', 'quote_required':'Kræver tilbud'}
    rows = []
    for line in report['lines']:
        options = []
        for o in line['options']:
            chosen = line['selected'] and line['selected']['offer_id'] == o['offer_id']
            cost = 'Uafklaret' if o['goods_excl_vat'] is None else fmt(o['goods_excl_vat']) + ' kr.'
            label = {'test':'TESTDATA','quote':'Tilbud','estimate':'Eget overslag'}.get(o['kind'],'Budgetreference')
            source = f"<a href='{e(o['source_url'])}'>Kilde</a>" if o.get('source_url') else e(o.get('source_reference') or 'Kilde mangler')
            options.append(f"<li><b>{e(o['supplier_name'])}</b> {'· Valgt' if chosen else ''}: {cost} · {label}<br><small>Indkøb: {fmt(o['purchase_quantity'])} {e(line['unit'])} · Pris observeret {e(o['observed_on'])} · {e(availability[o['availability']])} · {source} {e('; '.join(o['issues']))}</small></li>")
        rows.append(f"<tr><td><b>{e(line['label'])}</b><br><small>Behov inkl. tillæg: {fmt(line['required_quantity'])} {e(line['unit'])}<br>Ikke bestilt: {fmt(line['unordered_quantity'])}</small></td><td><ul>{''.join(options) or '<li>Ingen sammenlignelig pris</li>'}</ul></td><td>{fmt(line['actual_excl_vat'])} kr.</td><td>{fmt(line['committed_remaining_excl_vat'])} kr.</td><td>{fmt(line['estimated_unordered_excl_vat']) if line['estimated_unordered_excl_vat'] is not None else 'Mangler'} kr.</td></tr>")
    rate_labels = {'contractor_rate':'Faktureret timepris ekskl. moms', 'employer_cost':'Samlet lønomkostning', 'gross_wage':'Bruttotimeløn med angivne tillæg'}
    labor_rows = ''.join(f"<tr><td>{e(x['label'])}</td><td>{fmt(x['hours'])}</td><td>{fmt(x['hourly_rate'])} kr.<br><small>{e(rate_labels[x['rate_basis']])}</small></td><td>{fmt(x['additional_excl_vat'])} kr.<br><small>{'Indeholdt i '+e(x['included_in_line_id']) if x['included_in_line_id'] else e('; '.join(x['issues']))}</small></td></tr>" for x in report['labor'])
    labor_table = '<h2>Arbejdstimer og løn</h2><p>Kendt særskilt arbejdsomkostning: '+fmt(report['known_labor_excl_vat'])+' kr. Faktureret timepris og bruttoløn er forskellige grundlag. Angivne timer er et overslag, ikke en tidsplan eller en løn-/fakturaafstemning. Timer giver ikke i sig selv et CO₂tal.</p><div class="scroll"><table><tr><th>Arbejde</th><th>Persontimer</th><th>Prisgrundlag pr. persontime</th><th>Særskilt tillæg til regnskabet</th></tr>'+labor_rows+'</table></div>' if report['labor'] else ''
    context = report.get('climate_context')
    climate_context = '' if not context else '<h2>Klima følger samme model</h2><p>'+e(context['note'])+'</p><p><a href="'+e(context['report_href'])+'">Åbn det kildebaserede klimaregnskab</a> · '+e(context['status'])+'</p>'
    baskets = []
    for b in report['supplier_baskets']:
        baskets.append(f"<tr><td><b>{e(b['supplier_name'])}</b></td><td>{b['priced_lines']} / {b['required_lines']} poster med pris<br><small>{b['confirmed_available_lines']} angivet tilgængelige; ikke reserveret</small></td><td>{fmt(b['known_goods_excl_vat'])} kr.</td><td>{fmt(b['delivery_excl_vat'])} kr.</td><td>{fmt(b['rest_purchase_total_excl_vat'])} kr.</td><td>{fmt(b['transport_kg_co2e'])} kg CO₂e<br><small>{e('; '.join(b['issues']))}</small></td></tr>")
    basket_table = '<h2>Saml indkøbet hos én leverandør</h2><p>Forslag for ikke-bestilte mængder, flest poster med pris først. Kun afstemte produktvarianter medregnes. Manglende poster kræver supplerende køb og flere leverancer. Ingen automatisk pris- eller CO₂vinder.</p><div class="scroll"><table><tr><th>Leverandør</th><th>Prisreferencedækning</th><th>Kendt varebeløb</th><th>Levering/gebyrer</th><th>Restindkøb, hvis dækket</th><th>Transportscenarie</th></tr>' + ''.join(baskets) + '</table></div><p>Prisreferencedækning er antal poster, ikke en andel af projektværdi. Materialernes klimabidrag skal følge de samme varer og mængder; transporttallet er særskilt og er ikke fuld LCA. Færre indkøbssteder betyder ikke automatisk færre leverancer eller lavere CO₂.</p>'
    budget = 'Ikke fastlagt' if report['budget'] is None else fmt(report['budget']['amount_excl_vat']) + ' kr.'
    forecast = 'Uafklaret' if report['forecast_excl_vat'] is None else fmt(report['forecast_excl_vat']) + ' kr.'
    variance = 'Uafklaret' if report['variance_excl_vat'] is None else fmt(report['variance_excl_vat']) + ' kr.'
    warning = '<p class="notice">TESTDATA — dette er en funktionstest, ikke et leverandørtilbud eller projektbudget.</p>' if report['test_mode'] else ''
    status = {'not_set': 'Budgetrammen er ikke fastlagt', 'unresolved': 'Budgetstatus kan ikke afgøres med de manglende poster', 'within_budget': 'Inden for budget for det angivne omfang', 'known_cost_above_budget': 'Den kendte delsum overstiger budgetrammen'}[report['budget_status']]
    return f'''<!doctype html><html lang="da"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Leverandører og budget</title><style>body{{font:16px/1.5 system-ui;background:#f6f4ef;color:#24352e;margin:0}}main{{max-width:1300px;margin:auto;padding:32px}}h1{{font-size:34px}}.cards{{display:flex;flex-wrap:wrap;gap:16px}}.card{{background:white;padding:20px;flex:1;min-width:180px;border-radius:8px}}strong{{display:block;font-size:24px}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{text-align:left;vertical-align:top;padding:14px;border-bottom:1px solid #ddd}}small{{color:#52635b}}ul{{padding-left:18px}}a{{color:#195b70}}.notice{{background:#fff0cd;padding:16px}}.scroll{{overflow:auto}}</style><main><p>Gemte beregninger · {e(report['as_of'])} · Alle beløb ekskl. moms</p><h1>Leverandørpriser og budget</h1>{warning}{render_comparison(report.get('comparison'))}<div class="cards"><div class="card">Kendt delsum<strong>{fmt(report['known_subtotal_excl_vat'])} kr.</strong></div><div class="card">Budgetramme<strong>{budget}</strong></div><div class="card">Forventet slutpris<strong>{forecast}</strong></div><div class="card">Afvigelse, plus er overskridelse<strong>{variance}</strong></div></div><p>{e(status)}. {e(report['note'])}</p>{labor_table}{climate_context}{basket_table}<h2>Valgte varer og ordresnapshot</h2><div class="scroll"><table><tr><th>Post og mængde</th><th>Sammenlignelige priser for ikke-bestilt mængde</th><th>Faktureret</th><th>Resterende aftalt</th><th>Forventet ikke-bestilt</th></tr>{''.join(rows)}</table></div><h2>Levering, gebyrer og CO₂</h2><p>Transport for den valgte indkøbsplan: {fmt(report['delivery_transport_kg_co2e'])} kg CO₂e. Leverandørspecifik rute/mængde/lastgrundlag kræves. Dette erstatter ikke automatisk projektets eksisterende A4-scenarie.</p><ul>{''.join('<li>'+e(d['supplier_id'])+': '+('Mangler' if d['amount_excl_vat'] is None else fmt(d['amount_excl_vat'])+' kr.')+'</li>' for d in report['delivery']) or '<li>Ingen valgte leverancer</li>'}</ul><details open><summary>Mangler og afgrænsning</summary><ul>{''.join('<li>'+e(g)+'</li>' for g in report['unresolved']) or '<li>Ingen mangler i det erklærede omfang</li>'}</ul></details><p>En prisimport ændrer ikke model, materialevalg, miljøkilder eller en fast budgetramme. Dette er et prisgrundlag og en budgetprognose, ikke bogføring, LCC eller en handelsfunktion. Ukendte priser er ikke nul.</p></main></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('import', 'fetch'):
        p = sub.add_parser(command)
        p.add_argument('source')
        p.add_argument('--format', choices=['json', 'csv'], required=True)
        p.add_argument('--store', type=Path, required=True)
    p = sub.add_parser('report')
    p.add_argument('project', type=Path)
    p.add_argument('--store', type=Path, required=True)
    p.add_argument('--as-of', type=iso_day, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--allow-test-data', action='store_true')
    p = sub.add_parser('check')
    p.add_argument('report', type=Path)
    p.add_argument('--as-of', type=iso_day, required=True)
    args = parser.parse_args(argv)
    if args.command == 'import':
        result = import_bytes(Path(args.source).read_bytes(), args.format, args.store, args.source)
    elif args.command == 'fetch':
        result = fetch(args.source, args.format, args.store)
    elif args.command == 'check':
        saved = json.loads(args.report.read_text())
        if saved['as_of'] != str(args.as_of) or any(digest(Path(p).read_bytes()) != h for p, h in saved['bound_files'].items()):
            raise ValueError('Rapportens dato eller input har ændret sig; genkør')
        request = saved['request']
        if any(str(Path(request[k]).resolve()) not in saved['bound_files'] for k in ('project', 'store')):
            raise ValueError('Rapportens inputbinding mangler')
        expected = assess(json.loads(Path(request['project']).read_text()), json.loads(Path(request['store']).read_text()), args.as_of, saved['test_mode'])
        if any(saved.get(key) != value for key, value in expected.items()):
            raise ValueError('Gemte resultater matcher ikke en genberegning')
        result = {'current': True, 'as_of': saved['as_of']}
    else:
        project = json.loads(args.project.read_text())
        result = assess(project, json.loads(args.store.read_text()), args.as_of, args.allow_test_data)
        original_paths = [Path(x['original']) for x in json.loads(args.store.read_text())['imports']]
        result['request'] = {'project': str(args.project.resolve()), 'store': str(args.store.resolve())}
        result['bound_files'] = {str(p.resolve()): digest(p.read_bytes()) for p in (args.project, args.store, Path(__file__), Path(__file__).with_name('report_io.py'), *original_paths)}
        write_report(result, args.out, protected_paths=[args.project, args.store, Path(__file__), *original_paths])
        args.out.with_suffix('.html').write_text(render(result))
        result = {k: result[k] for k in ('status', 'known_subtotal_excl_vat', 'forecast_excl_vat', 'budget_status')}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as exc:
        print('Prisfejl: ' + str(exc), file=sys.stderr)
        sys.exit(1)
