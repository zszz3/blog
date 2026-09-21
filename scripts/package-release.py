#!/usr/bin/env python3
"""Package changed files plus a complete checksum manifest for the release."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile


def package(directory, remote, destination):
    files = {}
    changed = []
    for file in sorted(directory.rglob('*')):
        if file.is_symlink():
            raise ValueError('Build files cannot be symlinks')
        if not file.is_file():
            continue
        name = file.relative_to(directory).as_posix()
        if name == '.deploy-manifest.json':
            raise ValueError('Reserved deployment manifest filename')
        checksum = hashlib.sha256(file.read_bytes()).hexdigest()
        files[name] = checksum
        if remote.get('files', {}).get(name) != checksum:
            changed.append((name, file))
    manifest = json.dumps({'version': 1, 'base': remote.get('release'), 'files': files}).encode()
    with tarfile.open(destination, 'w:gz') as archive:
        member = tarfile.TarInfo('.deploy-manifest.json')
        member.size = len(manifest)
        archive.addfile(member, io.BytesIO(manifest))
        for name, file in changed:
            archive.add(file, arcname=name, recursive=False)
    print(f'Upload {len(changed)}/{len(files)} changed files; reuse {len(files)-len(changed)} verified files; archive {destination.stat().st_size} bytes')


if __name__ == '__main__':
    package(Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3]))
