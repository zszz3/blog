import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('release', Path(__file__).parents[1] / 'deploy/release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def archive(self, files=None):
        files = files or {name: b'page' for name in ['index.html', 'blog/index.html', 'search/index.html', 'rss.xml', 'pagefind/pagefind.js', 'pagefind/pagefind-entry.json']}
        files.setdefault('search.json', b'[]')
        archive = self.root / 'site.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            for name, data in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        return archive
    def publish(self, run):
        name = f'{run}-1-' + str(run) * 40
        return release.publish(self.root, self.archive(), name, run)
    def test_complete_switch_and_rollback(self):
        first = self.publish(1)['release']
        second = self.publish(2)['release']
        self.assertEqual((self.root / 'current').resolve().name, second)
        release.rollback(self.root, 'previous')
        self.assertEqual((self.root / 'current').resolve().name, first)
        self.assertEqual(json.loads((self.root / 'receipt.json').read_text())['latest_run'], 2)
    def test_incomplete_release_keeps_current(self):
        first = self.publish(1)['release']
        with self.assertRaises(ValueError):
            release.publish(self.root, self.archive({'index.html': b'partial'}), '2-1-' + '2' * 40, 2)
        self.assertEqual((self.root / 'current').resolve().name, first)
    def test_delayed_release_does_not_replace_newer(self):
        second = self.publish(2)['release']
        self.assertEqual(self.publish(1)['status'], 'skipped')
        self.assertEqual((self.root / 'current').resolve().name, second)
    def test_archive_cannot_escape_destination(self):
        destination = self.root / 'staging'
        destination.mkdir()
        with self.assertRaises(ValueError):
            release.extract(self.archive({'../outside': b'invalid'}), destination)
        self.assertFalse((self.root / 'outside').exists())
    def test_republishing_current_release_is_idempotent(self):
        self.publish(1)
        self.assertEqual(self.publish(1)['status'], 'unchanged')

if __name__ == '__main__': unittest.main()
