#!/usr/bin/env python3
"""Local material data: build, search and inspect a provenance-preserving SQLite snapshot."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / 'data/materials.sqlite'
SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE datasets(id TEXT PRIMARY KEY, summary_json TEXT NOT NULL);
CREATE TABLE sources(
 id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES datasets(id),
 title TEXT NOT NULL, publisher TEXT, url TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 local_path TEXT NOT NULL, sha256 TEXT NOT NULL, media_type TEXT,
 license TEXT NOT NULL, license_status TEXT NOT NULL, metadata_json TEXT NOT NULL
);
CREATE TABLE materials(
 id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES datasets(id),
 name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('generic','product','assembly')),
 category TEXT NOT NULL, aliases_json TEXT NOT NULL, description TEXT,
 source_id TEXT NOT NULL REFERENCES sources(id), source_locator TEXT NOT NULL,
 search_text TEXT NOT NULL, metadata_json TEXT NOT NULL
);
CREATE TABLE observations(
 id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES datasets(id),
 material_id TEXT NOT NULL REFERENCES materials(id), property TEXT NOT NULL,
 value REAL, value_text TEXT NOT NULL, unit TEXT, module TEXT,
 declared_unit TEXT, basis TEXT, method TEXT, data_status TEXT NOT NULL,
 conditions_json TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES sources(id),
 source_locator TEXT NOT NULL, metadata_json TEXT NOT NULL,
 CHECK(value IS NOT NULL OR length(value_text)>0)
);
CREATE TABLE build_info(key TEXT PRIMARY KEY, value TEXT NOT NULL);
'''


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold().replace('æ', 'ae').replace('ø', 'o')) if not unicodedata.combining(c))


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def objects(path):
    if not path.is_file():
        raise ValueError(f'Missing dataset file: {path}')
    with path.open(encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    obj = json.loads(line, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
                    if not isinstance(obj, dict):
                        raise ValueError('Expected object')
                    yield obj
                except (ValueError, TypeError) as exc:
                    raise ValueError(f'{path}:{line_number}: {exc}') from exc


def required(obj, *fields):
    for field in fields:
        if not isinstance(obj.get(field), str) or not obj[field].strip():
            raise ValueError(f'{obj.get("id", "record")}: missing/nontext {field}')


def original_path(root, relative):
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f'Original path escapes repository: {relative}')
    return result


def build(root=ROOT, destination=DEFAULT_DB):
    """Stream complete datasets into a new DB; replace the last good DB only on success."""
    root, destination = Path(root), Path(destination)
    staging = root / 'data/staging'
    datasets = sorted(p for p in staging.iterdir() if p.is_dir() and (p / 'sources.jsonl').exists())
    if not datasets:
        raise ValueError('No collected datasets in data/staging')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + '.building')
    if temporary.exists():
        temporary.unlink()
    db = sqlite3.connect(temporary)
    counts = {}
    source_ids = set()
    material_ids = set()
    try:
        db.executescript(SCHEMA)
        with db:
            for folder in datasets:
                dataset_id = folder.name
                summary = json.loads((folder / 'summary.json').read_text()) if (folder / 'summary.json').exists() else {}
                db.execute('INSERT INTO datasets VALUES (?,?)', (dataset_id, encode(summary)))
                for obj in objects(folder / 'sources.jsonl'):
                    required(obj, 'id', 'title', 'url', 'retrieved_at', 'local_path', 'sha256', 'license', 'license_status')
                    path = original_path(root, obj['local_path'])
                    if not path.is_file() or digest(path) != obj['sha256']:
                        raise ValueError(f'Original missing or checksum mismatch: {obj["local_path"]}')
                    db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
                        obj['id'], dataset_id, obj['title'], obj.get('publisher'), obj['url'], obj['retrieved_at'],
                        obj['local_path'], obj['sha256'], obj.get('media_type'), obj['license'], obj['license_status'], encode(obj)))
                    source_ids.add(obj['id'])
            for folder in datasets:
                for obj in objects(folder / 'materials.jsonl'):
                    required(obj, 'id', 'name', 'kind', 'category', 'source_id', 'source_locator')
                    if obj['source_id'] not in source_ids:
                        raise ValueError(f'Material source absent: {obj["id"]}')
                    aliases = obj.get('aliases', [])
                    if not isinstance(aliases, list) or any(not isinstance(a, str) for a in aliases):
                        raise ValueError(f'Invalid aliases: {obj["id"]}')
                    db.execute('INSERT INTO materials VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
                        obj['id'], folder.name, obj['name'], obj['kind'], obj['category'], encode(aliases), obj.get('description'),
                        obj['source_id'], obj['source_locator'], fold(' '.join([obj['name'], *aliases, obj['category']])), encode(obj)))
                    material_ids.add(obj['id'])
                count = 0
                for obj in objects(folder / 'observations.jsonl'):
                    required(obj, 'id', 'material_id', 'property', 'source_id', 'source_locator')
                    if obj['material_id'] not in material_ids or obj['source_id'] not in source_ids:
                        raise ValueError(f'Observation has unknown material/source: {obj["id"]}')
                    value = obj.get('value')
                    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                        raise ValueError(f'Observation value must be a finite number or null: {obj["id"]}')
                    value_text = obj.get('value_text')
                    if not isinstance(value_text, str) or (value is None and not value_text.strip()):
                        raise ValueError(f'Missing original value: {obj["id"]}')
                    conditions = obj.get('conditions', {})
                    if not isinstance(conditions, dict):
                        raise ValueError(f'Conditions must be an object: {obj["id"]}')
                    db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                        obj['id'], folder.name, obj['material_id'], obj['property'], value, value_text, obj.get('unit'),
                        obj.get('module'), obj.get('declared_unit'), obj.get('basis'), obj.get('method'), obj.get('data_status', 'reported'),
                        encode(conditions), obj['source_id'], obj['source_locator'], encode(obj)))
                    count += 1
                counts[folder.name] = count
            # Indices are built after the stream to keep multi-million-row imports efficient.
            db.executescript('''
                CREATE INDEX observations_material ON observations(material_id);
                CREATE INDEX observations_property ON observations(property, module);
                CREATE INDEX observations_source ON observations(source_id);
                CREATE INDEX materials_category ON materials(category);
                CREATE INDEX sources_dataset ON sources(dataset_id);
            ''')
            manifests = {str(p.relative_to(root)): digest(p) for folder in datasets for p in sorted(folder.glob('*.jsonl'))}
            db.execute('INSERT INTO build_info VALUES (?,?)', ('schema_version', '1'))
            db.execute('INSERT INTO build_info VALUES (?,?)', ('input_sha256', encode(manifests)))
            failures = db.execute('PRAGMA foreign_key_check').fetchall()
            if failures:
                raise ValueError(f'Foreign key errors: {failures[:5]}')
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity check failed')
        db.close()
        os.replace(temporary, destination)
    except BaseException:
        db.close()
        temporary.unlink(missing_ok=True)
        raise
    return {'database': str(destination), 'observations_by_dataset': counts, 'materials': len(material_ids), 'sources': len(source_ids)}


def connect(path):
    if not Path(path).is_file():
        raise ValueError(f'Database absent: {path}. Run python scripts/build_database.py to restore the included Parquet data, or python scripts/download_data.py for the full release download.')
    connection = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def rows(db, sql, params=()):
    result = []
    for row in db.execute(sql, params):
        obj = dict(row)
        for key in list(obj):
            if key.endswith('_json'):
                obj[key[:-5]] = json.loads(obj.pop(key))
        obj.pop('search_text', None)
        result.append(obj)
    return result


def stats(db):
    return {
        'counts': {t: db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['datasets', 'sources', 'materials', 'observations']},
        'numeric_observations': db.execute('SELECT count(*) FROM observations WHERE value IS NOT NULL').fetchone()[0],
        'datasets': rows(db, 'SELECT dataset_id,count(*) AS observations,count(DISTINCT material_id) AS materials FROM observations GROUP BY dataset_id'),
        'categories': rows(db, 'SELECT category,count(*) AS records FROM materials GROUP BY category ORDER BY records DESC'),
        'properties': rows(db, 'SELECT property,count(*) AS observations FROM observations GROUP BY property ORDER BY observations DESC'),
        'rights': rows(db, 'SELECT license_status,count(*) AS sources FROM sources GROUP BY license_status'),
    }


def verify(db, root, *, database_only=False):
    errors = []
    checked = set()
    for source in (() if database_only else db.execute('SELECT id,local_path,sha256 FROM sources')):
        key = source['local_path'], source['sha256']
        if key in checked:
            continue
        checked.add(key)
        path = original_path(root, source['local_path'])
        if not path.is_file() or digest(path) != source['sha256']:
            errors.append({'source': source['id'], 'path': source['local_path'], 'error': 'missing or changed original'})
    integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
    foreign_keys = [list(x) for x in db.execute('PRAGMA foreign_key_check')]
    return {'ok': not errors and not foreign_keys and integrity == 'ok', 'scope': 'database_only' if database_only else 'database_and_original_sources', 'original_files_checked': len(checked), 'original_sources_verified': not database_only and not errors, 'integrity': integrity, 'foreign_key_errors': foreign_keys, 'source_errors': errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('build', help='Rebuild SQLite from all staged originals and JSONL')
    commands.add_parser('stats')
    verification = commands.add_parser('verify')
    verification.add_argument('--database-only', action='store_true', help='Check SQLite integrity and references without requiring separately downloaded source originals')
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--category')
    search.add_argument('--limit', type=int, default=20)
    show = commands.add_parser('show')
    show.add_argument('id')
    observations = commands.add_parser('observations')
    observations.add_argument('--material')
    observations.add_argument('--property')
    observations.add_argument('--module')
    observations.add_argument('--dataset')
    observations.add_argument('--limit', type=int, default=50)
    observations.add_argument('--offset', type=int, default=0)
    sources = commands.add_parser('sources')
    sources.add_argument('--id')
    units = commands.add_parser('normalize', help='Convert one explicitly typed value to SI')
    units.add_argument('--value', type=float, required=True)
    units.add_argument('--unit', required=True)
    units.add_argument('--dimension', required=True)
    calculation = commands.add_parser('calculate', help='Calculate a source-bound mass, climate or wood-moisture request')
    calculation.add_argument('request', type=Path)
    calculation.add_argument('--out', type=Path)
    for name in ('extract', 'suggest', 'assess'):
        model = commands.add_parser(name)
        model.add_argument('model', type=Path)
        model.add_argument('--software', choices=('solidcraft', 'bimcraft'), required=True)
        model.add_argument('--out', type=Path)
        model.add_argument('--mesh-quantities', action='store_true', help='BIMcraft only: calculate volume from supported closed generic family meshes')
        if name == 'assess':
            model.add_argument('--bindings', type=Path, required=True)
    args = parser.parse_args(argv)
    if getattr(args, 'limit', 1) < 1 or getattr(args, 'offset', 0) < 0:
        parser.error('limit must be positive and offset nonnegative')
    try:
        if args.command == 'build':
            result = build(destination=args.db)
        elif args.command == 'normalize':
            from material_units import normalize
            result = normalize(args.value, args.unit, args.dimension)
        elif args.command in ('extract', 'suggest', 'assess'):
            import material_calculations as calculations
            model = calculations.extract(args.model, args.software, mesh_quantities=args.mesh_quantities)
            if args.command == 'extract':
                result = model
            else:
                with connect(args.db) as db:
                    result = calculations.suggestions(db, model) if args.command == 'suggest' else calculations.assess(db, model, json.loads(args.bindings.read_text()))
        elif args.command == 'calculate':
            from material_calculations import calculate
            with connect(args.db) as db:
                result = calculate(db, json.loads(args.request.read_text()))
        else:
            with connect(args.db) as db:
                if args.command == 'stats':
                    result = stats(db)
                elif args.command == 'verify':
                    result = verify(db, ROOT, database_only=args.database_only)
                elif args.command == 'search':
                    terms = fold(args.query).split()
                    clause = ['search_text LIKE ?' for _ in terms]
                    params = ['%' + x + '%' for x in terms]
                    if args.category:
                        clause.append('category=?'); params.append(args.category)
                    result = rows(db, 'SELECT * FROM materials WHERE ' + (' AND '.join(clause) or '1') + ' ORDER BY id LIMIT ?', [*params, args.limit])
                elif args.command == 'show':
                    matches = rows(db, 'SELECT * FROM materials WHERE id=?', [args.id])
                    if not matches:
                        raise ValueError('Material not found: ' + args.id)
                    result = matches[0]
                    result['properties'] = rows(db, 'SELECT property,unit,module,count(*) AS observations FROM observations WHERE material_id=? GROUP BY property,unit,module', [args.id])
                elif args.command == 'sources':
                    result = rows(db, 'SELECT * FROM sources' + (' WHERE id=?' if args.id else '') + ' ORDER BY id', [args.id] if args.id else [])
                else:
                    clause, params = [], []
                    for option, column in [('material', 'material_id'), ('property', 'property'), ('module', 'module'), ('dataset', 'dataset_id')]:
                        value = getattr(args, option)
                        if value:
                            clause.append(column + '=?'); params.append(value)
                    result = rows(db, 'SELECT * FROM observations WHERE ' + (' AND '.join(clause) or '1') + ' ORDER BY rowid LIMIT ? OFFSET ?', [*params, args.limit, args.offset])
        output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if getattr(args, 'out', None):
            from report_io import write_report
            write_report(result, args.out, [args.db, getattr(args, 'model', None), getattr(args, 'request', None), getattr(args, 'bindings', None)])
            print(json.dumps({'path': str(args.out), 'status': result.get('status', 'ok')}, ensure_ascii=False))
        else:
            print(output)
        if isinstance(result, dict) and result.get('ok') is False:
            return 1
        if isinstance(result, dict) and result.get('status') in ('partial', 'unresolved'):
            return 2
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({'error': str(exc), 'code': getattr(exc, 'code', 'invalid_input')}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
