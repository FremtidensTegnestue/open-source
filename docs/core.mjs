export const GROUPS = {wood:'Træ', insulation:'Isolering', concrete:'Beton', metal:'Metal', polymer:'Plast og polymerer', glass:'Glas', masonry:'Murværk', gypsum:'Gips', other:'Andre materialer og installationer'};
export const PHASES = [['A1-A3','Produktion'],['C3','Behandling efter brug'],['C4','Bortskaffelse'],['D','Uden for livscyklussen']];
export function normalize(text) {
  return String(text ?? '').toLocaleLowerCase('da-DK').replaceAll('æ','ae').replaceAll('ø','o').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
}
export function findMaterials(records, query) {
  const words = normalize(query).trim().split(/\s+/).filter(Boolean);
  return records.filter(({material:m}) => {
    const text = normalize([m.name,GROUPS[m.category] || '',m.id].join(' '));
    return words.every(word => {
      if (word==='tang') return /\balegraes\b|\btang\b/.test(text);
      if (word==='cellulose' || word==='celluloseisolering') return text.includes('papiruld') || text.includes(word);
      return text.includes(word);
    });
  }).sort((a,b) => a.material.name.localeCompare(b.material.name,'da'));
}
export function observation(record, module) {
  return record.observations.find(row => row.property === 'global_warming_potential' && row.module === module);
}
export function numberLabel(row) {
  if (!row || row.value === null || row.value === undefined || !Number.isFinite(row.value)) return {text:'Ikke oplyst',approximate:false};
  const rounded = Number(row.value.toPrecision(6));
  const scientific=Math.abs(row.value)>=1e9 || (row.value!==0 && Math.abs(row.value)<1e-6);
  return {text:new Intl.NumberFormat('da-DK',{maximumSignificantDigits:6,...(scientific ? {notation:'scientific'} : {})}).format(row.value),approximate:rounded !== row.value};
}
export function unitLabel(unit) {
  if (unit === 'kg CO2-eq') return 'kg CO₂e';
  if (unit === 'kg CO2-eq/(m2 year)') return 'kg CO₂e/(m² · år)';
  return unit || 'Enhed ikke oplyst';
}
export function conditions(row) {
  try {return JSON.parse(row?.conditions_json || '{}');} catch {return {};}
}
export function referenceLabel(row) {
  if (conditions(row).record_scope === 'installation_area_reference_factor') return 'Pr. 1 m² opvarmet etageareal inkl. opvarmet kælder, pr. år';
  if (!row?.declared_unit) return 'Referencemængde ikke oplyst';
  const match = row.declared_unit.match(/^([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)\s+(.+)$/i);
  if (!match) return `For ${row.declared_unit}`;
  const amount = numberLabel({value:Number(match[1])});
  const unit = match[2].replace('with R=1 m²K/W','ved varmemodstand R = 1 m²K/W');
  return `For ${amount.approximate ? '≈ ' : ''}${amount.text} ${unit}`;
}
// A deliberately narrow calculation in the source's own unit. Qualified
// insulation and annual installation references need a different method.
export function quantityBasis(record) {
  const rows = record.observations.filter(row => row.property === 'global_warming_potential');
  if (rows.length !== PHASES.length || PHASES.some(([module]) => rows.filter(row => row.module === module).length !== 1)) throw new Error('Klimafaserne mangler eller er gentaget.');
  let reference;
  for (const row of rows) {
    const context = conditions(row);
    if (context.record_scope === 'installation_area_reference_factor') throw new Error('Denne reference gælder opvarmet etageareal og år. Den kræver en særskilt beregningsmetode.');
    if (row.declared_unit?.includes('with R=')) throw new Error('Denne isoleringsreference gælder en bestemt varmemodstand. Areal alene er derfor ikke et tilstrækkeligt beregningsgrundlag.');
    const match = row.declared_unit?.match(/^(\d+(?:\.\d+)?) (kg|ton|m|m²|m³|stk)$/);
    if (!match || context.record_scope !== 'official_material_or_construction_reference' || row.unit !== 'kg CO2-eq') throw new Error('Denne reference har særlige enheder eller betingelser, som den enkle beregning ikke understøtter.');
    const amount = Number(match[1]), unit = match[2];
    if (!Number.isFinite(amount) || amount <= 0 || context.reference_amount !== amount || context.reference_unit !== unit) throw new Error('Kildens referencemængde og enhed stemmer ikke overens.');
    if (context.declared_amount !== undefined || context.declared_references !== undefined) throw new Error('Referencen kræver en udvidet kontrol af sit beregningsgrundlag.');
    if (reference && (reference.amount !== amount || reference.unit !== unit)) throw new Error('Klimafaserne gælder forskellige referencemængder.');
    if (row.value !== null && (typeof row.value !== 'number' || !Number.isFinite(row.value))) throw new Error('Kilden har en ugyldig klimaværdi.');
    reference = {amount,unit};
  }
  return reference;
}
export function parseQuantity(raw) {
  if (typeof raw !== 'string' || !/^(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(raw.trim())) throw new Error('Skriv en mængde på 0 eller mere, fx 2,5. Brug ingen tusindtalsseparator.');
  const value = Number(raw.trim().replace(',','.'));
  if (!Number.isFinite(value) || (value === 0 && /[1-9]/.test(raw))) throw new Error('Mængden er uden for det understøttede talområde.');
  return value;
}
export function quantityResult(record, value) {
  const reference = quantityBasis(record);
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) throw new Error('Mængden skal være et endeligt tal på 0 eller mere.');
  const factor = value / reference.amount;
  if (!Number.isFinite(factor) || (factor === 0 && value !== 0)) throw new Error('Mængden er uden for det understøttede talområde.');
  const phases = PHASES.map(([module]) => {
    const row = observation(record,module), result = row.value === null ? null : row.value * factor;
    if (result !== null && (!Number.isFinite(result) || (result === 0 && row.value !== 0 && value !== 0))) throw new Error('Resultatet er uden for det understøttede talområde.');
    return {module,value:result === 0 ? 0 : result,unit:'kg CO2-eq',observation_id:row.id,source_id:row.source_id};
  });
  return {method:'single_reference_quantity.v1',formula:'source_value × quantity / reference_amount',quantity:{value,unit:reference.unit},reference,scaling_factor:factor,phases,scope:'Én uændret materialereference, fase for fase. Ingen samlet bygnings-LCA eller teknisk egnethedsvurdering.'};
}
export function safeURL(raw) {
  try {const url = new URL(raw);return ['https:','http:'].includes(url.protocol) ? url.href : null;} catch {return null;}
}
export function validateData(data) {
  if (data?.schema_version !== 1 || data.material_count !== 507 || data.records?.length !== 507 || data.observation_count !== 2535 || !Array.isArray(data.sources)) throw new Error('Ukendt eller ufuldstændig dataudgave');
  const ids = new Set(), sources = new Set(data.sources.map(s => s.id));
  let rows = 0;
  for (const record of data.records) {
    const m = record.material;
    if (!m?.id || !m.name || ids.has(m.id) || !sources.has(m.source_id) || record.observations?.length !== 5) throw new Error('Ufuldstændig materialereference');
    ids.add(m.id);
    for (const row of record.observations) {
      if (row.material_id !== m.id || !sources.has(row.source_id) || !['number','object'].includes(typeof row.value) || (row.value !== null && !Number.isFinite(row.value))) throw new Error('Ugyldig observation');
      const basisSource = conditions(row).basis_source_id;
      if (basisSource && !sources.has(basisSource)) throw new Error('Grundlaget mangler sin kilde');
      rows++;
    }
    const modules = record.observations.filter(row => row.property === 'global_warming_potential').map(row => row.module).sort();
    if (modules.join('|') !== 'A1-A3|C3|C4|D') throw new Error('Et klimamodul mangler eller er gentaget');
  }
  if (rows !== data.observation_count) throw new Error('Forkert observationsantal');
  return data;
}
