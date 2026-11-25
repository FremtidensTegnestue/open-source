import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalize,findMaterials,numberLabel,unitLabel,referenceLabel,safeURL,validateData,observation,quantityBasis,parseQuantity,quantityResult} from './core.mjs';
import {INSULATION,insulationBasis,compareInsulation} from './insulation.mjs';
import {FASTENERS,fastenerBasis,validateFasteners,fastenerResult} from './fasteners.mjs';
const data = JSON.parse(readFileSync(new URL('./materialer.json',import.meta.url),'utf8'));
const screws=JSON.parse(readFileSync(new URL('./fastgoerelser.json',import.meta.url),'utf8'));

test('two separate screw sources preserve their original edition, scope and unreported modules',()=>{
  assert.equal(validateFasteners(screws),screws);
  assert.equal(screws.observation_count,9);
  assert.equal(FASTENERS.length,2);
  const galvanized=screws.records.find(r=>r.material.name==='Galvanized steel screws');
  const stainless=screws.records.find(r=>r.material.name==='Stainless steel screws');
  const a=fastenerResult(galvanized,2.5),b=fastenerResult(stainless,2.5);
  assert.equal(a.phases[0].value,3.46125799354958*2.5);
  assert.equal(b.phases[0].value,4.18348088118257*2.5);
  assert.deepEqual(a.missing_modules,['C4']);
  assert.deepEqual(b.missing_modules,['C3','C4']);
  assert.equal(a.phases[3].value,0);
  assert.equal(b.phases[3].value,null);
  assert.equal(a.phases[5].value,-1.3690431511612*2.5);
  assert(!('total' in a));assert.deepEqual(a.excluded_modules,['A4','A5','B1-B7']);
  assert.equal(fastenerResult(stainless,0).phases[3].value,null);
});
test('screw mass calculation rejects wrong product, indicator and conflicting mass reference',()=>{
  const base=screws.records[0];
  for (const change of [
    r=>r.material.name='Steel bracket',
    r=>r.observations[0].method='GWP-fossil',
    r=>r.observations[0].declared_unit='stk',
    r=>r.observations[0].basis='1000 kg',
    r=>{const c=JSON.parse(r.observations[0].conditions_json);c.declared_references[0].amount=1000;r.observations[0].conditions_json=JSON.stringify(c);},
    r=>r.observations[0].value=NaN,
    r=>r.observations.push(r.observations[0]),
  ]) {const r=structuredClone(base);change(r);assert.throws(()=>fastenerBasis(r));}
  for(const mass of [-1,NaN,Infinity,'2']) assert.throws(()=>fastenerResult(base,mass));
  assert.throws(()=>fastenerResult(base,Number.MAX_VALUE));
  assert.throws(()=>fastenerResult(base,Number.MIN_VALUE));
});
test('screw data fetch validation rejects incomplete, duplicated, re-scoped and unlicensed editions',()=>{
  for(const change of [
    d=>d.records.pop(),d=>d.records[1]=d.records[0],d=>d.sources.pop(),
    d=>d.sources[0].license_status='unknown',d=>d.records[0].observations[0].module='C4',
    d=>d.records[0].observations[0].source_id='missing',d=>d.parquet_manifest_sha256='',
  ]) {const d=structuredClone(screws);change(d);assert.throws(()=>validateFasteners(d));}
});

test('the complete shipped excerpt resolves every material and module',() => {
  assert.equal(validateData(data),data);
  assert.equal(new Set(data.records.map(r=>r.material.id)).size,507);
  assert.equal(data.records.reduce((n,r)=>n+r.observations.length,0),2535);
});
test('Danish and keyboard-friendly spellings find the same oak; material groups are searchable',() => {
  assert.equal(normalize('TRÆ Ø Å'),'trae o a');
  assert.deepEqual(findMaterials(data.records,'EGETRÆ'),findMaterials(data.records,'egetrae'));
  assert(findMaterials(data.records,'egetræ').some(r=>r.material.id==='br18:t7:G0407:row260'));
  assert.equal(findMaterials(data.records,'isolering').filter(r=>r.material.category==='insulation').length,68);
  assert.equal(findMaterials(data.records,'ft-no-material-89').length,0);
});
test('missing, zero and negative numbers stay distinct; rounding is announced',() => {
  assert.deepEqual(numberLabel({value:null}),{text:'Ikke oplyst',approximate:false});
  assert.deepEqual(numberLabel({value:0}),{text:'0',approximate:false});
  assert.deepEqual(numberLabel({value:-664}),{text:'-664',approximate:false});
  assert.equal(numberLabel({value:-1008.75834622427}).approximate,true);
  assert.equal(numberLabel({value:0.000001}).text,'0,000001');
});
test('reference units and annual installation factors are not silently converted',() => {
  const oak = data.records.find(r=>r.material.id==='br18:t7:G0407:row260');
  const row = observation(oak,'A1-A3');
  assert.equal(referenceLabel(row),'For 1 m³');
  assert.equal(row.value,-1008.75834622427);
  const installation = data.records.find(r=>observation(r,'A1-A3').unit.includes('year'));
  assert.match(referenceLabel(observation(installation,'A1-A3')),/opvarmet kælder, pr. år/);
  assert.equal(unitLabel('kg CO2-eq/(m2 year)'),'kg CO₂e/(m² · år)');
  assert.equal(unitLabel('g/cm³'),'g/cm³');
  assert.equal(referenceLabel({declared_unit:'0.999999999999997 m²'}),'For ≈ 1 m²');
  assert.equal(referenceLabel({declared_unit:'1 m² with R=1 m²K/W'}),'For 1 m² ved varmemodstand R = 1 m²K/W');
});
test('untrusted source addresses cannot become script or file links',() => {
  for(const raw of ['javascript:alert(1)','data:text/html,test','file:///tmp/test','not a url']) assert.equal(safeURL(raw),null);
  assert.equal(safeURL('https://example.org/source'),'https://example.org/source');
});
test('incomplete editions, duplicate IDs, missing modules and broken source links fail closed',() => {
  const copy = () => structuredClone(data);
  const partial=copy();partial.records.pop();assert.throws(()=>validateData(partial));
  const duplicate=copy();duplicate.records[1]=duplicate.records[0];assert.throws(()=>validateData(duplicate));
  const module=copy();module.records[0].observations[0].module='unknown';assert.throws(()=>validateData(module));
  const source=copy();source.records[0].observations[0].source_id='missing';assert.throws(()=>validateData(source));
  const basis=copy();basis.records[0].observations[0].conditions_json=JSON.stringify({basis_source_id:'missing'});assert.throws(()=>validateData(basis));
  const missing=copy();missing.records[0].observations[0].value=undefined;assert.throws(()=>validateData(missing));
});
test('quantity input accepts Danish decimals and zero, rejecting ambiguous or out-of-range input',() => {
  for (const [raw,value] of [['2,5',2.5],['2.5',2.5],['0',0],[' 0,25 ',0.25],['.5',0.5]]) assert.equal(parseQuantity(raw),value);
  for (const raw of ['', ' ', '-1','1.000,5','1,000.5','1e3','NaN','Infinity','2 kg',true,'0.'+'0'.repeat(400)+'1','9'.repeat(400)]) assert.throws(()=>parseQuantity(raw));
});
test('real oak quantity preserves negative production, zero C4 and separate D without a grand total',() => {
  const oak=data.records.find(r=>r.material.id==='br18:t7:G0407:row260');
  const r=quantityResult(oak,2);
  assert.deepEqual(r.reference,{amount:1,unit:'m³'});
  assert.equal(r.phases.find(p=>p.module==='A1-A3').value,-2017.51669244854);
  assert.equal(r.phases.find(p=>p.module==='C4').value,0);
  assert.equal(r.phases.find(p=>p.module==='D').value,-801.568539581294);
  assert(!('total' in r));
  const missing=structuredClone(oak);observation(missing,'C4').value=null;
  assert.equal(quantityResult(missing,2).phases.find(p=>p.module==='C4').value,null);
  assert.equal(quantityResult(missing,0).phases.find(p=>p.module==='C4').value,null);
  assert.deepEqual(quantityResult(oak,0).phases.map(p=>p.value),[0,0,0,0]);
});
test('every supported shipped reference uses its original amount; qualified bases remain unavailable',() => {
  let supported=0,declined=0,nearOne=0;
  for (const record of data.records) {
    let basis;
    try {basis=quantityBasis(record);} catch {declined++;continue;}
    supported++;
    const r=quantityResult(record,basis.amount*3);
    for(const p of r.phases) assert(Math.abs(p.value-observation(record,p.module).value*3)<=Math.max(1,Math.abs(p.value))*1e-12);
    if (basis.amount!==1) {nearOne++;assert.equal(basis.amount,JSON.parse(observation(record,'A1-A3').conditions_json).reference_amount);}
  }
  assert.equal(supported,447);assert.equal(declined,60);assert.equal(nearOne,5);
  const annual=data.records.find(r=>observation(r,'A1-A3').unit.includes('year'));
  assert.throws(()=>quantityBasis(annual),/etageareal og år/);
  const insulation=data.records.find(r=>observation(r,'A1-A3').declared_unit.includes('with R='));
  assert.throws(()=>quantityBasis(insulation),/varmemodstand/);
});
test('quantity calculation refuses conflicting references, missing phases, invalid values and underflow',() => {
  const oak=data.records.find(r=>r.material.id==='br18:t7:G0407:row260');
  const conflict=structuredClone(oak),row=observation(conflict,'C3');row.conditions_json=JSON.stringify({...JSON.parse(row.conditions_json),reference_amount:1000});
  assert.throws(()=>quantityResult(conflict,2),/stemmer ikke/);
  const unit=structuredClone(oak);observation(unit,'C3').declared_unit='1 kg';
  assert.throws(()=>quantityResult(unit,2));
  const missing=structuredClone(oak);missing.observations=missing.observations.filter(r=>r.module!=='C4');assert.throws(()=>quantityResult(missing,2));
  const duplicate=structuredClone(oak);observation(duplicate,'C4').module='C3';assert.throws(()=>quantityResult(duplicate,2));
  for(const value of [-1,NaN,Infinity,'2',true]) assert.throws(()=>quantityResult(oak,value));
  assert.throws(()=>quantityResult(oak,Number.MAX_VALUE));
  const tiny=structuredClone(oak);observation(tiny,'C3').value=1e-300;assert.throws(()=>quantityResult(tiny,1e-100));
});

test('cellulose finds paper insulation and tang finds eelgrass without a rectangular duct',()=>{
  assert(findMaterials(data.records,'cellulose').some(r=>r.material.name==='Papiruldsisolering, granulat'));
  assert.deepEqual(findMaterials(data.records,'tang').map(r=>r.material.name),['Akustikpanel, ålegræs','Akustikpanel, ålegræs, brandhæmmende']);
  assert.equal(findMaterials(data.records,'tang varmeisolering').length,0);
});
test('very large and tiny numbers stay legible without rounding a nonzero value to zero',()=>{
  assert.match(numberLabel({value:1e100}).text,/E100/);
  assert.match(numberLabel({value:1e-100}).text,/E-100/);
  assert.notEqual(numberLabel({value:1e-100}).text,'0');
});
const insulation=code=>data.records.find(r=>r.material.id.includes(`:${code}:`));
test('reviewed insulation catalogue resolves 8 slab/flexible and 5 loose-fill source references',()=>{
  assert.equal(INSULATION.length,13);
  assert.equal(INSULATION.filter(p=>p.form==='plade').length,8);
  assert.equal(INSULATION.filter(p=>p.form==='loes').length,5);
  for (const p of INSULATION) assert.equal(insulationBasis(data.records.find(r=>r.material.id===p.id)),p);
  for (const code of ['D1555','D1550','D1553','D1623','D1628']) assert.throws(()=>insulationBasis(insulation(code)));
});
test('20 m² at R5 is 100 reference units: two real references and all four phase differences',()=>{
  const result=compareInsulation(insulation('D1535'),insulation('D1627'),20,5);
  const expectedA=[59.015,0,1.804,-2.322],expectedB=[-214.2,322.3,0.02739,-18.18],expectedDiff=[-273.215,322.3,-1.77661,-15.858];
  for (let i=0;i<4;i++) {
    assert(Math.abs(result.variants[0].phases[i].value-expectedA[i])<1e-10);
    assert(Math.abs(result.variants[1].phases[i].value-expectedB[i])<1e-10);
    assert(Math.abs(result.differences[i].value-expectedDiff[i])<1e-10);
  }
  assert.equal(result.scaling_factor,100);
  assert(!('total' in result) && !('winner' in result));
  assert.equal(result.differences[3].module,'D');
});
test('same reference gives zero differences; area scaling and R scaling are independent',()=>{
  const a=insulation('D1620'),b=insulation('D1621');
  const r=compareInsulation(a,b,7.5,4);
  for (const p of [compareInsulation(a,b,15,4),compareInsulation(a,b,7.5,8)]) for(let i=0;i<4;i++) assert.equal(p.variants[0].phases[i].value,2*r.variants[0].phases[i].value);
  assert(compareInsulation(a,a,20,5).differences.every(p=>p.value===0 && !Object.is(p.value,-0)));
  assert(compareInsulation(a,b,0,5).variants.every(v=>v.phases.every(p=>p.value===0)));
});
test('missing source phases remain unknown, including at zero area; source records are untouched',()=>{
  const a=structuredClone(insulation('D1535')),b=insulation('D1627'),before=JSON.stringify(b);
  observation(a,'C4').value=null;
  for (const area of [0,20]) {
    const result=compareInsulation(a,b,area,5);
    assert.equal(result.variants[0].phases[2].value,null);
    assert.equal(result.differences[2].value,null);
  }
  assert.equal(JSON.stringify(b),before);
});
test('insulation rejects conflicts, wrong forms, incomplete phases and numeric failure',()=>{
  const a=insulation('D1535'),b=insulation('D1627');
  assert.throws(()=>compareInsulation(a,insulation('D1626'),20,5),/samme form/);
  for(const [area,r] of [[-1,5],[20,0],[20,-1],[NaN,5],[20,Infinity],['20',5],[true,5],[20,'5'],[Number.MAX_VALUE,5],[1e-300,1e-300]]) assert.throws(()=>compareInsulation(a,b,area,r));
  for(const mutate of [
    r=>{observation(r,'C3').conditions_json=JSON.stringify({...conditionsForTest(r),reference_amount:2});},
    r=>{observation(r,'C3').declared_unit='1 m²';},
    r=>{observation(r,'C3').module='D';},
    r=>{r.material.name+=' changed';},
    r=>{observation(r,'C3').value=NaN;},
    r=>{r.observations=r.observations.filter(p=>p.module!=='C4');},
  ]) {const changed=structuredClone(a);mutate(changed);assert.throws(()=>compareInsulation(changed,b,20,5));}
  const tiny=structuredClone(a);observation(tiny,'C3').value=1e-300;assert.throws(()=>compareInsulation(tiny,b,1e-100,1));
});
function conditionsForTest(record) {return JSON.parse(observation(record,'C3').conditions_json);}
