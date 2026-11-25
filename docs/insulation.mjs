import {PHASES, conditions, observation} from './core.mjs';

// Reviewed, homogeneous insulation references. Facings, pipe insulation,
// acoustic-only and load-bearing products are outside this comparison.
export const INSULATION = [
  ['D1532','row74','Mineraluld, fleksibel isolering, kl. 30','plade'],
  ['D1533','row75','Mineraluld, fleksibel isolering, kl. 32','plade'],
  ['D1534','row76','Mineraluld, fleksibel isolering, kl. 34','plade'],
  ['D1535','row77','Mineraluld, fleksibel isolering, kl. 37','plade'],
  ['D1543','row85','Mineraluld, granulat, kl. 32','loes'],
  ['D1544','row86','Mineraluld, granulat, kl. 34','loes'],
  ['D1545','row87','Mineraluld, granulat, kl. 37','loes'],
  ['D1546','row88','Mineraluld, granulat, kl. 42','loes'],
  ['D1620','row156','Isoleringsplade, hamp','plade'],
  ['D1621','row157','Isoleringsplade, kork','plade'],
  ['D1622','row158','Isoleringsplade, græs','plade'],
  ['D1626','row162','Træfiberisolering, løsuld','loes'],
  ['D1627','row163','Træfiberisolering, plade','plade'],
].map(([code,row,name,form])=>({id:`br18:t7:${code}:${row}`,name,form}));

export function insulationBasis(record) {
  const profile=INSULATION.find(item=>item.id===record?.material?.id);
  if (!profile || profile.name!==record.material.name || record.material.dataset_id!=='br18') throw new Error('Referencen er ikke gennemgået til denne isoleringssammenligning.');
  const rows=record.observations.filter(row=>row.property==='global_warming_potential');
  if (rows.length!==4 || PHASES.some(([module])=>rows.filter(row=>row.module===module).length!==1)) throw new Error('Klimafaserne mangler eller er gentaget.');
  for (const row of rows) {
    const c=conditions(row);
    if (row.declared_unit!=='1 m² with R=1 m²K/W' || row.unit!=='kg CO2-eq' || c.reference_amount!==1 || c.reference_unit!=='m² with R=1 m²K/W' || c.record_scope!=='official_material_or_construction_reference' || c.declared_amount!==undefined || c.declared_references!==undefined) throw new Error('Isoleringsreferencens enhed eller betingelser er ændret.');
    if (row.value!==null && (typeof row.value!=='number' || !Number.isFinite(row.value))) throw new Error('Kilden har en ugyldig klimaværdi.');
  }
  return profile;
}

export function compareInsulation(a,b,area,resistance) {
  const profiles=[insulationBasis(a),insulationBasis(b)];
  if (profiles[0].form!==profiles[1].form) throw new Error('Vælg to referencer med samme form: plade/fleksibel eller løsuld/granulat.');
  if (typeof area!=='number' || !Number.isFinite(area) || area<0) throw new Error('Arealet skal være 0 m² eller mere.');
  if (typeof resistance!=='number' || !Number.isFinite(resistance) || resistance<=0) throw new Error('Isoleringsevnen R skal være større end 0 m²K/W.');
  const factor=area*resistance;
  if (!Number.isFinite(factor) || (area!==0 && factor===0)) throw new Error('Areal eller R er uden for det understøttede talområde.');
  const variants=[a,b].map(record=>({material_id:record.material.id,name:record.material.name,phases:PHASES.map(([module])=>{
    const source=observation(record,module), value=source.value===null ? null : source.value*factor;
    if (value!==null && (!Number.isFinite(value) || (factor!==0 && source.value!==0 && value===0))) throw new Error('Resultatet er uden for det understøttede talområde.');
    return {module,value:value===0 ? 0 : value,unit:'kg CO2-eq',observation_id:source.id,source_id:source.source_id};
  })}));
  const differences=PHASES.map(([module],i)=>{
    const av=variants[0].phases[i].value,bv=variants[1].phases[i].value,value=av===null || bv===null ? null : bv-av;
    if(value!==null && !Number.isFinite(value)) throw new Error('Forskellen er uden for det understøttede talområde.');
    return {module,value:value===0 ? 0 : value,unit:'kg CO2-eq'};
  });
  return {method:'br18_insulation_area_r.v1',formula:'source_value × area_m2 × resistance_m2K_W / (1 m² × 1 m²K/W)',area_m2:area,resistance_m2K_W:resistance,scaling_factor:factor,form:profiles[0].form,variants,differences,scope:'Lineær skalering af udvalgte homogene BR18-referencer ved samme areal og R for isoleringslaget. Faser separat; ingen komplet LCA, teknisk ligestilling eller eftervisning af hele konstruktionens U-værdi.',excluded:['transport','spild','montage og øvrige lag','drift','vedligehold og udskiftning','C1 og C2'],technical_status:'Brand, fugt, lyd, montage, tykkelse og egnethed skal afklares for det konkrete produkt og projekt.'};
}
