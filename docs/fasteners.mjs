import {conditions} from './core.mjs';

export const FASTENERS = [
  {id:'environmental:material:oekobaudat:889e2819-01be-4aa4-b7d3-d19e01e75c02@20.26.070',name:'Galvanized steel screws',label:'Galvaniserede stålskruer'},
  {id:'environmental:material:oekobaudat:6c46fc8d-6a74-415b-8e6b-b90af72178ac@20.26.070',name:'Stainless steel screws',label:'Rustfri stålskruer'},
];
export const FASTENER_PHASES = [['A1-A3','Produktion'],['C1','Nedtagning'],['C2','Transport efter brug'],['C3','Behandling efter brug'],['C4','Bortskaffelse'],['D','Uden for livscyklussen']];
const INDICATOR='a7ea142a-9749-11ed-a8fc-0242ac120002';

export function fastenerBasis(record) {
  const profile=FASTENERS.find(p=>p.id===record?.material?.id);
  if (!profile || record.material.name!==profile.name || record.material.kind!=='generic') throw new Error('Skruekilden er ikke en af de to gennemgåede referencer.');
  const modules=new Set();
  for (const row of record.observations) {
    const c=conditions(row), refs=c.declared_references;
    if (row.property!=='climate_change' || row.method!==INDICATOR || c.indicator_uuid!==INDICATOR || row.unit!=='kg CO2 eq.'
        || row.material_id!==record.material.id || row.source_id!==record.material.source_id
        || row.declared_unit!=='kg' || row.basis!=='1.0 kg' || c.declared_amount!==1
        || refs?.length!==1 || refs[0].amount!==1 || refs[0].unit!=='kg' || refs[0].exchange_mean_amount!==1 || refs[0].resulting_flow_amount!==1
        || c.dataset_version!=='20.26.070' || c.geography!=='DE' || c.reference_year!==2023 || c.valid_until!==2026
        || c.standards?.length!==1 || c.standards[0]!=='EN 15804+A2 (EF 3.1)'
        || !FASTENER_PHASES.some(([m])=>m===row.module) || modules.has(row.module)
        || (row.value!==null && (typeof row.value!=='number' || !Number.isFinite(row.value)))) throw new Error('Skruekildens enhed, indikator, modul eller reference er ændret.');
    modules.add(row.module);
  }
  if (!modules.has('A1-A3')) throw new Error('Produktionsfasen mangler i skruekilden.');
  return profile;
}
export function validateFasteners(data) {
  if (data?.schema_version!==1 || data.material_count!==2 || data.records?.length!==2 || data.observation_count!==9 || data.sources?.length!==2 || !/^[a-f0-9]{64}$/.test(data.parquet_manifest_sha256)) throw new Error('Ukendt skrue-dataudgave.');
  const ids=new Set(), sources=new Map(data.sources.map(s=>[s.id,s]));
  let count=0;
  for (const record of data.records) {
    fastenerBasis(record);
    const source=sources.get(record.material.source_id);
    if (ids.has(record.material.id) || !source || source.license_status!=='verified' || source.license!=='Free of charge for all users and uses') throw new Error('Skrueudvalget har en dublet eller mangler kilde og vilkår.');
    const expected=record.material.name==='Galvanized steel screws' ? 'A1-A3|C1|C2|C3|D' : 'A1-A3|C1|C2|D';
    if(record.observations.map(r=>r.module).sort().join('|')!==expected) throw new Error('Skruekildens modulomfang er ændret.');
    ids.add(record.material.id);count+=record.observations.length;
  }
  if(count!==data.observation_count) throw new Error('Skruekildens observationsantal stemmer ikke.');
  return data;
}
export function fastenerResult(record,mass) {
  fastenerBasis(record);
  if (typeof mass!=='number' || !Number.isFinite(mass) || mass<0) throw new Error('Nettovægten skal være et endeligt tal på 0 kg eller mere.');
  const phases=FASTENER_PHASES.map(([module])=>{
    const row=record.observations.find(r=>r.module===module),value=row?.value==null ? null : row.value*mass;
    if (value!==null && (!Number.isFinite(value) || (value===0 && mass!==0 && row.value!==0))) throw new Error('Resultatet er uden for det understøttede talområde.');
    return {module,value:value===0 ? 0 : value,unit:'kg CO2-eq',observation_id:row?.id ?? null,source_id:row?.source_id ?? null};
  });
  return {method:'oekobaudat_screw_mass.v1',material_id:record.material.id,indicator_uuid:INDICATOR,
    quantity:{value:mass,unit:'kg'},reference:{amount:1,unit:'kg'},formula:'source_value × net_screw_mass_kg / 1 kg',
    phases,missing_modules:phases.filter(p=>p.value===null).map(p=>p.module),
    excluded_modules:['A4','A5','B1-B7'],scope:'Én tysk generisk skrue-reference. Kildens slutscenarie bevares. D vises særskilt. Ingen fuld LCA, produktmatch eller dokumentation for bæreevne og korrosion.'};
}
