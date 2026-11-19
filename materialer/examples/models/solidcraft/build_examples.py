#!/usr/bin/env python3
"""Create six explicit-material Solidcraft controls and an unspecified-material guard.

App-assigned density is only demonstrative. Material-database calculations must
select their own cited observations and may not silently reuse these densities.
"""
from pathlib import Path
import sys
import json
import subprocess

HERE = Path(__file__).resolve().parent
CASES = [
    {'id':'solid-wood','material':'Krydslamineret træ, CLT (Forbrænding EoL)','body':'WoodControl','dimensions_mm':[1000,500,100],'expected_volume_m3':0.05,'assigned_density_g_cm3':0.47},
    {'id':'solid-concrete','material':'Fabriksbeton (C25/30) i eksponeringsklasserne X0 og XC1','body':'ConcreteControl','dimensions_mm':[2000,300,200],'expected_volume_m3':0.12,'assigned_density_g_cm3':2.246},
    {'id':'solid-steel','material':'Konstruktionsstål, valsede profiler, lille forarbejdning','body':'SteelControl','dimensions_mm':[800,100,20],'expected_volume_m3':0.0016,'assigned_density_g_cm3':7.85},
    {'id':'solid-glass','material':'Glasbyggesten','body':'GlassControl','dimensions_mm':[1200,800,8],'expected_volume_m3':0.00768,'assigned_density_g_cm3':2.5},
    {'id':'solid-wood-moisture','material':'Fir, white','body':'WoodMoistureControl','dimensions_mm':[232,20,10],'expected_volume_m3':0.0000464,'assigned_density_g_cm3':0.4,'purpose':'Additional moisture specimen; x is explicitly assumed tangential width in the calculation request, not inferred by the adapter'},
    {'id':'solid-insulation','material':'Polystyren skumfyldning (uden bindemiddel)','body':'InsulationControl','dimensions_mm':[1500,600,150],'expected_volume_m3':0.135,'assigned_density_g_cm3':0.015},
]


def main():
    expected=[]
    for item in CASES:
        length,width,height=item['dimensions_mm']
        commands=[
            {'command':'solid.box','params':{'length':length,'width':width,'height':height,'body_name':item['body']}},
            {'command':'material.create','params':{'name':item['material'],'density_g_cm3':item['assigned_density_g_cm3']}},
            {'command':'material.assign','params':{'bodies':[item['body']],'material':item['material']}},
        ]
        script=HERE/(item['id']+'.commands.json');model=HERE/(item['id']+'.sc')
        script.write_text(json.dumps({'commands':commands},indent=2)+'\n')
        made=subprocess.run(['solidcraft-cli','run',str(script),'--save',str(model),'--results'],check=True,capture_output=True,text=True)
        (HERE/(item['id']+'.creation-reply.json')).write_text(made.stdout)
        measured=subprocess.run(['solidcraft-cli','eval',str(model)],check=True,capture_output=True,text=True)
        (HERE/(item['id']+'.eval.json')).write_text(measured.stdout)
        expected.append(item | {'model':str(model.name),'element_id':'solidcraft:'+item['body'],'expected_formula':'length_mm * width_mm * height_mm / 1000000000','reference_kind':'analytical rectangular-solid volume; dimensions authored explicitly'})
    unknown={'commands':[{'command':'solid.box','params':{'length':100,'width':100,'height':100,'body_name':'Unspecified'}}]}
    (HERE/'unknown.commands.json').write_text(json.dumps(unknown,indent=2)+'\n')
    subprocess.run(['solidcraft-cli','run',str(HERE/'unknown.commands.json'),'--save',str(HERE/'unknown.sc'),'--quiet'],check=True)
    (HERE/'expected.json').write_text(json.dumps({'software':'solidcraft','cases':expected,'guard_model':'unknown.sc','expected_guard_warning':'material_unspecified'},indent=2)+'\n')
    sys.path.insert(0,str(HERE.parents[2]))
    from adapters.solidcraft import extract
    for model in [*(HERE/case['model'] for case in expected),HERE/'unknown.sc']:
        model.with_suffix('.normalized.json').write_text(json.dumps(extract(model),ensure_ascii=False,indent=2)+'\n')
    print('Created six control models and one material-unspecified guard')

if __name__=='__main__':main()
