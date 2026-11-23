import {GROUPS,PHASES,findMaterials,observation,numberLabel,unitLabel,referenceLabel,conditions,safeURL,validateData} from './core.mjs';

const $ = id => document.getElementById(id);
let data, hits = [], shown = 12, selected = null;
const el = (tag,text,className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
function link(text,url) {
  const a = el('a',text), safe = safeURL(url);
  if (safe) a.href = safe;
  else a.append(' — adresse ikke tilgængelig');
  return a;
}
function button(text,handler,className='secondary') {
  const b = el('button',text,className);
  b.type = 'button';b.addEventListener('click',handler);return b;
}
function label(row) {
  const n = numberLabel(row);
  return (n.approximate ? '≈ ' : '') + n.text;
}
function updateAddress(id=null, push=false) {
  const params = new URLSearchParams();
  if ($('query').value.trim()) params.set('q',$('query').value.trim());
  if (id) params.set('materiale',id);
  const url = new URL(location.href);
  url.hash = params.toString();
  history[push ? 'pushState' : 'replaceState']({},'',url);
}
function search(update=true) {
  hits = findMaterials(data.records,$('query').value);
  shown = 12;selected = null;$('detail').hidden = true;
  if (update) updateAddress();
  renderResults();
}
function renderResults() {
  $('results').hidden = false;
  $('result-list').replaceChildren();
  $('empty').hidden = hits.length > 0;
  $('result-count').textContent = `${hits.length} ${hits.length === 1 ? 'reference' : 'referencer'} fundet${hits.length > shown ? ` · ${shown} vist` : ''}`;
  for (const record of hits.slice(0,shown)) {
    const m = record.material, li = el('li'), card = el('article',undefined,'result-card');
    card.append(el('p',GROUPS[m.category] || 'Materialereference','group'),el('h3',m.name),el('p',referenceLabel(observation(record,'A1-A3')),'reference'));
    const open = button('Se tal og kilde',() => showMaterial(record,true,true));
    open.setAttribute('aria-label',`Se tal og kilde for ${m.name}`);
    open.dataset.material = m.id;
    card.append(open);li.append(card);$('result-list').append(li);
  }
  $('more').hidden = shown >= hits.length;
}
function showMaterial(record, focus=false, push=false) {
  selected = record;
  const m = record.material, production = observation(record,'A1-A3'), c = conditions(production);
  const section = $('detail');section.replaceChildren();section.hidden = false;
  const top = el('div',undefined,'detail-top');
  top.append(el('p','Valgt materiale · generisk reference','eyebrow'),button('Tilbage til resultater',closeMaterial));
  const title = el('h2',m.name);title.id = 'material-title';title.tabIndex = -1;
  section.append(top,title,el('p',referenceLabel(production),'reference'));
  if (c.record_scope === 'installation_area_reference_factor') {
    section.append(el('p','Dette er en standardværdi for en installation pr. opvarmet areal og år. Den beskriver ikke én vare eller ét kilo materiale. Arealet omfatter også opvarmet kælder.','reference-note'));
  } else {
    section.append(el('p','Tallene gælder kildens referencemængde ovenfor. Samme materiale kan kræve en anden mængde for at opfylde dit projekts krav. Der er ikke regnet om til dit byggeri.','muted'));
  }
  if (production?.declared_unit?.includes('with R=')) section.append(el('p','Isoleringen er opgjort for den angivne varmemodstand R. Tallet gælder derfor ikke automatisk én fast tykkelse isolering.','reference-note'));
  if (c.source_comment) section.append(el('p',`Kildens bemærkning: ${c.source_comment}`,'reference-note'));
  const grid = el('div',undefined,'climate-grid');
  for (const [module,name] of PHASES) {
    const row = observation(record,module), phase = el('div',undefined,'phase');
    phase.append(el('h3',name),el('p',module,'module'),el('p',label(row),'value'),el('p',unitLabel(row?.unit),'unit'));
    grid.append(phase);
  }
  section.append(grid,el('p','CO₂e samler påvirkningen fra forskellige drivhusgasser i én enhed. ≈ betyder, at visningen er afrundet; kildens præcise tal findes nedenfor.','muted'));
  if (record.observations.some(row => row.value !== null && row.value < 0)) section.append(el('p','Et minustal i ét modul betyder ikke, at materialets samlede klimaaftryk er negativt. Modul D vises særskilt og er ikke trukket fra de øvrige tal.','notice'));
  section.append(el('p','Her vises produktion og tre efterfølgende moduler. Andre livscyklusfaser er ikke med i dette opslag. Tallene er ikke et samlet klimaregnskab og bør ikke rangordnes uden samme funktion, mængde og beregningsgrundlag.','muted'));
  const mass = record.observations.find(row => ['density','mass_factor'].includes(row.property));
  const physical = el('div',undefined,'physical'), massText = el('p');
  massText.append(el('strong',mass?.property === 'density' ? 'Densitet fra kilden' : 'Massefaktor fra kilden'),document.createTextNode(`${label(mass)} ${mass?.unit || ''}`));
  physical.append(massText);section.append(physical);
  const explanation = el('details'), summary = el('summary','Sådan læser du faserne');
  explanation.append(summary,el('p','A1–A3 beskriver produktionen. C3 beskriver behandling efter brug, og C4 bortskaffelse. D beskriver mulige virkninger uden for den opgjorte livscyklus. Ingen moduler er summeret på denne side.'),el('p','Referenceenheden er afgørende: ét tal pr. m³ kan ikke sammenlignes direkte med et tal pr. kg, m² eller år. En generisk reference er et beregningsgrundlag, ikke dokumentation for et bestemt produkt.'));
  section.append(explanation);
  const sourceDetails = el('details');sourceDetails.append(el('summary','Kilde, udgave og rettigheder'));
  const sources = el('ul',undefined,'source-list');
  const sourceIds = new Set(record.observations.map(row => row.source_id));
  if (c.basis_source_id) sourceIds.add(c.basis_source_id);
  for (const id of sourceIds) {
    const source = data.sources.find(source => source.id === id);
    if (!source) continue;
    const li = el('li');li.append(el('strong',source.publisher || 'Udgiver ikke oplyst'),el('p',source.title),link('Åbn originalkilden',source.url));
    const meta = el('div',undefined,'metadata');
    meta.append(el('p',`Hentet: ${source.retrieved_at.slice(0,10)}. Kilde-ID: ${source.id}`),el('p',`Kildens registrerede vilkår: ${source.license}`),el('p',`Registreret rettighedsstatus: ${source.license_status === 'unknown' ? 'Uafklaret — viderebrug kræver kontrol af kildens vilkår.' : source.license_status}`),el('p',`Filens SHA-256: ${source.sha256}`));
    li.append(meta);sources.append(li);
  }
  sourceDetails.append(sources);
  if (safeURL(c.underlying_source_url)) sourceDetails.append(link('Referencens bagvedliggende deklaration eller undersøgelse',c.underlying_source_url));
  sourceDetails.append(el('p','Kildeudgaven er fra 2025 og blev hentet i november 2026. Kontroller aktualitet og anvendelse før brug i et projekt. Vores MIT-licens ændrer ikke originalernes rettigheder.','muted'));
  section.append(sourceDetails);
  const exact = el('details');exact.append(el('summary','Kildens præcise tal og enheder'));
  const table = el('table',undefined,'raw-table'), caption = el('caption','Uændrede værdier fra det offentlige datagrundlag.');table.append(caption);
  const head = el('tr');for(const text of ['Egenskab','Kildens tal','Enhed','Reference','Placering']) head.append(el('th',text));
  const thead = el('thead');thead.append(head);table.append(thead);
  const body = el('tbody');
  for (const row of record.observations) {
    const tr = el('tr');
    const values = [row.module || (row.property === 'density' ? 'Densitet' : 'Massefaktor'),row.value_text || (row.value === null ? 'Ikke oplyst' : String(row.value)),row.unit || 'Ikke oplyst',row.declared_unit || 'Se kildens betingelser',row.source_locator];
    for (const value of values) tr.append(el('td',value));body.append(tr);
  }
  table.append(body);const rawWrap = el('div',undefined,'raw-wrap');rawWrap.append(table);exact.append(rawWrap,el('p',`Materiale-ID: ${m.id}`,'metadata'));section.append(exact);
  const actions = el('div',undefined,'detail-actions');actions.append(button('Gem materialedata',downloadMaterial),el('span','JSON-fil med præcise tal, betingelser og kilder.','muted'));section.append(actions);
  if (push) updateAddress(m.id,true);
  if (focus) {title.focus({preventScroll:true});section.scrollIntoView({block:'start'});}
}
function closeMaterial() {
  const id = selected?.material.id;selected = null;$('detail').hidden = true;updateAddress();
  if ($('results').hidden) search(false);
  const target = [...document.querySelectorAll('button[data-material]')].find(button => button.dataset.material === id);
  (target || $('query')).focus();$('results').scrollIntoView({block:'start'});
}
function downloadMaterial() {
  if (!selected) return;
  const sourceIds = new Set(selected.observations.map(row => row.source_id));
  for (const row of selected.observations) if (conditions(row).basis_source_id) sourceIds.add(conditions(row).basis_source_id);
  const exported = {scope:data.scope,parquet_manifest_sha256:data.parquet_manifest_sha256,...selected,sources:data.sources.filter(source => sourceIds.has(source.id))};
  const url = URL.createObjectURL(new Blob([JSON.stringify(exported,null,2)+'\n'],{type:'application/json'}));
  const a = el('a');a.href = url;a.download = selected.material.id.replace(/[^a-zA-Z0-9-]/g,'-')+'.json';document.body.append(a);a.click();a.remove();setTimeout(() => URL.revokeObjectURL(url),1000);
}
function restoreAddress(focus=false) {
  if (!data) return;
  const params = new URLSearchParams(location.hash.slice(1));
  $('query').value = params.get('q') || '';
  if (params.has('q')) search(false);
  else {$('results').hidden = true;$('detail').hidden = true;selected = null;}
  if (params.has('materiale')) {
    const record = data.records.find(record => record.material.id === params.get('materiale'));
    if (record) showMaterial(record,focus);
    else $('load-status').textContent = 'Linkets materiale findes ikke i denne dataudgave. Prøv en ny søgning.';
  }
}
async function load() {
  $('retry').hidden = true;$('load-status').textContent = 'Henter materialerne…';
  document.querySelectorAll('#search-form input,#search-form button,button[data-query]').forEach(node => node.disabled=true);
  try {
    const response = await fetch(new URL('materialer.json',import.meta.url));
    if (!response.ok) throw new Error('Data kunne ikke hentes');
    data = validateData(await response.json());
    document.querySelectorAll('#search-form input,#search-form button,button[data-query]').forEach(node => node.disabled=false);
    $('load-status').textContent = 'Klar. Vælg et eksempel, eller søg med dine egne ord.';restoreAddress();
  } catch {
    data = null;selected = null;$('results').hidden = true;$('detail').hidden = true;
    $('load-status').textContent = 'Materialerne kunne ikke hentes. Kontroller forbindelsen, og prøv igen. Du kan stadig bruge læsestoffet nedenfor.';
    $('retry').hidden = false;
  }
}
$('search-form').addEventListener('submit',event => {event.preventDefault();if(data) search();});
for (const b of document.querySelectorAll('button[data-query]')) b.addEventListener('click',() => {$('query').value=b.dataset.query;search();});
$('more').addEventListener('click',() => {shown+=12;renderResults();});
$('retry').addEventListener('click',load);
window.addEventListener('popstate',() => restoreAddress(true));
load();
