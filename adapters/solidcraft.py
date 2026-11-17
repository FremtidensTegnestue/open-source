#!/usr/bin/env python3
"""Read Solidcraft model quantities without saving or modifying the source model.

Volumes are measured by Solidcraft's geometry engine. Bbox extents are world-axis
aligned, not grain/material directions; total surface is not a reference face area.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from report_io import write_report


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def finite(value, *, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    if nonnegative and value < 0:
        return None
    return float(value)


def normalize_measurement(reply):
    """Normalize actual eval response; unknown quantities stay unknown."""
    if not isinstance(reply, dict) or not isinstance(reply.get('bodies'), list):
        raise ValueError('Unexpected Solidcraft eval response: bodies list absent')
    for feature in reply.get('timeline', []):
        if feature.get('error'):
            raise ValueError(f'Solidcraft model contains failed feature {feature.get("name")}: {feature["error"]}')
    elements, warnings, seen = [], [], set()
    for index, body in enumerate(reply['bodies']):
        name = body.get('name')
        if not isinstance(name, str) or not name:
            raise ValueError('Solidcraft body has no stable name')
        if name in seen:
            raise ValueError('Duplicate Solidcraft body name: ' + name)
        seen.add(name)
        element_id = 'solidcraft:' + name
        material = body.get('material')
        if not isinstance(material, str) or not material.strip() or material.casefold() == 'default':
            material = None
            warnings.append({'code': 'material_unspecified', 'message': 'Body has no explicit material; Solidcraft default density is not used.', 'element_id': element_id})
        volume_mm3 = finite(body.get('volume_mm3'), nonnegative=True) if body.get('closed') is True else None
        if volume_mm3 is None:
            warnings.append({'code': 'volume_unavailable', 'message': 'No measured closed-body volume is available; no bbox-volume approximation is substituted.', 'element_id': element_id})
        area_mm2 = finite(body.get('area_mm2'), nonnegative=True)
        bbox = body.get('bbox')
        dimensions = None
        if isinstance(bbox, dict):
            lower, upper = bbox.get('min'), bbox.get('max')
            if isinstance(lower, list) and isinstance(upper, list) and len(lower) == len(upper) == 3:
                extents = []
                for lo, hi in zip(lower, upper):
                    lo, hi = finite(lo), finite(hi)
                    if lo is None or hi is None or hi < lo:
                        extents = []; break
                    extents.append((hi - lo) / 1000.0)
                if len(extents) == 3:
                    dimensions = dict(zip(['x', 'y', 'z'], extents))
        elements.append({
            'id': element_id,
            'name': name,
            'material_name': material,
            'volume_m3': volume_mm3 / 1_000_000_000.0 if volume_mm3 is not None else None,
            'area_m2': None,
            'surface_area_m2': area_mm2 / 1_000_000.0 if area_mm2 is not None else None,
            'dimensions_m': dimensions,
            'source_ref': {
                'quantity_command': 'solidcraft-cli eval',
                'body_index': index,
                'body_name': name,
                'volume_field': f'/bodies/{index}/volume_mm3',
                'material_field': f'/bodies/{index}/material',
                'volume_unit_conversion': 'mm3 / 1000000000 = m3',
                'surface_area_unit_conversion': 'mm2 / 1000000 = m2',
                'dimensions_basis': 'world-axis-aligned bounding-box extents, not material-local axes',
                'measured_by': body.get('measured_by'),
                'closed': body.get('closed'),
                'raw_measurement': body,
            },
        })
    if not elements:
        warnings.append({'code': 'empty_model', 'message': 'Model contains no measured bodies.'})
    return elements, warnings


def extract(model_path, *, executable='solidcraft-cli', timeout=120):
    model_path = Path(model_path).expanduser().resolve()
    if not model_path.is_file():
        raise ValueError('Solidcraft model not found: ' + str(model_path))
    # .json is also an executable command-script input to Solidcraft. Do not
    # accept it as an inert model in a read-only data adapter.
    if model_path.suffix.casefold() not in ('.sc', '.step', '.stp'):
        raise ValueError('Supported inert model inputs: .sc, .step and .stp; command-script JSON is not accepted')
    original_hash = sha256(model_path)
    command = [executable, 'eval', str(model_path)]
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        version = subprocess.run([executable, '--version'], text=True, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError('Solidcraft inspection could not run: ' + str(error)) from error
    if result.returncode:
        raise ValueError(f'Solidcraft eval failed ({result.returncode}): {(result.stderr or result.stdout).strip()}')
    if version.returncode:
        raise ValueError('Could not identify Solidcraft CLI version')
    if sha256(model_path) != original_hash:
        raise ValueError('Source model changed during Solidcraft inspection')
    try:
        reply = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError('Solidcraft eval did not return valid JSON') from error
    elements, warnings = normalize_measurement(reply)
    return {
        'schema_version': 1,
        'software': 'solidcraft',
        'software_version': version.stdout.strip(),
        'model': {'path': str(model_path), 'sha256': original_hash},
        'extraction': {
            'command': command,
            'source_unchanged': True,
            'raw_reply': reply,
            'stderr': result.stderr,
            'notes': [
                'Closed-body volumes are returned by the actual geometry engine.',
                'area_m2 is unknown: Solidcraft total surface area is exposed separately as surface_area_m2.',
                'Model-assigned densities/masses remain provenance only; this adapter does not select database density.',
                'STEP imports without explicit material remain material-unspecified.',
            ],
        },
        'elements': elements,
        'warnings': warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    try:
        normalized = extract(args.model)
        text = json.dumps(normalized, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.out:
            write_report(normalized, args.out, [args.model])
        else:
            print(text, end='')
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
