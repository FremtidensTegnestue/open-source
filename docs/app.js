import {GROUPS,PHASES,findMaterials,observation,numberLabel,unitLabel,referenceLabel,conditions,safeURL,validateData,quantityBasis,parseQuantity,quantityResult} from './core.mjs';
import {INSULATION,insulationBasis,compareInsulation} from './insulation.mjs';
import {FASTENERS,FASTENER_PHASES,validateFasteners,fastenerResult} from './fasteners.mjs';

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
function phaseGrid(rows,phases=PHASES) {
  const grid=el('div',undefined,'climate-grid');
  for(const [module,name] of phases) {
    const row=rows.find(row=>row?.module===module),phase=el('div',undefined,'phase');
    phase.append(el('h3',name),el('p',module,'module'),el('p',label(row),'value'),el('p',unitLabel(row?.unit),'unit'));
    grid.append(phase);
  }
  return grid;
}
function quantityCalculator(record) {
  const section=el('section',undefined,'quantity-calculation');
  const title=el('h3','Se bidraget for din mængde');title.id='quantity-title';section.setAttribute('aria-labelledby',title.id);section.append(title);
  let basis;
  try {basis=quantityBasis(record);} catch(error) {
    section.append(el('p',error.message));
    if (INSULATION.some(item=>item.id===record.material.id)) section.append(button('Sammenlign denne isolering',()=>chooseInsulation(record)));
    section.append(el('p','Du kan stadig læse kildens tal og bruge Gem materialedata.','muted'));return section;
  }
  section.append(el('p','Indtast en mængde af præcis den valgte materialetype og opbygning. Resultatet opdateres med det samme.'));
  const form=el('form'),input=el('input'),fieldLabel=el('label',`Din mængde i ${basis.unit}`);
  input.id='quantity-value';input.type='text';input.inputMode='decimal';input.autocomplete='off';input.placeholder='Fx 2,5';input.setAttribute('aria-describedby','quantity-help quantity-error');fieldLabel.htmlFor=input.id;
  const help=el('p',`Enheden er låst til kildens ${basis.unit}. Brug komma eller punktum som decimaltegn og ingen tusindtalsseparator. Størrelse, tykkelse og andre betingelser i referencen bevares.`,'muted');help.id='quantity-help';
  const error=el('p',undefined,'quantity-error');error.id='quantity-error';error.setAttribute('role','alert');
  const status=el('p','Indtast en mængde for at se dit beregnede bidrag.','muted');status.setAttribute('role','status');
  const output=el('div');output.hidden=true;
  const save=button('Gem beregning',()=>downloadJSON({...materialExport(record),calculation:result},record.material.id+'-beregning'));
  let result=null;
  function update() {
    result=null;output.replaceChildren();output.hidden=true;error.textContent='';input.removeAttribute('aria-invalid');
    if (!input.value.trim()) {status.textContent='Indtast en mængde for at se dit beregnede bidrag.';return;}
    try {
      result=quantityResult(record,parseQuantity(input.value));
      status.textContent=`Beregnet for ${label(result.quantity)} ${basis.unit} af den valgte reference.`;
      if (result.phases.some(phase=>phase.module!=='D' && phase.value<0)) output.append(el('p','Et negativt bidrag i én fase betyder ikke, at materialets samlede klimaaftryk er negativt.','notice'));
      output.append(phaseGrid(result.phases),el('p','Faserne vises hver for sig. D er ikke trukket fra. Transport, spild, montage, drift og udskiftninger er ikke tilføjet; dette er et afgrænset materialebidrag.','muted'));
      const method=el('details');method.append(el('summary','Sådan er din mængde beregnet'),el('p',`Kildens tal × ${String(result.quantity.value).replace('.',',')} / ${String(basis.amount).replace('.',',')}. Enhed: ${basis.unit}. Ingen enhedsomregning eller ændring af produktets egenskaber.`));
      output.append(method,save,el('p','Gemmer din mængde, de beregnede faser og kildens uændrede data som en JSON-fil.','muted'));output.hidden=false;
    } catch(problem) {input.setAttribute('aria-invalid','true');error.textContent=problem.message;status.textContent='Der vises ingen beregning for denne mængde.';}
  }
  input.addEventListener('input',update);form.addEventListener('submit',event=>{event.preventDefault();update();});
  form.append(fieldLabel,input,help,error);section.append(form,status,output);return section;
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
  if (update) {$('results-title').focus({preventScroll:true});$('results').scrollIntoView({block:'start'});}
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
  if (m.category==='insulation' || m.name.includes('ålegræs')) {
    const guidance=el('details');guidance.append(el('summary','Brug og forhold du skal afklare'));
    guidance.append(el('p',m.name.includes('ålegræs') ? 'Denne reference gælder et akustikpanel af ålegræs. Den dokumenterer ikke varmeisolering eller andre tangprodukter.' : 'Afklar materialets konkrete anvendelse, tykkelse, brand, fugt, lyd og montage. Navnet eller et lavt klimatal er ikke en dokumentation for teknisk egnethed.'));
    guidance.append(link('Se materialekort og kilder',new URL('#materialevalg',location.href).href));section.append(guidance);
  }
  section.append(quantityCalculator(record),el('h3','Kildens tal for referencemængden'));
  const grid = phaseGrid(PHASES.map(([module]) => observation(record,module)));
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
  table.append(body);const rawWrap = el('div',undefined,'raw-wrap');rawWrap.tabIndex=0;rawWrap.setAttribute('role','region');rawWrap.setAttribute('aria-label','Kildens præcise tal; tabellen kan rulles vandret');rawWrap.append(table);exact.append(rawWrap,el('p',`Materiale-ID: ${m.id}`,'metadata'));section.append(exact);
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
function materialExport(record) {
  const sourceIds = new Set(record.observations.map(row => row.source_id));
  for (const row of record.observations) if (conditions(row).basis_source_id) sourceIds.add(conditions(row).basis_source_id);
  return {scope:data.scope,parquet_manifest_sha256:data.parquet_manifest_sha256,...record,sources:data.sources.filter(source => sourceIds.has(source.id))};
}
function downloadJSON(value,name) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'}));
  const a = el('a');a.href = url;a.download = name.replace(/[^a-zA-Z0-9-]/g,'-')+'.json';document.body.append(a);a.click();a.remove();setTimeout(() => URL.revokeObjectURL(url),1000);
}
function downloadMaterial() {
  if (selected) downloadJSON(materialExport(selected),selected.material.id);
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
    initInsulation();
    document.querySelectorAll('#search-form input,#search-form button,button[data-query]').forEach(node => node.disabled=false);
    $('load-status').textContent = 'Klar. Vælg et eksempel, eller søg med dine egne ord.';restoreAddress();
  } catch {
    data = null;selected = null;$('results').hidden = true;$('detail').hidden = true;
    $('insulation-result').replaceChildren();$('insulation-save').hidden=true;
    $('insulation-status').textContent='Sammenligningen er ikke tilgængelig, før materialerne er hentet.';
    document.querySelectorAll('#insulation-form input,#insulation-form select,#insulation-form button').forEach(node=>node.disabled=true);
    $('load-status').textContent = 'Materialerne kunne ikke hentes. Kontroller forbindelsen, og prøv igen. Du kan stadig bruge læsestoffet nedenfor.';
    $('retry').hidden = false;
  }
}
let insulationResult=null;
function initInsulation() {
  // Refuse stale profile names or changed reference conditions before enabling.
  for (const profile of INSULATION) insulationBasis(data.records.find(record=>record.material.id===profile.id));
  document.querySelectorAll('#insulation-form input,#insulation-form select,#insulation-form button').forEach(node=>node.disabled=false);
  fillInsulationOptions();updateInsulation();
}
function fillInsulationOptions() {
  const profiles=INSULATION.filter(item=>item.form===$('insulation-form-type').value);
  for (const id of ['insulation-a','insulation-b']) {
    $(id).replaceChildren();
    for (const p of profiles) {const option=el('option',p.name);option.value=p.id;$(id).append(option);}
  }
  $('insulation-a').value=profiles.find(p=>p.id.includes($('insulation-form-type').value==='plade' ? 'D1535:' : 'D1545:')).id;
  $('insulation-b').value=profiles.find(p=>p.id.includes($('insulation-form-type').value==='plade' ? 'D1627:' : 'D1626:')).id;
}
function chooseInsulation(record) {
  const profile=insulationBasis(record);
  if ($('insulation-form-type').value!==profile.form) {$('insulation-form-type').value=profile.form;fillInsulationOptions();}
  $('insulation-a').value=profile.id;updateInsulation();
  $('isolering').scrollIntoView({block:'start'});$('insulation-a').focus({preventScroll:true});
}
function updateInsulation() {
  insulationResult=null;$('insulation-result').replaceChildren();$('insulation-save').hidden=true;$('insulation-error').textContent='';
  for(const id of ['insulation-area','insulation-r']) $(id).removeAttribute('aria-invalid');
  if (!data) return;
  if (!$('insulation-area').value.trim() || !$('insulation-r').value.trim()) {$('insulation-status').textContent='Angiv areal og ønsket R for at se begge muligheder.';return;}
  let field='insulation-area';
  try {
    const area=parseQuantity($('insulation-area').value);field='insulation-r';
    const resistance=parseQuantity($('insulation-r').value);
    if (resistance<=0) throw new Error('Isoleringsevnen R skal være større end 0 m²K/W.');
    field=null;
    const a=data.records.find(record=>record.material.id===$('insulation-a').value),b=data.records.find(record=>record.material.id===$('insulation-b').value);
    insulationResult=compareInsulation(a,b,area,resistance);
    $('insulation-status').textContent=`Samme areal: ${label({value:area})} m². Samme isoleringsevne: R = ${label({value:resistance})} m²K/W. Ingen samlet vinder udpeges.`;
    const names=el('div',undefined,'comparison-names');
    for (const [i,record] of [a,b].entries()) {
      const name=el('div');name.append(el('h3',`${i===0 ? 'A' : 'B'} · ${record.material.name}`),button('Se reference og kilde',()=>{showMaterial(record,true,true);},'secondary'));names.append(name);
    }
    $('insulation-result').append(names);
    if (insulationResult.variants.some(v=>v.phases.some(p=>p.module!=='D' && p.value!==null && p.value<0))) $('insulation-result').append(el('p','Negative produktionstal kan modsvares af påvirkninger efter brug. Læs alle viste faser; et minustal er ikke et samlet negativt klimaaftryk.','notice'));
    for (const [i,[module,name]] of PHASES.entries()) {
      const section=el('section',undefined,'comparison-phase');section.append(el('h3',`${name} · ${module}`));
      const list=el('dl');
      for (const [title,row] of [['A',insulationResult.variants[0].phases[i]],['B',insulationResult.variants[1].phases[i]],['Forskel B minus A',insulationResult.differences[i]]]) {
        const cell=el('div');cell.append(el('dt',title),el('dd',label(row)),el('p','kg CO₂e','muted'));list.append(cell);
      }
      section.append(list);$('insulation-result').append(section);
    }
    $('insulation-result').append(el('p','En negativ forskel betyder, at B er lavere i den pågældende fase. D vises særskilt og er ikke trukket fra. ≈ markerer afrunding; download bevarer de præcise beregnede tal.','muted'));
    $('insulation-save').hidden=false;
  } catch(error) {
    insulationResult=null;$('insulation-result').replaceChildren();$('insulation-save').hidden=true;
    if(field) $(field).setAttribute('aria-invalid','true');
    $('insulation-error').textContent=error.message;$('insulation-status').textContent='Ret indtastningen. Den tidligere sammenligning er fjernet.';
  }
}
$('insulation-form').addEventListener('submit',event=>{event.preventDefault();updateInsulation();});
for(const id of ['insulation-area','insulation-r']) $(id).addEventListener('input',updateInsulation);
for(const id of ['insulation-a','insulation-b']) $(id).addEventListener('change',updateInsulation);
$('insulation-form-type').addEventListener('change',()=>{fillInsulationOptions();updateInsulation();});
$('insulation-clear').addEventListener('click',()=>{$('insulation-area').value='';$('insulation-r').value='';updateInsulation();$('insulation-area').focus();});
$('insulation-save').addEventListener('click',()=>{
  if(!insulationResult) return;
  downloadJSON({schema_version:1,tool_version:'browser-insulation-1',data_scope:data.scope,parquet_manifest_sha256:data.parquet_manifest_sha256,calculation:insulationResult,source_records:insulationResult.variants.map(v=>materialExport(data.records.find(r=>r.material.id===v.material_id))),method_url:'https://fremtidenstegnestue.github.io/open-source/#isolering-metode'},'isoleringssammenligning');
});
$('search-form').addEventListener('submit',event => {event.preventDefault();if(data) search();});
for (const b of document.querySelectorAll('button[data-query]')) b.addEventListener('click',() => {$('query').value=b.dataset.query;search();});
$('more').addEventListener('click',() => {shown+=12;renderResults();});
$('retry').addEventListener('click',load);
$('new-search').addEventListener('click',() => {$('query').focus({preventScroll:true});$('materialer').scrollIntoView({block:'start'});});
let fastenersData=null, screwResult=null;
function updateFastener() {
  screwResult=null;$('fastener-result').replaceChildren();$('fastener-save').hidden=true;
  $('fastener-error').textContent='';$('fastener-mass').removeAttribute('aria-invalid');
  if(!fastenersData) return;
  const record=fastenersData.records.find(r=>r.material.id===$('fastener-kind').value);
  const source=fastenersData.sources.find(s=>s.id===record.material.source_id);
  const sourceBox=$('fastener-source');sourceBox.replaceChildren();
  sourceBox.append(el('p',`Originalnavn: ${record.material.name}. ÖKOBAUDAT / Sphera Solutions GmbH. Udgave 20.26.070 · tysk generisk reference · referenceår 2023 · datagyldighed til 2026.`),link('Åbn den præcise kildereference',source.url));
  if (!$('fastener-mass').value.trim()) {$('fastener-status').textContent='Indtast skruernes nettovægt for at se bidraget.';return;}
  try {
    screwResult=fastenerResult(record,parseQuantity($('fastener-mass').value));
    $('fastener-status').textContent=`${FASTENERS.find(p=>p.id===record.material.id).label} · ${label(screwResult.quantity)} kg nettovægt.`;
    $('fastener-result').append(phaseGrid(screwResult.phases,FASTENER_PHASES),el('p',`Ikke oplyst i denne reference: ${screwResult.missing_modules.join(', ')}. Manglende faser er ikke sat til nul. D er ikke trukket fra.`,'notice'));
    const exact=el('details'),list=el('ul');exact.append(el('summary','Se kildens præcise tal pr. 1 kg'));
    for(const [module] of FASTENER_PHASES) {
      const row=record.observations.find(r=>r.module===module);
      list.append(el('li',`${module}: ${row ? row.value_text ?? 'Ikke oplyst' : 'Ikke oplyst'}${row ? ` ${row.unit}` : ''}`));
    }
    exact.append(list);$('fastener-result').append(exact);$('fastener-save').hidden=false;
  } catch(error) {
    $('fastener-mass').setAttribute('aria-invalid','true');$('fastener-error').textContent=error.message;
    $('fastener-status').textContent='Ret nettovægten. Den tidligere beregning er fjernet.';
  }
}
async function loadFasteners() {
  fastenersData=null;screwResult=null;$('fastener-result').replaceChildren();$('fastener-source').replaceChildren();$('fastener-save').hidden=true;$('fastener-retry').hidden=true;$('fastener-error').textContent='';
  document.querySelectorAll('#fastener-form input,#fastener-form select,#fastener-form button').forEach(n=>n.disabled=true);
  $('fastener-status').textContent='Henter skruereferencerne…';
  try {
    const response=await fetch(new URL('fastgoerelser.json',import.meta.url));
    if(!response.ok) throw new Error('Skruedata kunne ikke hentes.');
    fastenersData=validateFasteners(await response.json());
    $('fastener-kind').replaceChildren();
    for(const profile of FASTENERS) {const option=el('option',profile.label);option.value=profile.id;$('fastener-kind').append(option);}
    document.querySelectorAll('#fastener-form input,#fastener-form select,#fastener-form button').forEach(n=>n.disabled=false);
    updateFastener();
  } catch {
    fastenersData=null;$('fastener-result').replaceChildren();$('fastener-save').hidden=true;
    $('fastener-status').textContent='Skruedata kunne ikke hentes eller godkendes. Der vises ingen beregning. Prøv igen; kildekortene kan stadig læses.';
    $('fastener-retry').hidden=false;
  }
}
$('fastener-form').addEventListener('submit',event=>{event.preventDefault();updateFastener();});
$('fastener-mass').addEventListener('input',updateFastener);
$('fastener-kind').addEventListener('change',updateFastener);
$('fastener-clear').addEventListener('click',()=>{$('fastener-mass').value='';updateFastener();$('fastener-mass').focus();});
$('fastener-retry').addEventListener('click',loadFasteners);
$('fastener-save').addEventListener('click',()=>{
  if(!screwResult || !fastenersData) return;
  const record=fastenersData.records.find(r=>r.material.id===screwResult.material_id);
  downloadJSON({schema_version:1,tool_version:'browser-fasteners-1',scope:fastenersData.scope,parquet_manifest_sha256:fastenersData.parquet_manifest_sha256,
    calculation:screwResult,source_record:record,sources:fastenersData.sources.filter(s=>s.id===record.material.source_id)},'skruer-beregning');
});
window.addEventListener('popstate',() => restoreAddress(true));
load();
loadFasteners();
