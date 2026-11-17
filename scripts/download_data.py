#!/usr/bin/env python3
"""Install the full versioned SQLite release after checking its size, SHA-256 and integrity.

Network access occurs only when main()/download() is called. Decompression requires
the optional zstandard package; reading the manifest and checking an existing copy
use Python's standard library.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'data/releases/2026-11-17.json'
DEFAULT_DESTINATION = ROOT / 'data/materials.sqlite'
CHUNK_BYTES = 1024 * 1024


class DownloadError(ValueError):
    pass


def load_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding='utf-8'))
    if (not isinstance(manifest, dict) or type(manifest.get('schema_version')) is not int
            or manifest['schema_version'] != 1):
        raise DownloadError('Expected a release manifest with schema_version 1')
    assets = manifest.get('assets')
    asset = assets.get('sqlite') if isinstance(assets, dict) else None
    if not isinstance(asset, dict) or asset.get('compression') != 'zstd':
        raise DownloadError('Manifest must contain assets.sqlite with compression zstd')
    if not isinstance(asset.get('url'), str) or not asset['url'].startswith(('https://', 'file://')):
        raise DownloadError('SQLite asset URL must use https:// (or file:// for local copies)')
    for prefix in ('compressed', 'uncompressed'):
        size = asset.get(prefix + '_bytes')
        digest = asset.get(prefix + '_sha256')
        if type(size) is not int or size <= 0:
            raise DownloadError(f'Manifest {prefix}_bytes must be a positive integer')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise DownloadError(f'Manifest {prefix}_sha256 must be a lowercase SHA-256')
    return manifest, asset


def file_matches(path, size, expected_sha256):
    if not path.is_file() or path.stat().st_size != size:
        return False
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK_BYTES), b''):
            digest.update(block)
    return digest.hexdigest() == expected_sha256


def check_sqlite(path):
    connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise DownloadError('Downloaded SQLite database failed PRAGMA quick_check')
    finally:
        connection.close()


def copy_checked(source, destination, expected_size, expected_sha256, label):
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: source.read(CHUNK_BYTES), b''):
        size += len(block)
        if size > expected_size:
            raise DownloadError(f'{label} exceeds the manifest byte count')
        destination.write(block)
        digest.update(block)
    if size != expected_size:
        raise DownloadError(f'{label} byte count differs from the manifest')
    if digest.hexdigest() != expected_sha256:
        raise DownloadError(f'{label} SHA-256 differs from the manifest')


def download(manifest_path=DEFAULT_MANIFEST, destination=DEFAULT_DESTINATION, force=False):
    manifest, asset = load_manifest(manifest_path)
    destination = Path(destination).expanduser().absolute()
    if destination.exists():
        if file_matches(destination, asset['uncompressed_bytes'], asset['uncompressed_sha256']):
            check_sqlite(destination)
            return {'status': 'current', 'database': str(destination),
                    'dataset_version': manifest.get('dataset_version')}
        if not force:
            raise DownloadError(f'Existing destination differs from this release: {destination}. '
                                'Choose another --destination or use --force to replace it.')
        if not destination.is_file():
            raise DownloadError(f'Destination is not a file: {destination}')
    try:
        import zstandard
    except ImportError as exc:
        raise DownloadError('Install decompression support: python3 -m pip install zstandard') from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_paths = []
    try:
        # Unique files beside the target keep replacement on the same filesystem.
        # Cleanup only touches paths created by this invocation.
        with tempfile.NamedTemporaryFile(prefix='.' + destination.name + '.', suffix='.part',
                                         dir=destination.parent, delete=False) as compressed:
            compressed_path = Path(compressed.name)
            temporary_paths.append(compressed_path)
            request = urllib.request.Request(asset['url'], headers={'User-Agent': 'FremtidensTegnestue-Data/1'})
            with urllib.request.urlopen(request, timeout=60) as response:
                copy_checked(response, compressed, asset['compressed_bytes'],
                             asset['compressed_sha256'], 'Compressed download')

        with tempfile.NamedTemporaryFile(prefix='.' + destination.name + '.', suffix='.tmp',
                                         dir=destination.parent, delete=False) as database:
            database_path = Path(database.name)
            temporary_paths.append(database_path)
            try:
                with compressed_path.open('rb') as source:
                    with zstandard.ZstdDecompressor().stream_reader(source, read_across_frames=True) as reader:
                        copy_checked(reader, database, asset['uncompressed_bytes'],
                                     asset['uncompressed_sha256'], 'Uncompressed database')
            except zstandard.ZstdError as exc:
                raise DownloadError(f'Cannot decompress SQLite asset: {exc}') from exc
            database.flush()
            os.fsync(database.fileno())
        check_sqlite(database_path)
        if force:
            os.replace(database_path, destination)
        else:
            # Publish atomically without overwriting a file created meanwhile.
            # Both files are on the same filesystem, so a hard link is atomic.
            os.link(database_path, destination)
        return {'status': 'installed', 'database': str(destination),
                'dataset_version': manifest.get('dataset_version')}
    finally:
        for path in temporary_paths:
            path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST,
                        help='Local versioned release manifest')
    parser.add_argument('--destination', type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument('--force', action='store_true', help='Replace a different existing database only after validation')
    args = parser.parse_args(argv)
    try:
        result = download(args.manifest, args.destination, args.force)
    except (ValueError, OSError, sqlite3.Error, urllib.error.URLError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
