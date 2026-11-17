import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

try:
    import zstandard
except ImportError:
    zstandard = None

spec = importlib.util.spec_from_file_location(
    'download_data', Path(__file__).resolve().parents[1] / 'scripts/download_data.py')
downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader)


@unittest.skipUnless(zstandard, 'Install zstandard to test release downloads')
class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.sqlite'
        with sqlite3.connect(self.source) as db:
            db.execute('CREATE TABLE materials(name TEXT)')
            db.execute("INSERT INTO materials VALUES ('test material')")
        self.asset = self.root / 'source.sqlite.zst'
        self.asset.write_bytes(zstandard.ZstdCompressor().compress(self.source.read_bytes()))
        self.destination = self.root / 'installed/materials.sqlite'
        self.manifest_path = self.root / 'release.json'
        self.manifest = {'schema_version': 1, 'dataset_version': 'test', 'assets': {
            'sqlite': {'url': self.asset.as_uri(), 'compression': 'zstd',
                       'compressed_bytes': self.asset.stat().st_size,
                       'compressed_sha256': hashlib.sha256(self.asset.read_bytes()).hexdigest(),
                       'uncompressed_bytes': self.source.stat().st_size,
                       'uncompressed_sha256': hashlib.sha256(self.source.read_bytes()).hexdigest()}}}
        self.write_manifest()

    def write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest))

    def assert_no_temporary_files(self):
        self.assertEqual(list(self.destination.parent.glob('.*.part')), [])
        self.assertEqual(list(self.destination.parent.glob('.*.tmp')), [])

    def test_install_verified_database_and_skip_matching_copy_without_network(self):
        result = downloader.download(self.manifest_path, self.destination)
        self.assertEqual(result['status'], 'installed')
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes())
        with patch.object(downloader.urllib.request, 'urlopen', side_effect=AssertionError('network called')):
            self.assertEqual(downloader.download(self.manifest_path, self.destination)['status'], 'current')
        self.assert_no_temporary_files()

    def test_different_existing_copy_is_not_overwritten_without_force(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b'local database to preserve')
        with patch.object(downloader.urllib.request, 'urlopen', side_effect=AssertionError('network called')):
            with self.assertRaisesRegex(downloader.DownloadError, 'Existing destination differs'):
                downloader.download(self.manifest_path, self.destination)
        self.assertEqual(self.destination.read_bytes(), b'local database to preserve')

    def test_compressed_corruption_and_size_mismatch_preserve_existing_database(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b'original')
        for change in ('checksum', 'size'):
            with self.subTest(change=change):
                compressed = self.asset.read_bytes()
                bad = bytes([compressed[0] ^ 1]) + compressed[1:] if change == 'checksum' else compressed[:-1]
                with patch.object(downloader.urllib.request, 'urlopen', return_value=io.BytesIO(bad)):
                    with self.assertRaises(downloader.DownloadError):
                        downloader.download(self.manifest_path, self.destination, force=True)
                self.assertEqual(self.destination.read_bytes(), b'original')
                self.assert_no_temporary_files()

    def test_uncompressed_integrity_failures_leave_no_new_database(self):
        for field in ('uncompressed_bytes', 'uncompressed_sha256'):
            with self.subTest(field=field):
                original = self.manifest['assets']['sqlite'][field]
                self.manifest['assets']['sqlite'][field] = original + 1 if isinstance(original, int) else '0' * 64
                self.write_manifest()
                with self.assertRaises(downloader.DownloadError):
                    downloader.download(self.manifest_path, self.destination)
                self.assertFalse(self.destination.exists())
                self.assert_no_temporary_files()
                self.manifest['assets']['sqlite'][field] = original

    def test_non_sqlite_payload_rejected_even_with_valid_hashes(self):
        data = b'This is not a SQLite database'
        self.asset.write_bytes(zstandard.ZstdCompressor().compress(data))
        self.manifest['assets']['sqlite'].update(
            compressed_bytes=self.asset.stat().st_size,
            compressed_sha256=hashlib.sha256(self.asset.read_bytes()).hexdigest(),
            uncompressed_bytes=len(data), uncompressed_sha256=hashlib.sha256(data).hexdigest())
        self.write_manifest()
        with self.assertRaises(sqlite3.DatabaseError):
            downloader.download(self.manifest_path, self.destination)
        self.assertFalse(self.destination.exists())
        self.assert_no_temporary_files()

    def test_network_failure_preserves_old_copy_and_only_removes_own_temps(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b'original')
        other = self.destination.parent / '.materials.sqlite.other.part'
        other.write_bytes(b'other operation')
        with patch.object(downloader.urllib.request, 'urlopen', side_effect=OSError('connection interrupted')):
            with self.assertRaises(OSError):
                downloader.download(self.manifest_path, self.destination, force=True)
        self.assertEqual(self.destination.read_bytes(), b'original')
        self.assertEqual(list(self.destination.parent.glob('.*.part')), [other])

    def test_force_replaces_only_after_validation(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b'original')
        replace = downloader.os.replace
        def verify_before_replace(source, destination):
            self.assertEqual(self.destination.read_bytes(), b'original')
            downloader.check_sqlite(Path(source))
            replace(source, destination)
        with patch.object(downloader.os, 'replace', side_effect=verify_before_replace) as replaced:
            downloader.download(self.manifest_path, self.destination, force=True)
        replaced.assert_called_once()
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes())
        self.assert_no_temporary_files()

    def test_destination_created_during_download_is_not_overwritten(self):
        publish = downloader.os.link
        def create_before_publish(source, destination):
            self.destination.write_bytes(b'created by another operation')
            publish(source, destination)
        with patch.object(downloader.os, 'link', side_effect=create_before_publish):
            with self.assertRaises(FileExistsError):
                downloader.download(self.manifest_path, self.destination)
        self.assertEqual(self.destination.read_bytes(), b'created by another operation')
        self.assert_no_temporary_files()

    def test_invalid_zstd_payload_preserves_existing_database(self):
        data = b'not a zstd frame'
        self.asset.write_bytes(data)
        self.manifest['assets']['sqlite'].update(
            compressed_bytes=len(data), compressed_sha256=hashlib.sha256(data).hexdigest())
        self.write_manifest()
        self.destination.parent.mkdir()
        self.destination.write_bytes(b'original')
        with self.assertRaisesRegex(downloader.DownloadError, 'Cannot decompress'):
            downloader.download(self.manifest_path, self.destination, force=True)
        self.assertEqual(self.destination.read_bytes(), b'original')
        self.assert_no_temporary_files()

    def test_invalid_manifest_has_no_side_effects(self):
        for bad_manifest in ({'schema_version': True}, {'schema_version': 1, 'assets': []}):
            self.manifest_path.write_text(json.dumps(bad_manifest))
            with self.assertRaises(downloader.DownloadError):
                downloader.download(self.manifest_path, self.destination)
        self.assertFalse(self.destination.parent.exists())


if __name__ == '__main__':
    unittest.main()
