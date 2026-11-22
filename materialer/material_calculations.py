"""Traceable calculations and explicit model/database bindings; no inferred product equivalence."""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import materials
from material_units import normalize

GWP_PROPERTIES = {'global_warming_potential', 'gwp', 'gwp_total', 'gwp_fossil', 'gwp_biogenic', 'gwp_luluc'}
GWP_UNITS = {'kg CO2-eq': 1.0, 'kg CO2-Equiv.': 1.0, 'kg CO2 eq.': 1.0, 'kg CO2e': 1.0,
             'kgCO2e': 1.0, 'kg CO2-Äqv.': 1.0, 'kg CO2-eq.': 1.0, 'kg CO_(2) eq': 1.0, 'kg CO_(2) eqv.': 1.0, 'kg CO_(2)-Äq.': 1.0, 'g CO2-eq': 0.001, 't CO2-eq': 1000.0}

class CalculationError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def positive(value, label, zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (value < 0 if zero else value <= 0):
        raise CalculationError('invalid_quantity', f'{label} must be a finite {"nonnegative" if zero else "positive"} number')
    return float(value)


def observation(db, observation_id, material_id):
    rows = materials.rows(db, 'SELECT * FROM observations WHERE id=?', [observation_id])
    if not rows:
        raise CalculationError('observation_missing', f'Observation not found: {observation_id}')
    obj = rows[0]
    if obj['material_id'] != material_id:
        raise CalculationError('material_mismatch', 'Selected observation belongs to another material record')
    if obj['value'] is None or not math.isfinite(obj['value']):
        raise CalculationError('value_not_declared', 'Selected source has no finite numerical value')
    source = materials.rows(db, 'SELECT * FROM sources WHERE id=?', [obj['source_id']])[0]
    obj['citation'] = {k: source[k] for k in ('id', 'title', 'publisher', 'url', 'retrieved_at', 'local_path', 'sha256', 'license', 'license_status')}
    obj['citation']['source_locator'] = obj['source_locator']
    # The complete original observation already lives in the database. Keep the
    # report readable while retaining all scientific context and source identity.
    obj.pop('metadata', None)
    return obj


def finish(value, unit, method, inputs, **extra):
    if not math.isfinite(value):
        raise CalculationError('numeric_overflow', 'Calculation exceeds the finite numeric range')
    return dict(status='ok', value=value, unit=unit, method=method, inputs=inputs, **extra)


def mass(db, request):
    obj = observation(db, request['density_observation_id'], request['material_id'])
    if obj['property'] != 'density':
        raise CalculationError('property_mismatch', 'Mass from volume requires density, not an area mass factor')
    density = normalize(obj['value'], obj['unit'], 'density')
    positive(density['value'], 'density')
    quantity = request['quantity']
    volume = normalize(quantity['value'], quantity['unit'], 'volume')
    positive(volume['value'], 'volume', zero=True)
    return finish(volume['value'] * density['value'], 'kg',
                  {'id': 'mass.volume_density.v1', 'formula': 'mass_kg = volume_m3 * density_kg_m3'},
                  {'volume': volume, 'density': obj, 'density_normalized': density})


def reference_basis(obj):
    text = obj.get('declared_unit')
    if not isinstance(text, str):
        raise CalculationError('reference_basis_missing', 'Source has no declared reference amount/unit')
    context = obj.get('conditions', {})
    if not isinstance(context, dict):
        raise CalculationError('unsupported_reference_basis', 'Reference context must be an object')
    match = re.fullmatch(r'\s*([+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s+([^\s]+)\s*', text)
    if match:
        amount, unit = positive(float(match[1]), 'declared reference amount'), match[2]
        origin = 'explicit amount and unit in source declared_unit'
    else:
        # ILCD records can store unit and amount in separate source fields. Never
        # infer amount1 from the unit or use reference exchange meanAmount1.
        unit = text.strip()
        amount = context.get('declared_amount')
        refs = context.get('declared_references', [])
        matching = [ref for ref in refs if isinstance(ref, dict) and ref.get('unit') == unit]
        if not matching or any(ref.get('amount') != amount for ref in matching):
            raise CalculationError('unsupported_reference_basis', f'Declared basis needs additional context or is unsupported: {text}')
        amount = positive(amount, 'source declared amount')
        origin = 'explicit declared_amount checked against original declared_references'
    aliases = {'qm': 'm2', 'sqm': 'm2', 'cbm': 'm3'}
    normalized_unit = aliases.get(unit, unit)
    for dimension in ('mass', 'volume', 'area'):
        try:
            result = normalize(amount, normalized_unit, dimension)
        except ValueError:
            continue
        positive(result['value'], 'normalized declared reference amount')
        break
    else:
        raise CalculationError('unsupported_reference_basis', f'Unsupported declared unit: {unit}')

    def confirm(value, source_unit):
        if not isinstance(source_unit, str):
            raise CalculationError('unsupported_reference_basis', 'Source reference needs an explicit unit')
        source_unit = source_unit.strip()
        reference = normalize(positive(value, 'source reference amount'),
                              aliases.get(source_unit, source_unit), dimension)
        if not math.isclose(reference['value'], result['value'], rel_tol=1e-12, abs_tol=0):
            raise CalculationError('reference_basis_conflict', 'Source reference amounts or units conflict')

    if context.get('reference_amount') is not None or context.get('reference_unit') is not None:
        confirm(context.get('reference_amount'), context.get('reference_unit'))
    refs = context.get('declared_references', [])
    if not isinstance(refs, list):
        raise CalculationError('unsupported_reference_basis', 'Declared references must be a list')
    for ref in refs:
        if not isinstance(ref, dict):
            raise CalculationError('unsupported_reference_basis', 'Declared reference must be an object')
        confirm(ref.get('amount'), ref.get('unit'))
    if context.get('declared_amount') is not None:
        source_amount = positive(context['declared_amount'], 'source declared amount')
        if context.get('declared_unit') is not None:
            confirm(source_amount, context['declared_unit'])
        elif refs:
            if not any(ref.get('amount') == source_amount for ref in refs):
                raise CalculationError('reference_basis_conflict', 'Declared amount disagrees with source references')
        else:
            confirm(source_amount, unit)
    result.update(source_unit=unit, basis_source=origin)
    return dimension, result


def climate(db, request):
    obj = observation(db, request['gwp_observation_id'], request['material_id'])
    if obj['property'] not in GWP_PROPERTIES or obj['unit'] not in GWP_UNITS:
        raise CalculationError('indicator_mismatch', 'Expected a supported global-warming indicator and explicit CO2-equivalent unit')
    if not isinstance(obj.get('module'), str) or not obj['module'].strip():
        raise CalculationError('module_missing', 'A lifecycle module must be specified by the source')
    if obj['conditions'].get('record_scope') == 'installation_area_reference_factor':
        raise CalculationError('unsupported_reference_basis', 'Installation factors require the building-area/year method, not material scaling')
    dimension, declared = reference_basis(obj)
    quantity = request['quantity']
    actual = normalize(quantity['value'], quantity['unit'], dimension)
    positive(quantity['value'], 'quantity', zero=True)
    positive(actual['value'], 'quantity', zero=True)
    factor = actual['value'] / declared['value']
    value = obj['value'] * GWP_UNITS[obj['unit']] * factor
    if value == 0 and obj['value'] != 0 and quantity['value'] != 0:
        raise CalculationError('numeric_underflow', 'Nonzero climate contribution is outside the supported numeric range')
    return finish(value, 'kg CO2-eq',
                  {'id': 'climate.declared_reference_scaling.v1', 'formula': 'contribution = source_value * numerator_conversion * quantity_in_source_basis / declared_amount'},
                  {'quantity': actual, 'source_observation': obj, 'declared_basis': declared, 'scaling_factor': factor, 'numerator_conversion_factor': GWP_UNITS[obj['unit']]},
                  module=obj['module'], indicator=obj['property'], indicator_method=obj['method'],
                  scope='Single source indicator/module only; no lifecycle sum, building-LCA or compliance conclusion')


def moisture(db, request):
    direction = request.get('direction')
    if direction not in ('radial', 'tangential'):
        raise CalculationError('direction_required', 'Wood direction must be explicitly radial or tangential')
    obj = observation(db, request['coefficient_observation_id'], request['material_id'])
    if obj['property'] != 'moisture_dimensional_change_coefficient_' + direction:
        raise CalculationError('property_mismatch', 'Use the matching dimensional-change coefficient, not total green-to-dry shrinkage')
    coefficient = normalize(obj['value'], obj['unit'], 'moisture_coefficient')
    positive(coefficient['value'], 'moisture coefficient')
    dimension = normalize(request['dimension']['value'], request['dimension']['unit'], 'length')
    positive(dimension['value'], 'starting dimension')
    start = positive(request['initial_moisture_percent'], 'initial moisture', zero=True)
    end = positive(request['final_moisture_percent'], 'final moisture', zero=True)
    conditions = obj['conditions']
    low, high = conditions.get('valid_moisture_content_percent_min'), conditions.get('valid_moisture_content_percent_max')
    if low is None or high is None:
        raise CalculationError('validity_range_missing', 'Source coefficient has no supported moisture validity range')
    if not low <= start <= high or not low <= end <= high:
        raise CalculationError('outside_validity_range', f'Both moisture states must be within source range {low}–{high}%')
    change = dimension['value'] * coefficient['value'] * (end - start)
    return finish(change, 'm',
                  {'id': 'wood.usda_2021_eq13_3.v1', 'formula': 'delta_dimension = initial_dimension * coefficient_per_percentage_point * (final_MC_percent - initial_MC_percent)',
                   'source': 'USDA Wood Handbook 2021 chapter13, printed page13–16, equation13–3; table13–5', 'source_file': 'data/raw/wood/chapter_13.pdf'},
                  {'dimension': dimension, 'coefficient': obj, 'coefficient_normalized': coefficient, 'initial_moisture_percent': start, 'final_moisture_percent': end},
                  final_dimension_m=dimension['value'] + change,
                  assumptions=['Approximate source method within its moisture range; percent means percentage points of water mass per oven-dry wood mass',
                               'Explicit radial/tangential direction; geometry alone does not determine grain orientation'])


def calculate(db, request):
    if not isinstance(request, dict):
        raise CalculationError('invalid_request', 'Calculation request must be an object')
    functions = {'mass': mass, 'climate': climate, 'moisture': moisture}
    if request.get('kind') not in functions:
        raise CalculationError('unsupported_calculation', 'Choose mass, climate or moisture')
    try:
        return functions[request['kind']](db, request)
    except (KeyError, TypeError) as exc:
        raise CalculationError('missing_input', f'Missing or invalid calculation input: {exc}') from exc


def extract(path, software, *, mesh_quantities=False):
    if mesh_quantities and software != 'bimcraft':
        raise CalculationError('unsupported_mesh_quantities', '--mesh-quantities is supported only for BIMcraft')
    if software == 'solidcraft':
        from adapters.solidcraft import extract as adapter
    elif software == 'bimcraft':
        from adapters.bimcraft import extract as adapter
    else:
        raise CalculationError('unsupported_model', 'Choose solidcraft or bimcraft')
    try:
        result = adapter(path, mesh_quantities=True) if mesh_quantities else adapter(path)
    except subprocess.SubprocessError as exc:
        raise CalculationError("model_inspection_failed", str(exc)) from exc
    if result.get('software') != software or result.get('schema_version') != 1:
        raise CalculationError('invalid_extraction', 'Adapter returned an unsupported quantity contract')
    return result


def suggestions(db, model):
    records = materials.rows(db, 'SELECT id,name,category,kind,search_text FROM materials')
    result = []
    for element in model['elements']:
        name = element.get('material_name')
        candidates = []
        if name:
            exact = [m for m in records if materials.fold(m['name']) == materials.fold(name)]
            if exact:
                candidates = [dict(material_id=m['id'], name=m['name'], category=m['category'], match_kind='exact_label') for m in exact[:10]]
            else:
                terms = materials.fold(name).split()
                for item in records:
                    hits = sum(term in materials.fold(item['name']) for term in terms)
                    if hits:
                        candidates.append(dict(material_id=item['id'], name=item['name'], category=item['category'], match_kind='text_overlap', matched_terms=hits))
                candidates.sort(key=lambda x: (-x['matched_terms'], x['material_id']))
                candidates = candidates[:10]
        result.append(dict(element_id=element['id'], model_material_name=name, candidates=candidates,
                           status='review_required' if candidates else 'unresolved', selection_policy='Suggestions only; explicit observation and material bindings required for assessment'))
    return dict(model=model['model'], elements=result)


def database_fingerprint(db):
    row = db.execute("SELECT value FROM build_info WHERE key='input_sha256'").fetchone()
    return hashlib.sha256(row[0].encode()).hexdigest() if row else None


def unavailable(exc):
    return dict(status='unavailable', error={'code': getattr(exc, 'code', 'invalid_input'), 'message': str(exc)})


def assess(db, model, bindings):
    if bindings.get('schema_version') != 1 or not isinstance(bindings.get('elements'), dict):
        raise CalculationError('invalid_bindings', 'Bindings require schema_version1 and an elements object')
    if bindings.get('model_sha256') != model['model']['sha256']:
        raise CalculationError('model_changed', 'Bindings must explicitly match this source model SHA-256')
    reports = []
    for element in model['elements']:
        report = dict(element_id=element['id'], element_name=element['name'], model_material_name=element.get('material_name'),
                      model_quantity_source=element.get('source_ref'), calculations={}, diagnostics=[])
        binding = bindings['elements'].get(element['id'])
        if not binding:
            report.update(status='unresolved', diagnostics=[{'code': 'binding_missing', 'message': 'No explicit material/observation binding for this model element'}])
            reports.append(report); continue
        if not element.get('material_name') or binding.get('model_material_name') != element['material_name']:
            report.update(status='unresolved', diagnostics=[{'code': 'material_label_changed', 'message': 'Missing or changed model material label; no calculation performed'}])
            reports.append(report); continue
        if not binding.get('selection_note'):
            report.update(status='unresolved', diagnostics=[{'code': 'selection_note_missing', 'message': 'Explain the material/dataset selection and assumptions'}])
            reports.append(report); continue
        material_id = binding.get('material_id')
        rows = materials.rows(db, 'SELECT id,name,kind,category FROM materials WHERE id=?', [material_id])
        if not rows:
            report.update(status='unresolved', diagnostics=[{'code': 'material_missing', 'message': 'Bound database material does not exist'}])
            reports.append(report); continue
        report['binding'] = dict(material=rows[0], selection_note=binding['selection_note'], selection_mode='explicit_reference_scenario')
        operations = binding.get('operations', ['mass', 'climate'])
        if not isinstance(operations, list) or not operations or any(not isinstance(x, str) for x in operations):
            raise CalculationError('invalid_operations', 'Operations must be a nonempty list of calculation names')
        volume = element.get('volume_m3')
        increment = (element.get('source_ref') or {}).get('volume_rounding_increment_m3', 0)
        mass_result = None
        if 'mass' in operations or 'climate' in operations:
            try:
                positive(volume, 'model volume')
                if increment:
                    positive(increment, 'quantity rounding increment')
                mass_result = mass(db, dict(material_id=material_id, density_observation_id=binding['density_observation_id'], quantity={'value': volume, 'unit': 'm3'}))
                if increment:
                    uncertainty = increment / 2 * mass_result['inputs']['density_normalized']['value']
                    mass_result['model_quantity_rounding_bound_kg'] = uncertainty
                if 'mass' in operations:
                    report['calculations']['mass'] = mass_result
            except (ValueError, KeyError, TypeError) as exc:
                if 'mass' in operations:
                    report['calculations']['mass'] = unavailable(exc)
        if 'climate' in operations:
            report['calculations']['climate'] = []
            ids = binding.get('gwp_observation_ids', [])
            if not ids:
                report['diagnostics'].append({'code': 'gwp_binding_missing', 'message': 'No explicit climate observation selected'})
            for oid in ids:
                try:
                    obj = observation(db, oid, material_id)
                    basis_dimension, declared = reference_basis(obj)
                    if basis_dimension == 'area' and not binding.get('area_basis_note'):
                        raise CalculationError('area_semantics_unconfirmed', 'Explicitly confirm the reported model area matches the source reference area')
                    quantity = {'volume': {'value': volume, 'unit': 'm3'}, 'area': {'value': element.get('area_m2'), 'unit': 'm2'}}.get(basis_dimension)
                    if basis_dimension == 'mass':
                        if mass_result is None:
                            raise CalculationError('mass_missing', 'Mass-based climate factor needs a resolved source density/mass calculation')
                        quantity = {'value': mass_result['value'], 'unit': 'kg'}
                    positive(quantity['value'], 'model reference quantity')
                    result = climate(db, dict(material_id=material_id, gwp_observation_id=oid, quantity=quantity))
                    if basis_dimension == 'area':
                        result['area_basis_note'] = binding['area_basis_note']
                    if increment and basis_dimension in ('mass', 'volume'):
                        scale = increment / 2 if basis_dimension == 'volume' else mass_result['model_quantity_rounding_bound_kg']
                        result['model_quantity_rounding_bound_kg_co2_eq'] = abs(obj['value'] * GWP_UNITS[obj['unit']] / declared['value'] * scale)
                    report['calculations']['climate'].append(result)
                except (ValueError, KeyError, TypeError) as exc:
                    report['calculations']['climate'].append(dict(observation_id=oid, **unavailable(exc)))
        if 'moisture' in operations:
            try:
                config = binding['moisture']
                if not config.get('orientation_note'):
                    raise CalculationError('orientation_missing', 'Explicit source-axis to radial/tangential direction assumption is required')
                axis = config['dimension_axis']
                if axis not in ('x', 'y', 'z'):
                    raise CalculationError('dimension_axis_missing', 'Choose an explicit model bounding-box axis')
                dimension = (element.get('dimensions_m') or {}).get(axis)
                request = dict(config, kind='moisture', material_id=material_id, dimension={'value': dimension, 'unit': 'm'})
                report['calculations']['moisture'] = calculate(db, request)
                report['calculations']['moisture']['orientation_note'] = config['orientation_note']
            except (ValueError, KeyError, TypeError) as exc:
                report['calculations']['moisture'] = unavailable(exc)
        if any(op not in ('mass', 'climate', 'moisture') for op in operations):
            report['diagnostics'].append({'code': 'unsupported_operation', 'message': 'Unknown calculation operation requested'})
        all_results = []
        for value in report['calculations'].values():
            all_results.extend(value if isinstance(value, list) else [value])
        report['status'] = 'ok' if all_results and all(x['status'] == 'ok' for x in all_results) and not report['diagnostics'] else 'partial'
        reports.append(report)
    missing_ids = sorted(set(bindings['elements']) - {e['id'] for e in model['elements']})
    warnings = list(model.get('warnings', []))
    if missing_ids:
        warnings.append({'code': 'bound_element_missing', 'message': 'Bound IDs absent from extraction', 'element_ids': missing_ids})
    return dict(schema_version=1, status='ok' if reports and all(x['status'] == 'ok' for x in reports) and not missing_ids and all(w.get('severity') == 'notice' for w in warnings) else 'partial',
                model=model['model'], software=model['software'], software_version=model['software_version'], extraction=model['extraction'],
                database_input_fingerprint=database_fingerprint(db), elements=reports, warnings=warnings,
                scope='Selected homogeneous reference scenarios; source context and product equivalence require review; no regulatory or complete building-LCA conclusion')
