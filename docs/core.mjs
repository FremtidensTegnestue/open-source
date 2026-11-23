export const GROUPS = {wood:'Træ', insulation:'Isolering', concrete:'Beton', metal:'Metal', polymer:'Plast og polymerer', glass:'Glas', masonry:'Murværk', gypsum:'Gips', other:'Andre materialer og installationer'};
export const PHASES = [['A1-A3','Produktion'],['C3','Behandling efter brug'],['C4','Bortskaffelse'],['D','Uden for livscyklussen']];
export function normalize(text) {
  return String(text ?? '').toLocaleLowerCase('da-DK').replaceAll('æ','ae').replaceAll('ø','o').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
}
export function findMaterials(records, query) {
  const words = normalize(query).trim().split(/\s+/).filter(Boolean);
  return records.filter(({material:m}) => {
    const text = normalize([m.name,GROUPS[m.category] || '',m.id].join(' '));
    return words.every(word => text.includes(word));
  }).sort((a,b) => a.material.name.localeCompare(b.material.name,'da'));
}
export function observation(record, module) {
  return record.observations.find(row => row.property === 'global_warming_potential' && row.module === module);
}
export function numberLabel(row) {
  if (!row || row.value === null || row.value === undefined || !Number.isFinite(row.value)) return {text:'Ikke oplyst',approximate:false};
  const rounded = Number(row.value.toPrecision(6));
  return {text:new Intl.NumberFormat('da-DK',{maximumSignificantDigits:6}).format(row.value),approximate:rounded !== row.value};
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
