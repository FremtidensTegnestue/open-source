#!/usr/bin/env python3
"""Read BIMcraft model quantities without writing the source project.

The adapter uses the installed CLI's `inspect` and paginated `elements` commands.
Volumes and areas are BIMcraft's reported quantities, already m3 and m2. Length
fields and type/layer thicknesses are reported by that API in millimetres.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from report_io import write_report

NON_MATERIAL_CATEGORIES = {
    'level', 'grid', 'view', 'sheet', 'schedule', 'text', 'dimension', 'tag',
    'section', 'elevation', 'detail_line', 'model_line', 'reference_plane',
    'property_line', 'camera', 'image', 'point_cloud',
}

MESH_WELD_TOLERANCE_MM = 0.00001
DEFAULT_MESH_PLANE = '9e3c0a10-1f0b-4d8c-8a5e-0000000000a1'
MESH_LIMITS = 'One unparameterized generic family mesh in the default reference plane; rigid instance placement only. Self-intersections are not checked; tessellation differs from the original CAD solid.'


def _mesh_volume(mesh):
    """Volume of one closed, consistently oriented triangle shell, in m3.

    Tight vertex welding permits repeated mesh coordinates. It does not repair
    open meshes, reverse faces, combine separate shells or test intersections.
    """
    if not isinstance(mesh, list) or not mesh:
        raise ValueError('Family form has no triangle mesh')
    tolerance = MESH_WELD_TOLERANCE_MM
    buckets, vertices, faces = defaultdict(list), [], []
    for triangle in mesh:
        if not isinstance(triangle, list) or len(triangle) != 3:
            raise ValueError('Mesh must contain 3-vertex triangles')
        face = []
        for point in triangle:
            if not isinstance(point, list) or len(point) != 3 or any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) for x in point):
                raise ValueError('Mesh vertices must have three finite coordinates in mm')
            key = tuple(math.floor(x / tolerance) for x in point)
            match = None
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for index in buckets.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                            if math.dist(point, vertices[index]) <= tolerance:
                                match = index
                                break
                        if match is not None:
                            break
                    if match is not None:
                        break
                if match is not None:
                    break
            if match is None:
                match = len(vertices)
                vertices.append(tuple(point))
                buckets[key].append(match)
            face.append(match)
        a, b, c = (vertices[i] for i in face)
        u, v = tuple(b[i] - a[i] for i in range(3)), tuple(c[i] - a[i] for i in range(3))
        cross = (u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2], u[0]*v[1] - u[1]*v[0])
        if len(set(face)) != 3 or not all(math.isfinite(x) for x in cross) or math.hypot(*cross) <= tolerance*tolerance:
            raise ValueError('Mesh contains a degenerate triangle after vertex welding')
        faces.append(face)
    edges, incident = defaultdict(list), defaultdict(set)
    for index, face in enumerate(faces):
        for vertex in face:
            incident[vertex].add(index)
        for a, b in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((a, b)))].append((index, a, b))
    neighbors = [set() for _ in faces]
    fans = defaultdict(lambda: defaultdict(set))
    for edge, uses in edges.items():
        if len(uses) != 2:
            raise ValueError('Mesh is open or nonmanifold: every edge must have exactly two faces')
        first, second = uses
        if (first[1], first[2]) != (second[2], second[1]):
            raise ValueError('Mesh has inconsistent triangle winding across an edge')
        neighbors[first[0]].add(second[0])
        neighbors[second[0]].add(first[0])
        for vertex in edge:
            fans[vertex][first[0]].add(second[0])
            fans[vertex][second[0]].add(first[0])

    def connected(start, adjacency):
        seen, pending = {start}, [start]
        while pending:
            for other in adjacency[pending.pop()]:
                if other not in seen:
                    seen.add(other)
                    pending.append(other)
        return seen

    if len(connected(0, neighbors)) != len(faces):
        raise ValueError('Mesh has disconnected shells; only one connected shell is supported')
    for vertex, attached in incident.items():
        if connected(next(iter(attached)), fans[vertex]) != attached:
            raise ValueError('Mesh has a nonmanifold vertex')
    origin = vertices[0]
    points = [tuple((p[i] - origin[i]) / 1000.0 for i in range(3)) for p in vertices]
    terms = []
    for face in faces:
        a, b, c = (points[i] for i in face)
        terms.append((a[0]*(b[1]*c[2] - b[2]*c[1]) + a[1]*(b[2]*c[0] - b[0]*c[2]) + a[2]*(b[0]*c[1] - b[1]*c[0])) / 6.0)
    volume = abs(math.fsum(terms))
    if not math.isfinite(volume) or volume <= 0:
        raise ValueError('Mesh has no finite positive enclosed volume')
    return volume


def _family_mesh_quantity(row, reply):
    """Bound support to the actual BIMcraft 0.12 import_mesh family contract."""
    if not isinstance(reply, dict) or not isinstance(reply.get('family'), dict):
        raise ValueError('BIMcraft did not return this family definition')
    if reply.get('warnings'):
        raise ValueError('Family definition has BIMcraft warnings requiring review')
    family = reply['family']
    if family.get('category') != 'generic' or family.get('parameters') != []:
        raise ValueError('Only unparameterized generic families support mesh quantities')
    if set(family) - {'category', 'parameters', 'types', 'forms', 'planes'}:
        raise ValueError('Unsupported family context beyond the imported mesh contract')
    family_type = row.get('type')
    types, values = family.get('types'), reply.get('values', {})
    if not isinstance(types, dict) or types.get(family_type) != {} or any(v != {} for v in types.values()):
        raise ValueError('Family type has parameters or no matching empty type')
    if not isinstance(values, dict) or any(v != {} for v in values.values()) or row.get('values', {}) != {}:
        raise ValueError('Family or instance parameter values are unsupported')
    instance_fields = {'id', 'guid', 'name', 'mark', 'category', 'family', 'family_guid', 'type', 'values', 'angle', 'at', 'level', 'offset', 'offset_from_host', 'shared_east', 'shared_north', 'shared_elevation', 'height', 'work_plane', 'material', 'area_m2', 'volume_m3', 'mirrored'}
    if set(row) - instance_fields:
        raise ValueError('Unsupported component instance fields; scaling or geometry modifications cannot be assumed rigid')
    if row.get('category') != 'component' or reply.get('name') != row.get('family'):
        raise ValueError('Family definition does not match this component')
    for field in ('angle', 'offset', 'offset_from_host', 'shared_east', 'shared_north', 'shared_elevation', 'height'):
        if field in row and (not isinstance(row[field], (int, float)) or isinstance(row[field], bool) or not math.isfinite(row[field])):
            raise ValueError('Component placement must be finite')
    if 'at' in row and (not isinstance(row['at'], list) or len(row['at']) != 2 or any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) for x in row['at'])):
        raise ValueError('Component placement must contain two finite coordinates')
    if 'mirrored' in row and not isinstance(row['mirrored'], bool):
        raise ValueError('Component mirror flag must be boolean')
    options = reply.get('options', {})
    if not isinstance(options, dict) or options.get('cut_with_voids_when_loaded', False) or options.get('work_plane_based', False):
        raise ValueError('Cutting or work-plane-based family options are unsupported')
    if set(options) - {'always_vertical', 'cut_in_views', 'cut_with_voids_when_loaded', 'default_elevation', 'omniclass', 'room_calculation_point', 'shared', 'work_plane_based'}:
        raise ValueError('Unsupported family options beyond the imported mesh contract')
    forms = family.get('forms')
    if not isinstance(forms, list) or len(forms) != 1 or not isinstance(forms[0], dict):
        raise ValueError('Exactly one solid mesh form is required; additional forms and voids are unsupported')
    form = forms[0]
    if not isinstance(form.get('guid'), str) or not form['guid']:
        raise ValueError('Mesh form has no source GUID')
    if set(form) - {'id', 'guid', 'host', 'from', 'to', 'material', 'mesh', 'visible', 'void'} or form.get('visible', True) is not True or form.get('void', False) is not False:
        raise ValueError('Unsupported form context, void or conditional visibility')
    if form.get('host') != {'plane': DEFAULT_MESH_PLANE} or form.get('from') != 0 or form.get('to') != 0:
        raise ValueError('Mesh form must use the unmodified default reference plane')
    planes = family.get('planes')
    plane = next((p for p in planes if isinstance(p, dict) and p.get('guid') == DEFAULT_MESH_PLANE), None) if isinstance(planes, list) else None
    if plane is None or plane.get('start') != [-1000, 0, 0] or plane.get('end') != [1000, 0, 0] or plane.get('up') != [0, 1000, 0] or plane.get('defines_origin') is not True or plane.get('level') is not True:
        raise ValueError('Family default reference plane is missing or modified')
    volume = _mesh_volume(form.get('mesh'))
    # A body or family label is not a physical material assignment.
    material, problem = _material({'material': form.get('material')}, {})
    source = {
        'quantity_api': 'bimcraft-cli family mesh',
        'quantity_fields': {'volume': 'family.forms[].mesh', 'area': 'area_m2'},
        'volume_method': 'absolute oriented tetrahedron sum about translated origin; math.fsum; mm to m before integration',
        'family_name': row.get('family'), 'family_type': family_type,
        'source_form_id': form.get('id'), 'source_form_guid': form.get('guid'),
        'triangle_count': len(form['mesh']), 'vertex_welding_tolerance_mm': MESH_WELD_TOLERANCE_MM,
        'mesh_quantity_limits': MESH_LIMITS, 'self_intersection_checked': False,
        'material_assignment': 'explicit family form material' if material is not None else None,
        'material_source_field': 'family.forms[].material',
    }
    return volume, material, problem, source


def _sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _run(command, timeout):
    reply = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if reply.returncode:
        raise ValueError('BIMcraft command failed: ' + (reply.stderr or reply.stdout).strip())
    records = []
    for line in reply.stdout.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError('BIMcraft emitted non-JSON output') from exc
        if isinstance(record, dict) and record.get('error'):
            raise ValueError('BIMcraft reported error: ' + str(record['error']))
        records.append(record)
    return records


def _finite_nonnegative(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _type_record(inspect, row):
    category, name = row.get('category'), row.get('type')
    types = inspect.get('types', {})
    for key in (category, {'structuralcolumn': 'structural_column'}.get(category)):
        if key and isinstance(types.get(key), dict) and name in types[key]:
            return types[key][name], ['types', key, name]
    for key in (category,):
        if key and isinstance(types.get('runs', {}).get(key), dict) and name in types['runs'][key]:
            return types['runs'][key][name], ['types', 'runs', key, name]
    return {}, None


def _material(row, type_record):
    """Resolve only explicit assignment; never guess from type/family names."""
    layers = type_record.get('layers')
    if isinstance(layers, list) and layers:
        active = [l for l in layers if isinstance(l, dict) and _finite_nonnegative(l.get('thickness')) and l['thickness'] > 0]
        if not active:
            return None, 'No positive-thickness material layer is explicitly assigned.'
        if any(not isinstance(l.get('material'), str) or not l['material'].strip() for l in active):
            return None, 'One or more positive-thickness layers has no explicit material.'
        names = {l['material'] for l in active}
        if len(names) > 1:
            return None, 'Mixed-material layers: total volume is not allocated to any single material.'
        return next(iter(names)), None
    direct = row.get('material')
    if isinstance(direct, str) and direct.strip():
        return direct, None
    direct = type_record.get('material')
    if isinstance(direct, str) and direct.strip():
        return direct, None
    return None, 'No explicit homogeneous material assignment was reported.'


def normalize(inspect, rows, model, version, commands, import_summary=None, *, mesh_quantities=False, family_replies=None, family_lookup_errors=None):
    """Normalize already-read CLI quantities; useful for deterministic unit tests."""
    elements, warnings = [], []
    if import_summary is not None:
        skipped = import_summary.get('skipped', [])
        if skipped:
            warnings.append({'code': 'ifc_import_skipped', 'message': f'BIMcraft skipped {len(skipped)} IFC entities during import; quantities do not cover those entities.', 'count': len(skipped)})
        generic = import_summary.get('generic', 0)
        if generic:
            warnings.append({'code': 'ifc_import_generic', 'message': f'BIMcraft imported {generic} IFC entities as generic representations; review their quantities and assignments.', 'count': generic})
    for w in inspect.get('warnings', []):
        warnings.append({'code': 'bimcraft_model_warning', 'message': str(w)})
    for row in rows:
        if row.get('category') in NON_MATERIAL_CATEGORIES:
            continue
        element_id = str(row.get('id', row.get('guid', '')))
        if not element_id:
            raise ValueError('BIMcraft returned an element without stable id or GUID')
        type_record, type_path = _type_record(inspect, row)
        material_name, material_problem = _material(row, type_record)
        volume = row.get('volume_m3')
        mesh_source = {}
        if mesh_quantities and row.get('category') == 'component' and not _finite_nonnegative(volume):
            try:
                family_name = row.get('family')
                lookup_problem = (family_lookup_errors or {}).get(family_name)
                if lookup_problem:
                    raise ValueError(lookup_problem)
                volume, material_name, material_problem, mesh_source = _family_mesh_quantity(row, (family_replies or {}).get(family_name))
                warnings.append({'code': 'mesh_quantity_limits', 'severity': 'notice', 'message': MESH_LIMITS, 'element_id': element_id})
            except (ValueError, OverflowError, TypeError) as exc:
                volume = None
                warnings.append({'code': 'unsupported_mesh_quantity', 'message': str(exc), 'element_id': element_id})
        if material_problem:
            code = 'mixed_material_layers' if material_problem.startswith('Mixed-material') else 'missing_material'
            warnings.append({'code': code, 'message': material_problem, 'element_id': element_id})
        if not _finite_nonnegative(volume):
            volume = None
            warnings.append({'code': 'missing_volume', 'message': 'BIMcraft did not report a finite nonnegative volume_m3; no geometric estimate was substituted.', 'element_id': element_id})
        if volume is not None and row.get('category') == 'floor':
            warnings.append({'code': 'quantity_rounding', 'severity': 'notice', 'message': 'BIMcraft 0.12 elements reports floor volume rounded to 0.001 m3; retain the reporting precision in downstream calculations.', 'element_id': element_id})
        area = row.get('area_m2')
        if not _finite_nonnegative(area):
            area = None
        dimensions = {}
        for key in ('length', 'width', 'height', 'thickness'):
            value = row.get(key)
            if _finite_nonnegative(value):
                dimensions[key] = value / 1000.0
        elements.append({
            'id': element_id,
            'name': str(row.get('name') or row.get('mark') or row.get('type') or row.get('category') or element_id),
            'material_name': material_name,
            'volume_m3': volume,
            'area_m2': area,
            'dimensions_m': dimensions or None,
            'category': row.get('category'),
            'source_ref': {
                'element_id': row.get('id'), 'guid': row.get('guid'),
                'quantity_api': 'bimcraft-cli elements',
                'quantity_fields': {'volume': 'volume_m3', 'area': 'area_m2'},
                'volume_rounding_increment_m3': 0.001 if row.get('category') == 'floor' and volume is not None else None,
                'area_semantics': 'BIMcraft category-specific reported area; not assumed exterior or total surface area',
                'source_length_unit': 'mm', 'volume_unit': 'm3', 'area_unit': 'm2',
                'type_path_in_inspect': type_path,
                'type_record': type_record, 'element_record': row,
                **mesh_source,
            },
        })
    return {
        'schema_version': 1, 'software': 'bimcraft', 'software_version': version,
        'model': model,
        'extraction': {
            'import_summary': import_summary,
            'command': commands[0] if commands else [],
            'commands': commands,
            'notes': [
                'Source model opened without save; inspect/elements report quantities from BIMcraft.',
                'BIMcraft volume_m3 and area_m2 are retained without further scaling. Floor volume reporting is rounded to 0.001 m3 in the verified version.',
                'Only explicit homogeneous assignment is resolved; mixed layers remain unresolved.',
                'Lengths from elements and type layers are millimetres; normalized dimensions divide by 1000.',
                'Reported area is category-specific and must not be used blindly as a facade/reference area.',
            ],
        },
        'elements': elements, 'warnings': warnings,
    }


def extract(model_path, cli='bimcraft-cli', timeout=120, page_size=1000, *, mesh_quantities=False):
    path = Path(model_path).expanduser().resolve()
    if not path.is_file():
        raise ValueError('Model file not found: ' + str(path))
    if path.suffix.lower() not in {'.bimc', '.bimcraft', '.ifc'}:
        raise ValueError('Adapter accepts .bimc, .bimcraft or .ifc; other BIMcraft import formats are not verified here')
    if not isinstance(page_size, int) or isinstance(page_size, bool) or not 1 <= page_size <= 1000:
        raise ValueError('page_size must be an integer from 1 to 1000')
    before = _sha256(path)
    version_reply = subprocess.run([cli, '--version'], capture_output=True, text=True, timeout=timeout, check=True)
    version = version_reply.stdout.strip()
    if version != 'bimcraft-cli 0.12.0':
        raise ValueError('BIMcraft adapter quantity/precision contract is verified for bimcraft-cli 0.12.0; run the controls and update the adapter for ' + version)
    command = [cli, 'run', str(path), '--cmd', 'inspect {}', '--cmd', 'elements ' + json.dumps({'limit': page_size, 'offset': 0}, separators=(',', ':'))]
    commands = [command]
    replies = _run(command, timeout)
    import_summary = next((x for x in replies if isinstance(x, dict) and isinstance(x.get('elements'), dict) and 'skipped' in x and 'format' in x), None)
    inspect = next((x for x in replies if isinstance(x, dict) and isinstance(x.get('types'), dict)), None)
    page = next((x for x in replies if isinstance(x, dict) and isinstance(x.get('elements'), list) and 'returned' in x), None)
    if inspect is None or page is None:
        raise ValueError('BIMcraft response lacks inspect types or element page')
    rows = list(page['elements'])
    count = page.get('count')
    if not isinstance(count, int) or count < len(rows):
        raise ValueError('BIMcraft returned an invalid element count')
    while len(rows) < count:
        command = [cli, 'run', str(path), '--cmd', 'elements ' + json.dumps({'limit': page_size, 'offset': len(rows)}, separators=(',', ':'))]
        commands.append(command)
        replies = _run(command, timeout)
        page = next((x for x in replies if isinstance(x, dict) and isinstance(x.get('elements'), list) and 'returned' in x), None)
        if page is None or not page['elements']:
            raise ValueError('BIMcraft pagination stopped before all elements were read')
        if page.get('count') != count:
            raise ValueError('BIMcraft element count changed during pagination')
        rows.extend(page['elements'])
    if len({str(x.get('id')) for x in rows}) != len(rows):
        raise ValueError('BIMcraft pagination returned duplicate element IDs')
    family_replies, family_lookup_errors = {}, {}
    if mesh_quantities:
        family_names = sorted({x['family'] for x in rows if x.get('category') == 'component' and not _finite_nonnegative(x.get('volume_m3')) and isinstance(x.get('family'), str) and x['family']})
        # Read each referenced definition once; inspect.families has metadata only.
        for offset in range(0, len(family_names), 50):
            names = family_names[offset:offset + 50]
            command = [cli, 'run', str(path)]
            for name in names:
                command.extend(['--cmd', 'family ' + json.dumps({'name': name}, separators=(',', ':'))])
            commands.append(command)
            try:
                replies = _run(command, timeout)
            except (ValueError, OSError, subprocess.SubprocessError) as exc:
                family_lookup_errors.update({name: 'BIMcraft family lookup failed: ' + str(exc) for name in names})
                continue
            for reply in replies:
                if isinstance(reply, dict) and reply.get('name') in names and isinstance(reply.get('family'), dict):
                    family_replies[reply['name']] = reply
    after = _sha256(path)
    if before != after:
        raise ValueError('Source model changed during extraction')
    result = normalize(inspect, rows, {'path': str(path), 'sha256': before}, version, commands, import_summary, mesh_quantities=mesh_quantities, family_replies=family_replies, family_lookup_errors=family_lookup_errors)
    if mesh_quantities:
        result['extraction']['mesh_quantities'] = True
        result['extraction']['notes'].append('Opt-in mesh quantities: only supported missing-volume generic components use family mesh integration. ' + MESH_LIMITS)
    if path.suffix.lower() == '.ifc':
        result['warnings'].append({'code': 'ifc_import_context', 'message': 'Quantities and assignments are from BIMcraft\'s imported interpretation; review model/import warnings and retained source IDs before using them.'})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--mesh-quantities', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = extract(args.model, mesh_quantities=args.mesh_quantities)
        data = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.out:
            write_report(result, args.out, [args.model])
        else:
            print(data, end='')
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
