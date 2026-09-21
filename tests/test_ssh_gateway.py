import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

DEPLOY = Path(__file__).parents[1] / 'deploy'
spec = importlib.util.spec_from_file_location('ssh_gateway', DEPLOY / 'ssh_gateway.py')
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, files=None):
        if files is None:
            files = {name: b'page' for name in ['index.html', 'blog/index.html', 'search/index.html',
                     'rss.xml', 'pagefind/pagefind.js', 'pagefind/pagefind-entry.json']}
            files['search.json'] = b'[]'
        result = io.BytesIO()
        with tarfile.open(fileobj=result, mode='w:gz') as archive:
            for name, data in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
        result.seek(0)
        return result

    def execute(self, command, archive=None):
        gateway.execute(command, archive or self.archive(), self.root, DEPLOY / 'release.py')

    def test_publish_and_rollback_use_fixed_release_tool(self):
        first, second = '1-1-' + 'a' * 40, '2-1-' + 'b' * 40
        self.execute('publish ' + first)
        self.execute('publish ' + second)
        self.assertEqual((self.root / 'current').resolve().name, second)
        self.execute('rollback previous')
        self.assertEqual((self.root / 'current').resolve().name, first)
        self.assertEqual(json.loads((self.root / 'receipt.json').read_text())['latest_run'], 2)
        self.assertEqual(list(self.root.glob('.ssh-upload-*')), [])

    def test_rejects_shell_commands_paths_and_extra_arguments(self):
        release = '1-1-' + 'a' * 40
        for command in ['', 'sh', 'bash -c id', 'status\n', 'status;id', 'sftp',
                        'publish previous', 'rollback ../../etc', 'publish ' + release + '; id',
                        'publish ' + release + '\n', 'publish ' + release + ' --root /tmp',
                        'publish 0-1-' + 'a' * 40]:
            with self.subTest(command=command), self.assertRaises(ValueError):
                self.execute(command)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_invalid_archive_does_not_replace_live_site(self):
        first = '1-1-' + 'a' * 40
        self.execute('publish ' + first)
        for files in [{'index.html': b'incomplete'}, {'../outside': b'escape'}]:
            with self.assertRaises(subprocess.CalledProcessError):
                self.execute('publish 2-1-' + 'b' * 40, self.archive(files))
        self.assertEqual((self.root / 'current').resolve().name, first)
        self.assertFalse((self.root / 'outside').exists())
        self.assertEqual(list(self.root.glob('.ssh-upload-*')), [])

    def test_empty_and_oversized_uploads_are_removed(self):
        with patch.object(gateway, 'MAX_ARCHIVE_BYTES', 8):
            for data in [b'', b'x' * 9]:
                with self.subTest(size=len(data)), self.assertRaises(ValueError):
                    self.execute('publish 1-1-' + 'a' * 40, io.BytesIO(data))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_status_reads_only_the_release_receipt(self):
        self.execute('publish 1-1-' + 'a' * 40)
        with patch('sys.stdout', new_callable=io.StringIO) as output:
            self.execute('status')
        self.assertEqual(json.loads(output.getvalue())['latest_run'], 1)


if __name__ == '__main__':
    unittest.main()
