import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import materials
import material_calculations as calc

class CalculationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.db=__import__('sqlite3').connect(':memory:');self.db.row_factory=__import__('sqlite3').Row;self.addCleanup(self.db.close)
        self.db.executescript(materials.SCHEMA)
        self.db.execute("INSERT INTO datasets VALUES ('test','{}')")
        self.db.execute("INSERT INTO sources VALUES ('source','test','Reference table','Publisher','https://example.org/source','2026-11-17','source.txt','hash','text/plain','unknown','unknown','{}')")
        for mid in ['test:wood','test:steel']:
            self.db.execute('INSERT INTO materials VALUES (?,?,?,?,?,?,?,?,?,?,?)',(mid,'test',mid,'generic','wood','[]','test','source','Table1','wood','{}'))
        self.add('density','density',470,'kg/m³')
        self.add('coefficient','moisture_dimensional_change_coefficient_tangential',.00245,'1/%MC',conditions={'valid_moisture_content_percent_min':6,'valid_moisture_content_percent_max':14})
        self.add('gwp','global_warming_potential',1639,'kg CO2-eq',basis='1 ton',module='A1-A3')
        self.add('D','global_warming_potential',-100,'kg CO2-eq',basis='1 ton',module='D')
    def add(self,oid,prop,value,unit,conditions=None,basis=None,module=None):
        self.db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(oid,'test','test:wood',prop,value,str(value),unit,module,basis,None,'test method','reported',json.dumps(conditions or {}),'source','Table1 row1','{}'))
    def test_mass_power_units_and_citation(self):
        r=calc.calculate(self.db,dict(kind='mass',material_id='test:wood',density_observation_id='density',quantity={'value':1e6,'unit':'mm3'}))
        self.assertAlmostEqual(r['value'],.47)
        self.assertEqual(r['inputs']['density']['citation']['source_locator'],'Table1 row1')
        with self.assertRaisesRegex(ValueError,'another material'):
            calc.calculate(self.db,dict(kind='mass',material_id='test:steel',density_observation_id='density',quantity={'value':1,'unit':'m3'}))
    def test_climate_metric_tonne_and_negative_module_are_separate(self):
        for oid,expected in [('gwp',3278),('D',-200)]:
            r=calc.calculate(self.db,dict(kind='climate',material_id='test:wood',gwp_observation_id=oid,quantity={'value':2000,'unit':'kg'}))
            self.assertAlmostEqual(r['value'],expected)
            self.assertEqual(r['module'],'D' if oid=='D' else 'A1-A3')
    def test_reference_1000kg_and_thermalR_are_not_stripped(self):
        self.add('1000','gwp_total',17,'kg CO2-eq',basis='1000 kg',module='A1-A3')
        r=calc.calculate(self.db,dict(kind='climate',material_id='test:wood',gwp_observation_id='1000',quantity={'value':500,'unit':'kg'}))
        self.assertEqual(r['value'],8.5)
        self.add('R','global_warming_potential',1,'kg CO2-eq',basis='1 m² with R=1 m²K/W',module='A1-A3')
        with self.assertRaises(calc.CalculationError):calc.reference_basis(calc.observation(self.db,'R','test:wood'))
    def test_ilcd_declared_amount_is_explicit_and_not_exchange_amount1(self):
        self.add('ilcd','gwp',859,'kg CO_(2)-Äq.',basis='kg',module='A1',conditions={'declared_amount':1000,'declared_references':[{'amount':1000,'unit':'kg','exchange_mean_amount':1}]})
        r=calc.calculate(self.db,dict(kind='climate',material_id='test:wood',gwp_observation_id='ilcd',quantity={'value':500,'unit':'kg'}))
        self.assertEqual(r['value'],429.5)
        self.add('ambig','gwp',1,'kg CO2-eq',basis='kg',module='A1',conditions={'declared_amount':1000,'declared_references':[{'amount':1,'unit':'kg'}]})
        with self.assertRaises(calc.CalculationError):calc.reference_basis(calc.observation(self.db,'ambig','test:wood'))
    def test_shared_climate_scaling_contract(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/climate-scaling.json').read_text(encoding='utf-8'))
        for case in fixture['cases']:
            with self.subTest(case=case['id']):
                source=fixture['observation_defaults'] | case['source']
                oid='scaling:'+case['id']
                self.add(oid,source['property'],source['value'],source['unit'],
                         conditions=source['conditions'],basis=source['declared_unit'],module=source['module'])
                request=dict(kind='climate',material_id='test:wood',gwp_observation_id=oid,quantity=case['quantity'])
                if case.get('error'):
                    with self.assertRaises(ValueError):calc.calculate(self.db,request)
                else:
                    result=calc.calculate(self.db,request)
                    self.assertAlmostEqual(result['value'],case['value'],delta=max(1e-12,abs(case['value'])*1e-12))
                    self.assertEqual(result['module'],source['module'])
                    self.assertEqual(result['indicator'],source['property'])
    def test_moisture_matches_published_example_and_range(self):
        q=dict(kind='moisture',material_id='test:wood',coefficient_observation_id='coefficient',dimension={'value':232,'unit':'mm'},initial_moisture_percent=8,final_moisture_percent=11,direction='tangential')
        r=calc.calculate(self.db,q);self.assertAlmostEqual(r['value'],.0017052)
        self.assertAlmostEqual(r['final_dimension_m'],.2337052)
        with self.assertRaisesRegex(ValueError,'within source range'):calc.calculate(self.db,dict(q,final_moisture_percent=20))
        with self.assertRaisesRegex(ValueError,'matching dimensional-change'):calc.calculate(self.db,dict(q,direction='radial'))
    def model(self):
        return {'schema_version':1,'software':'bimcraft','software_version':'test','model':{'path':'a.bimc','sha256':'known'},'extraction':{},'warnings':[], 'elements':[{'id':'1','name':'test','material_name':'wood','volume_m3':.1,'area_m2':1,'dimensions_m':{'x':.232},'source_ref':{'volume_rounding_increment_m3':.001}}]}
    def bindings(self):
        return {'schema_version':1,'model_sha256':'known','elements':{'1':dict(material_id='test:wood',model_material_name='wood',selection_note='Explicit test scenario',density_observation_id='density',gwp_observation_ids=['gwp','D'])}}
    def test_explicit_binding_checksum_and_unknown_material(self):
        m=self.model();b=self.bindings();r=calc.assess(self.db,m,b)
        self.assertEqual(r['status'],'ok')
        self.assertAlmostEqual(r['elements'][0]['calculations']['mass']['model_quantity_rounding_bound_kg'],.235)
        with self.assertRaisesRegex(ValueError,'SHA-256'):calc.assess(self.db,m,dict(b,model_sha256='changed'))
        m['elements'][0]['material_name']=None;r=calc.assess(self.db,m,b)
        self.assertEqual(r['status'],'partial');self.assertFalse(r['elements'][0]['calculations'])
    def test_area_needs_explicit_semantic_confirmation(self):
        self.add('area','global_warming_potential',2,'kg CO2-eq',basis='1 m²',module='A1-A3')
        m=self.model();b=self.bindings();b['elements']['1']['gwp_observation_ids']=['area']
        r=calc.assess(self.db,m,b);self.assertEqual(r['elements'][0]['calculations']['climate'][0]['status'],'unavailable')
        b['elements']['1']['area_basis_note']='Reference area deliberately represented by model area in this control'
        r=calc.assess(self.db,m,b);self.assertEqual(r['elements'][0]['calculations']['climate'][0]['value'],2)
    def test_omitted_import_content_blocks_global_success(self):
        m=self.model();m['warnings']=[{'code':'bimcraft_model_warning','message':'Importer omitted two unsupported elements'}]
        r=calc.assess(self.db,m,self.bindings());self.assertEqual(r['status'],'partial')
        m['warnings']=[{'code':'quantity_rounding','severity':'notice','message':'Rounded at documented precision'}]
        self.assertEqual(calc.assess(self.db,m,self.bindings())['status'],'ok')
    def test_source_ambiguous_and_area_mass_are_rejected(self):
        self.add('bad','density',1,'source_ambiguous')
        with self.assertRaises(ValueError):calc.mass(self.db,dict(material_id='test:wood',density_observation_id='bad',quantity={'value':1,'unit':'m3'}))
        self.add('area-mass','mass_factor',1,'kg/m²')
        with self.assertRaises(ValueError):calc.mass(self.db,dict(material_id='test:wood',density_observation_id='area-mass',quantity={'value':1,'unit':'m3'}))
    def test_missing_inputs_and_zero_resolution_are_not_success(self):
        with self.assertRaises(calc.CalculationError):calc.calculate(self.db,dict(kind='mass'))
        m=self.model();m['elements'][0]['volume_m3']=0
        r=calc.assess(self.db,m,self.bindings());self.assertEqual(r['status'],'partial')
        self.assertEqual(r['elements'][0]['calculations']['mass']['status'],'unavailable')

if __name__=='__main__':unittest.main()
