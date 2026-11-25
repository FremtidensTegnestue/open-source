import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalize,findMaterials,numberLabel,unitLabel,referenceLabel,safeURL,validateData,observation,quantityBasis,parseQuantity,quantityResult} from './core.mjs';
const data = JSON.parse(readFileSync(new URL('./materialer.json',import.meta.url),'utf8'));

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
