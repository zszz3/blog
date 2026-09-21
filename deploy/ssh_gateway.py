#!/usr/bin/env python3
"""Root-owned SSH entry point: receive a static site, roll back, or read status."""
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile

SITE_ROOT = Path('/opt/wojiecihuo/site')
RELEASE_TOOL = Path('/usr/local/lib/wojiecihuo-publisher/release.py')
RELEASE_ID = r'[1-9][0-9]{0,9}-[1-9][0-9]{0,5}-[a-f0-9]{40}'
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024


def parse_command(command):
    if command == 'status':
        return 'status', None
    match = re.fullmatch(r'(publish|rollback) (' + RELEASE_ID + r'|previous)', command)
    if not match or (match[1] == 'publish' and match[2] == 'previous'):
        raise ValueError('Only publish, rollback, and status are allowed')
    return match[1], match[2]


def receive_archive(source, destination):
    size = 0
    while chunk := source.read(1024 * 1024):
        size += len(chunk)
        if size > MAX_ARCHIVE_BYTES:
            raise ValueError('Archive exceeds the upload limit')
        destination.write(chunk)
    if size == 0:
        raise ValueError('Empty archive')


def execute(command, source, root=SITE_ROOT, release_tool=RELEASE_TOOL):
    operation, release = parse_command(command)
    if operation == 'status':
        print((root / 'receipt.json').read_text().strip())
        return
    args = [sys.executable, '-I', str(release_tool), operation, '--root', str(root), '--release', release]
    if operation == 'rollback':
        subprocess.run(args, check=True, timeout=120, stdin=subprocess.DEVNULL)
        return
    # Unique temporary files keep incomplete/concurrent uploads separate. Never
    # use a client-supplied pathname or execute a shell command from the client.
    with tempfile.NamedTemporaryFile(prefix='.ssh-upload-', suffix='.tar.gz', dir=root) as archive:
        receive_archive(source, archive)
        archive.flush()
        args += ['--archive', archive.name, '--run', release.split('-')[0]]
        subprocess.run(args, check=True, timeout=120, stdin=subprocess.DEVNULL)


def main():
    def timeout(_signum, _frame):
        raise TimeoutError('Deployment request timed out')

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(300)
    try:
        execute(os.environ.get('SSH_ORIGINAL_COMMAND', ''), sys.stdin.buffer)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        signal.alarm(0)
    return 0


if __name__ == '__main__':
    sys.exit(main())
