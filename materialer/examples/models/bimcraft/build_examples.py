#!/usr/bin/env python3
"""Author reproducible BIM quantity specimens; dimensions are analytical controls.

These are homogeneous rectangular floor specimens for checking the extraction
chain, not suggested real building assemblies or engineering design specimens.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from adapters.bimcraft import extract

CASES = [
    ('wood','Krydslamineret træ, CLT (Forbrænding EoL)',2000,1000,50,'br18:t7:B1318:row2'),
    ('concrete','Fabriksbeton (C25/30) i eksponeringsklasserne X0 og XC1',1200,800,100,'br18:t7:B1433:row25'),
    ('steel','Konstruktionsstål, valsede profiler, lille forarbejdning',1000,500,10,'br18:t7:D1591:row129'),
    ('glass','Glasbyggesten',1000,600,10,'br18:t7:G0954:row410'),
    ('insulation','Polystyren skumfyldning (uden bindemiddel)',1500,800,120,'br18:t7:G0161:row196'),
]

def command(name,params):return name+' '+json.dumps(params,ensure_ascii=False,separators=(',',':'))
def build(label,commands,ifc=False):
    script=HERE/(label+'.commands.txt')
    script.write_text('\n'.join(commands)+'\n')
    argv=['bimcraft-cli','run','--script',str(script),'--save',str(HERE/(label+'.bimc'))]
    if ifc:argv+=['--save',str(HERE/(label+'.ifc'))]
    reply=subprocess.run(argv,capture_output=True,text=True,check=True)
    (HERE/(label+'.build.raw.jsonl')).write_text(reply.stdout)
    inspection=subprocess.run(['bimcraft-cli','run',str(HERE/(label+'.bimc')),'--cmd','inspect {}','--cmd','elements {"limit":1000,"offset":0}'],capture_output=True,text=True,check=True)
    (HERE/(label+'.inspect.raw.jsonl')).write_text(inspection.stdout)
    out=extract(HERE/(label+'.bimc'))
    (HERE/(label+'.extracted.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    return out

def main():
    commands=[command('new',{'name':'Five homogeneous material quantity controls'})]
    expected=[]
    for index,(case,name,x,y,t,mid) in enumerate(CASES):
        x0=index*3000
        commands += [command('material',{'name':name}),command('type',{'category':'floor','name':case+' specimen','layers':[{'function':'structure','material':name,'thickness':t}]}),command('floor',{'boundary':[[x0,0],[x0+x,0],[x0+x,y],[x0,y]],'type':case+' specimen','level':'Level 1'})]
        expected.append({'case_id':'bimcraft-'+case,'name':case+' specimen','material_name':name,'material_record_id':mid,'dimensions_mm':{'length':x,'width':y,'thickness':t},'expected_volume_m3':x*y*t/1e9,'expected_plan_area_m2':x*y/1e6,'formula':'length_mm * width_mm * thickness_mm / 1e9','assumption':'Homogeneous rectangular floor quantity specimen, without openings or joins; material identity is an explicit reference scenario, not a product verification.'})
    out=build('controls',commands,ifc=True)
    byname={e['name']:e for e in out['elements']}
    for ex in expected:
        actual=byname[ex['name']]
        assert actual['material_name']==ex['material_name']
        assert abs(actual['volume_m3']-ex['expected_volume_m3'])<1e-12
        ex.update(element_id=actual['id'],element_guid=actual['source_ref']['guid'],model='examples/models/bimcraft/controls.bimc')
    assert all(w['code']=='quantity_rounding' for w in out['warnings']),out['warnings']
    # A valid model with actual volume but no material: assignment must remain unknown.
    missing=build('missing-material',[
        command('new',{'name':'Missing material control'}),
        command('type',{'category':'floor','name':'Unassigned specimen','thickness':20}),
        command('floor',{'boundary':[[0,0],[1000,0],[1000,300],[0,300]],'type':'Unassigned specimen','level':'Level 1'}),
    ])
    assert missing['elements'][0]['material_name'] is None
    assert any(w['code']=='missing_material' for w in missing['warnings'])
    # Mixed layers carry a real total volume but it must not be assigned wholly to either layer.
    mixed=build('mixed-layers',[
        command('new',{'name':'Mixed material control'}),
        command('type',{'category':'floor','name':'Mixed specimen','layers':[{'function':'finish','material':'Timber','thickness':20},{'function':'structure','material':'Concrete','thickness':100}]}),
        command('floor',{'boundary':[[0,0],[1000,0],[1000,300],[0,300]],'type':'Mixed specimen','level':'Level 1'}),
    ])
    assert mixed['elements'][0]['material_name'] is None
    assert any(w['code']=='mixed_material_layers' for w in mixed['warnings'])
    # Source CLI rounding regression: keep the loss visible, not corrected by geometry.
    rounded=build('rounded-volume',[
        command('new',{'name':'Volume rounding control'}),
        command('type',{'category':'floor','name':'Thin glass specimen','layers':[{'function':'structure','material':'Glass','thickness':8}]}),
        command('floor',{'boundary':[[0,0],[1000,0],[1000,600],[0,600]],'type':'Thin glass specimen','level':'Level 1'}),
    ],ifc=True)
    assert rounded['elements'][0]['volume_m3']==0.005
    assert rounded['elements'][0]['source_ref']['volume_rounding_increment_m3']==0.001
    (HERE/'rounding-regression.json').write_text(json.dumps({'model':'examples/models/bimcraft/rounded-volume.bimc','analytical_volume_m3':0.0048,'reported_volume_m3':rounded['elements'][0]['volume_m3'],'reporting_increment_m3':0.001,'dimensions_mm':[1000,600,8],'note':'The adapter preserves the CLI rounded quantity. The program IFC export contains full0.0048 but is not substituted by this adapter.'},indent=2)+'\n')
    (HERE/'expected.json').write_text(json.dumps({'software':'bimcraft','cases':expected,'negative_controls':['missing-material.bimc','mixed-layers.bimc'],'model_units':'mm; reported area_m2 and volume_m3 retain SI units','notes':'Expected quantities are derived independently from authored dimensions, not copied from CLI quantity results.'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':len(expected),'warnings_positive':out['warnings'],'negative_controls_verified':2},ensure_ascii=False))

if __name__=='__main__':main()
