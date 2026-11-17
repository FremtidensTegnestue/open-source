#!/usr/bin/env python3
"""Exercise real CAD -> GLB -> BIM -> material CLI, then revise and repeat.

Geometry is created and changed only through Solidcraft. BIMcraft imports that
geometry; material labels are restored by an explicit, hash-bound transfer map.
Expected quantities are calculated independently from dimensions and original XLSX.
"""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import json
import math
import subprocess
import sys
import time

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'data/raw/br18/table-7-2025.xlsx'
MATERIALS = {
    'concrete': {'id': 'br18:t7:B1433:row25', 'row': 25},
    'steel': {'id': 'br18:t7:D1591:row129', 'row': 129},
}
PARTS = {'ConcretePanel': 'concrete', 'Rail_A': 'steel', 'Rail_B': 'steel'}
LOG = []


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def run(label, args, expected=(0,)):
    started = time.monotonic()
    result = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, text=True, timeout=180)
    logpath = HERE / 'logs' / label
    logpath.parent.mkdir(parents=True, exist_ok=True)
    logpath.with_suffix('.stdout.txt').write_text(result.stdout)
    logpath.with_suffix('.stderr.txt').write_text(result.stderr)
    LOG.append({'step': label, 'command': [str(a) for a in args], 'returncode': result.returncode,
                'elapsed_seconds': round(time.monotonic() - started, 4)})
    save(HERE / 'command-log.json', LOG)
    if result.returncode not in expected:
        raise RuntimeError(f'{label}: exit {result.returncode}: {result.stderr or result.stdout}')
    return result


def records(reply):
    return [json.loads(s) for s in reply.stdout.splitlines() if s.strip()]


def cli(label, verb, model, out, *, software, bindings=None, mesh=False, expected=(0,)):
    args = [sys.executable, ROOT/'materials.py', verb, model, '--software', software, '--out', out]
    if bindings:
        args += ['--bindings', bindings]
    if mesh:
        args += ['--mesh-quantities']
    return run(label, args, expected)


def near(actual, expected, label, *, rel=2e-6, absolute=1e-9):
    if not math.isclose(float(actual), float(expected), rel_tol=rel, abs_tol=absolute):
        raise AssertionError(f'{label}: {actual} != {expected}')


def analytic(thickness_mm):
    # Independent of CAD evaluation and triangle integration: net planar area
    # times thickness, and two rectangular rails, using exact decimal arithmetic.
    return {'ConcretePanel': (Decimal('1.5')*Decimal('1.0')-Decimal('0.3')*Decimal('0.2')) * Decimal(thickness_mm)/1000,
            'Rail_A': Decimal('1.0')*Decimal('0.08')*Decimal('0.01'),
            'Rail_B': Decimal('1.0')*Decimal('0.08')*Decimal('0.01')}


def expected_results(thickness):
    result = {}
    for name, volume in analytic(thickness).items():
        material = MATERIALS[PARTS[name]]
        mass = volume * Decimal(str(material['density_kg_m3']))
        gwp = Decimal(str(material['gwp_A1_A3']))
        climate = volume*gwp if material['declared_unit'] == 'm³' else mass/1000*gwp
        result[name] = {'volume_m3': float(volume), 'mass_kg': float(mass), 'gwp_A1_A3_kg_CO2eq': float(climate)}
    return result


def bindings(extraction, *, bim=False):
    bound = {}
    for element in extraction['elements']:
        name = element['source_ref']['element_record']['family'] if bim else element['name']
        material = MATERIALS[PARTS[name]]
        assert element['material_name'] == material['name']
        mid = material['id']
        bound[element['id']] = {
            'material_id': mid, 'model_material_name': material['name'],
            'selection_note': 'Explicit abstract quantity/reference scenario selected in the integrated-workflow material manifest. '
                              'A rectangular rail is a quantity specimen, not a verified rolled product. '
                              'The concrete reference is not an actual delivered mix. No product equivalence, structural design or whole-building LCA is asserted.',
            'operations': ['mass', 'climate'], 'density_observation_id': mid+':mass',
            'gwp_observation_ids': [mid+':gwp:A1-A3'],
        }
    return {'schema_version': 1, 'model_sha256': extraction['model']['sha256'], 'elements': bound}


def verify_assessment(assessment, extraction, expected, *, bim=False):
    assert assessment['status'] == 'ok', assessment.get('warnings')
    byid = {e['id']: e for e in extraction['elements']}
    checks = []
    for element in assessment['elements']:
        source = byid[element['element_id']]
        name = source['source_ref']['element_record']['family'] if bim else source['name']
        reference = expected[name]
        near(source['volume_m3'], reference['volume_m3'], name+' volume')
        mass = element['calculations']['mass']
        climate = element['calculations']['climate']
        assert len(climate) == 1
        near(mass['value'], reference['mass_kg'], name+' mass')
        near(climate[0]['value'], reference['gwp_A1_A3_kg_CO2eq'], name+' climate')
        checks.append({'part': name, 'volume_m3': source['volume_m3'], 'mass_kg': mass['value'],
                       'gwp_A1_A3_kg_CO2eq': climate[0]['value'], 'status': 'passed'})
    assert set(x['part'] for x in checks) == set(PARTS)
    return checks


def totals(rows):
    return {k: math.fsum(r[k] for r in rows) for k in ('mass_kg', 'gwp_A1_A3_kg_CO2eq')}


def workflow(revision, thickness):
    folder = HERE/revision
    folder.mkdir(exist_ok=True)
    model, glb = folder/'model.sc', folder/'transfer.glb'
    if revision == 'base':
        run(revision+'-create', ['solidcraft-cli', 'run', HERE/'create-solidcraft.json', '--save', model, '--out', glb, '--results', '--param-check', 'strict'])
    else:
        run(revision+'-edit', ['solidcraft-cli', 'run', HERE/'revise-solidcraft.json', '--in', HERE/'base/model.sc', '--save', model, '--out', glb, '--results', '--param-check', 'strict'])
    model_hash = sha(model)
    evaluation = json.loads(run(revision+'-source-eval', ['solidcraft-cli', 'eval', model]).stdout)
    save(folder/'source-eval.json', evaluation)
    assert len(evaluation['bodies']) == 3 and all(x['closed'] for x in evaluation['bodies'])
    source_by_name = {b['name']: b for b in evaluation['bodies']}
    expected = expected_results(thickness)
    save(folder/'independent-reference.json', expected)
    cli(revision+'-cad-extract', 'extract', model, folder/'solid-extract.json', software='solidcraft')
    solid_extract = read(folder/'solid-extract.json')
    save(folder/'solid-bindings.json', bindings(solid_extract))
    cli(revision+'-cad-assess', 'assess', model, folder/'solid-assessment.json', software='solidcraft', bindings=folder/'solid-bindings.json')
    solid_checks = verify_assessment(read(folder/'solid-assessment.json'), solid_extract, expected)

    # A fresh BIM project on every revision is deliberate: import_mesh appends;
    # it is not a CAD link or a reload operation. No old components are carried.
    args = ['bimcraft-cli', 'run', '--cmd', 'new '+json.dumps({'name': 'Three-part material workflow '+revision}),
            '--cmd', 'import_mesh '+json.dumps({'path': str(glb)}),
            '--cmd', 'elements '+json.dumps({'category': 'component'})]
    for name in PARTS:
        args += ['--cmd', 'family '+json.dumps({'name': name})]
    args += ['--save', folder/'unbound.bimc']
    replies = records(run(revision+'-bim-import', args))
    imported = next(x for x in replies if 'left_out' in x)
    assert not imported['left_out'], imported
    component_page = next(x for x in replies if isinstance(x.get('elements'), list))
    components = component_page['elements']
    assert len(components) == 3
    families = {r['name']: r['family'] for r in replies if 'family' in r}
    assert set(families) == set(PARTS)

    # A mesh with a visual material label still has no approved physical binding.
    cli(revision+'-unbound-extract', 'extract', folder/'unbound.bimc', folder/'unbound-extract.json', software='bimcraft', mesh=True)
    unbound = read(folder/'unbound-extract.json')
    save(folder/'unbound-bindings.json', {'schema_version': 1, 'model_sha256': unbound['model']['sha256'], 'elements': {}})
    cli(revision+'-unbound-assess', 'assess', folder/'unbound.bimc', folder/'unbound-assessment.json', software='bimcraft',
        bindings=folder/'unbound-bindings.json', mesh=True, expected=(2,))
    assert all(not e['calculations'] and e['status'] == 'unresolved' for e in read(folder/'unbound-assessment.json')['elements'])

    # Restore physical meaning from the authored manifest, never from GLB colour.
    args = ['bimcraft-cli', 'run', folder/'unbound.bimc']
    for material in MATERIALS.values():
        args += ['--cmd', 'material '+json.dumps({'name': material['name']}, ensure_ascii=False)]
    for name, family in families.items():
        assert len(family['forms']) == 1
        args += ['--cmd', 'family '+json.dumps({'name': name, 'form': {'id': family['forms'][0]['id'], 'material': MATERIALS[PARTS[name]]['name']}}, ensure_ascii=False)]
    args += ['--save', folder/'model.bimc']
    run(revision+'-bim-material-map', args)
    bim_hash = sha(folder/'model.bimc')
    save(folder/'transfer-material-map.json', {
        'schema_version': 1, 'selection_mode': 'explicit_reference_scenario',
        'cad_model_sha256': model_hash, 'glb_sha256': sha(glb), 'bim_model_sha256': bim_hash,
        'manifest_sha256': sha(HERE/'material-manifest.json'),
        'parts': [{'source_body': e['family'], 'bim_element_id': e['id'], 'bim_guid': e['guid'],
                   'material_id': MATERIALS[PARTS[e['family']]]['id'], 'material_name': MATERIALS[PARTS[e['family']]]['name']} for e in components],
        'material_assignment_geometry_check': 'pending',
        'notes': ['GLB carries mesh and visual materials, not the authored physical material record.',
                  'The BIM material is assigned explicitly from this manifest; no colour/name guessing.',
                  'BIM quantities below are measured from the BIM family triangles, not copied CAD volumes.'],
    })
    cli(revision+'-bim-default-extract', 'extract', folder/'model.bimc', folder/'bim-default-extract.json', software='bimcraft')
    assert all(e['volume_m3'] is None for e in read(folder/'bim-default-extract.json')['elements'])
    cli(revision+'-bim-mesh-extract', 'extract', folder/'model.bimc', folder/'bim-extract.json', software='bimcraft', mesh=True)
    bim_extract = read(folder/'bim-extract.json')
    assert len(bim_extract['elements']) == 3
    # The family query is preserved in the quantity source, so check it against
    # the original imported family to prove that material assignment kept geometry.
    for element in bim_extract['elements']:
        name = element['source_ref']['element_record']['family']
        # Independently reread the saved family rather than depending on adapter layout.
        reply = records(run(revision+'-family-check-'+name, ['bimcraft-cli', 'run', folder/'model.bimc', '--cmd', 'family '+json.dumps({'name': name})]))
        current = next(x['family'] for x in reply if 'family' in x)
        assert current['forms'][0]['mesh'] == families[name]['forms'][0]['mesh']
        assert current['forms'][0]['material'] == MATERIALS[PARTS[name]]['name']
    transfer_map = read(folder/'transfer-material-map.json')
    transfer_map['material_assignment_geometry_check'] = 'passed'
    for part in transfer_map['parts']:
        part['mesh_unchanged_by_material_assignment'] = True
    save(folder/'transfer-material-map.json', transfer_map)
    save(folder/'bim-bindings.json', bindings(bim_extract, bim=True))
    cli(revision+'-bim-assess', 'assess', folder/'model.bimc', folder/'bim-assessment.json', software='bimcraft', bindings=folder/'bim-bindings.json', mesh=True)
    bim_checks = verify_assessment(read(folder/'bim-assessment.json'), bim_extract, expected, bim=True)

    # Back through the programs, including every placement. Solidcraft evaluates
    # the returned triangle mesh; native CAD history is not claimed to return.
    run(revision+'-bim-export', ['bimcraft-cli', 'run', folder/'model.bimc', '--save', folder/'roundtrip.glb'])
    returned = json.loads(run(revision+'-roundtrip-eval', ['solidcraft-cli', 'eval', '--in', folder/'roundtrip.glb']).stdout)
    save(folder/'roundtrip-eval.json', returned)
    assert len(returned['bodies']) == 3
    id_to_name = {str(e['id']): e['family'] for e in components}
    return_checks = []
    for body in returned['bodies']:
        name = id_to_name[body['name']]
        assert body['closed'] is True
        near(body['volume_mm3']/1e9, expected[name]['volume_m3'], name+' return volume')
        for endpoint in ('min', 'max'):
            for actual, target in zip(body['bbox'][endpoint], source_by_name[name]['bbox'][endpoint]):
                near(actual, target, name+' return '+endpoint, rel=0, absolute=0.002)
        return_checks.append({'part': name, 'closed': True, 'volume_m3': body['volume_mm3']/1e9,
                              'world_bbox_matches_within_mm': 0.002, 'returned_material': body['material'], 'status': 'passed'})
    assert sha(model) == model_hash and sha(folder/'model.bimc') == bim_hash
    run(revision+'-snapshot', ['solidcraft-cli', 'snapshot', model, '--out', folder/'model.png', '--width', '1200', '--height', '900', '--view', 'iso', '--no-grid', '--no-axes'])
    return {'thickness_mm': thickness, 'solidcraft': solid_checks, 'bimcraft': bim_checks,
            'roundtrip': return_checks, 'solidcraft_totals': totals(solid_checks), 'bimcraft_totals': totals(bim_checks),
            'expected_totals': {k: math.fsum(e[k] for e in expected.values()) for k in ('mass_kg', 'gwp_A1_A3_kg_CO2eq')},
            'component_count': 3, 'cad_sha256': model_hash, 'bim_sha256': bim_hash}


def main():
    save(HERE/'verification.json', {'status': 'running', 'started_at': datetime.now(timezone.utc).isoformat()})
    versions = {p: run('version-'+p, [p+'-cli', '--version']).stdout.strip() for p in ('solidcraft', 'bimcraft')}
    workbook = load_workbook(SOURCE, read_only=True, data_only=True)
    sheet = workbook.active
    for material in MATERIALS.values():
        row = material['row']
        material.update(name=sheet.cell(row,4).value, density_kg_m3=sheet.cell(row,11).value,
                        gwp_A1_A3=sheet.cell(row,5).value, declared_unit=sheet.cell(row,10).value)
        assert sheet.cell(row,9).value == 1 and sheet.cell(row,12).value == 'kg/m³'
    workbook.close()
    save(HERE/'material-manifest.json', {'scope': 'Abstract homogeneous reference scenario, not a verified supplied product or structural assembly.',
        'source': {'path': str(SOURCE.relative_to(ROOT)), 'sha256': sha(SOURCE)},
        'material_records': MATERIALS, 'source_body_to_material': PARTS,
        'geometry': {'plate_mm': [1500,1000,100], 'opening_mm': [300,200], 'rail_mm': [1000,80,10], 'rail_count': 2,
                     'revision': 'plate_thickness100→120mm; rail top positions follow the CAD parameter; rail dimensions unchanged'}})
    base = workflow('base', 100)
    revised = workflow('revised', 120)
    stale = cli('stale-solid-binding-rejected', 'assess', HERE/'revised/model.sc', HERE/'revised/stale-solid-result.json',
                software='solidcraft', bindings=HERE/'base/solid-bindings.json', expected=(1,))
    assert 'model_changed' in stale.stderr + stale.stdout
    stale_bim = cli('stale-bim-binding-rejected', 'assess', HERE/'revised/model.bimc', HERE/'revised/stale-bim-result.json',
                    software='bimcraft', bindings=HERE/'base/bim-bindings.json', mesh=True, expected=(1,))
    assert 'model_changed' in stale_bim.stderr + stale_bim.stdout
    delta = {k: revised['bimcraft_totals'][k]-base['bimcraft_totals'][k] for k in ('mass_kg','gwp_A1_A3_kg_CO2eq')}
    for key in delta:
        near(delta[key], revised['expected_totals'][key]-base['expected_totals'][key], 'revision delta '+key)
    summary = {'status': 'passed', 'checked_at': datetime.now(timezone.utc).isoformat(), 'versions': versions,
        'workflow': ['Solidcraft parametric CAD','GLB export','BIMcraft generic mesh import','explicit material manifest',
                     'material CLI closed mesh quantities','source-bound mass and A1-A3 climate','BIM GLB export','Solidcraft roundtrip evaluation'],
        'base': base, 'revised': revised, 'change': delta, 'stale_bindings_rejected': {'solidcraft': True, 'bimcraft': True},
        'limits': ['Generic imported meshes, not native BIM walls/floors or retained CAD parameter history.',
                   'Physical material meaning is deliberately restored using the authored manifest.',
                   'Revision creates a fresh BIM project; no automatic synchronization or merge.',
                   'Mesh checks cover closure, winding and connectivity, not arbitrary self-intersection.',
                   'Reference scenario only; no product equivalence or structural verification.']}
    save(HERE/'verification.json', summary)
    print(json.dumps({'status':'passed','base':base['bimcraft_totals'],'revised':revised['bimcraft_totals'],'change':delta},ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        save(HERE/'verification.json', {'status': 'failed', 'error': str(exc)})
        raise
