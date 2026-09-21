import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


REPO = Path(__file__).parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


release = module('incremental_release', REPO / 'deploy/release.py')
packager = module('packager', REPO / 'scripts/package-release.py')


class IncrementalReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'server'
        self.root.mkdir()
        self.dist = Path(self.temp.name) / 'dist'
        for name in ['index.html', 'blog/index.html', 'search/index.html', 'rss.xml',
                     'pagefind/pagefind.js', 'pagefind/pagefind-entry.json', 'old.html', 'image.webp']:
            self.write(name, b'original')
        self.write('search.json', b'[]')
        self.archive = Path(self.temp.name) / 'site.tar.gz'
        self.first = '1-1-' + 'a' * 40
        self.second = '2-1-' + 'b' * 40
        packager.package(self.dist, release.inventory(self.root), self.archive)
        release.publish(self.root, self.archive, self.first, 1)

    def write(self, name, content):
        file = self.dist / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)

    def manifest_archive(self, manifest, uploaded=None):
        with tarfile.open(self.archive, 'w:gz') as archive:
            files = {release.MANIFEST_NAME: json.dumps(manifest).encode(), **(uploaded or {})}
            for name, content in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))

    def test_increment_reuses_unchanged_files_and_applies_add_change_delete(self):
        remote = release.inventory(self.root)
        self.write('index.html', b'updated')
        self.write('new/index.html', b'new article')
        (self.dist / 'old.html').unlink()
        packager.package(self.dist, remote, self.archive)
        with tarfile.open(self.archive) as archive:
            self.assertEqual(set(archive.getnames()), {release.MANIFEST_NAME, 'index.html', 'new/index.html'})
        release.publish(self.root, self.archive, self.second, 2)
        current = self.root / 'current'
        self.assertEqual((current / 'index.html').read_bytes(), b'updated')
        self.assertEqual((current / 'new/index.html').read_bytes(), b'new article')
        self.assertEqual((current / 'image.webp').read_bytes(), b'original')
        self.assertFalse((current / 'old.html').exists())
        self.assertFalse((current / release.MANIFEST_NAME).exists())
        self.assertEqual((self.root / 'previous' / 'index.html').read_bytes(), b'original')
        release.rollback(self.root, 'previous')
        self.assertEqual((current / 'index.html').read_bytes(), b'original')

    def test_reused_and_uploaded_checksums_are_verified_before_switching(self):
        remote = release.inventory(self.root)
        for uploaded in [{}, {'index.html': b'tampered upload'}]:
            manifest = {'version': 1, 'base': self.first, 'files': dict(remote['files'])}
            if not uploaded:
                manifest['files']['image.webp'] = '0' * 64
            self.manifest_archive(manifest, uploaded)
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                release.publish(self.root, self.archive, self.second, 2)
            self.assertEqual((self.root / 'current').resolve().name, self.first)

    def test_unsafe_missing_and_unlisted_files_are_rejected(self):
        remote = release.inventory(self.root)
        cases = [
            ({'version': 1, 'base': '../outside', 'files': remote['files']}, {}),
            ({'version': 1, 'base': self.first, 'files': {'../outside': '0' * 64}}, {}),
            ({'version': 1, 'base': self.first, 'files': {'/outside': '0' * 64}}, {}),
            ({'version': 1, 'base': self.first, 'files': {'missing.html': '0' * 64}}, {}),
            ({'version': 1, 'base': self.first, 'files': remote['files']}, {'extra.html': b'unlisted'}),
        ]
        for manifest, uploaded in cases:
            with self.subTest(manifest=manifest):
                self.manifest_archive(manifest, uploaded)
                with self.assertRaises(ValueError):
                    release.publish(self.root, self.archive, self.second, 2)
                self.assertEqual((self.root / 'current').resolve().name, self.first)

    def test_manifest_gateway_returns_only_current_public_files(self):
        gateway = module('incremental_gateway', REPO / 'deploy/ssh_gateway.py')
        self.assertEqual(gateway.parse_command('manifest'), ('manifest', None))
        result = subprocess.run(['python3', '-I', str(REPO / 'deploy/release.py'),
                                 'manifest', '--root', str(self.root)], check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        self.assertEqual(data, release.inventory(self.root))
        self.assertNotIn('receipt.json', data['files'])
        with self.assertRaises(ValueError):
            gateway.parse_command('manifest /etc')


if __name__ == '__main__':
    unittest.main()
