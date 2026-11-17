#!/usr/bin/env python3
"""Fetch preserved source originals by their recorded URL and SHA-256.

The full structured dataset already ships as Parquet. This optional operation
downloads the separate original documents for source-level checking.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import materials

DEMO_SOURCES = {
    'br18:source:table-7-2025.xlsx', 'wood:chapter-13',
    'environmental:oekobaudat:3428753d-b270-4b13-bbe0-244b981db333@00.04.000',
}


def fetch(source, root=ROOT):
    destination = materials.original_path(root, source['local_path'])
    if destination.is_file():
        if materials.digest(destination) != source['sha256']:
            raise ValueError('Existing original has a different checksum: ' + source['local_path'])
        return {'source': source['id'], 'status': 'current'}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        request = urllib.request.Request(source['url'], headers={'User-Agent': 'FremtidensTegnestue-SourceArchive/1'})
        digest = hashlib.sha256()
        with urllib.request.urlopen(request, timeout=90) as response, tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.source-', delete=False) as stream:
            temporary = Path(stream.name)
            for block in iter(lambda: response.read(1024 * 1024), b''):
                stream.write(block); digest.update(block)
        if digest.hexdigest() != source['sha256']:
            raise ValueError('Publisher response differs from preserved source: ' + source['id'])
        os.link(temporary, destination)
        return {'source': source['id'], 'status': 'downloaded'}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--demo', action='store_true', help='Originals used by the included examples')
    group.add_argument('--all', action='store_true', help='All registered source originals; many requests and potentially stale publisher URLs')
    parser.add_argument('--db', type=Path, default=ROOT/'data/materials.sqlite')
    parser.add_argument('--root', type=Path, default=ROOT, help='Destination root for recorded relative paths')
    args = parser.parse_args()
    try:
        with materials.connect(args.db) as db:
            sources = [dict(r) for r in db.execute('SELECT id,url,local_path,sha256 FROM sources')]
        selected = [s for s in sources if args.all or s['id'] in DEMO_SOURCES]
        selected = list({(s['local_path'], s['sha256']): s for s in selected}.values())
        if args.demo and {s['id'] for s in selected} != DEMO_SOURCES:
            raise ValueError('Database lacks one or more required example sources')
        failures, successes = [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            pending = {pool.submit(fetch, s, args.root): s for s in selected}
            for future in concurrent.futures.as_completed(pending):
                try:
                    successes.append(future.result())
                except Exception as exc:
                    failures.append({'source': pending[future]['id'], 'error': str(exc)})
        print(json.dumps({'checked_or_downloaded': len(successes), 'failures': failures,
                          'note': 'No changed publisher file is accepted under an old source hash.'}, ensure_ascii=False, indent=2))
        return 1 if failures else 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
