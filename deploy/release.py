#!/usr/bin/env python3
"""Validate and switch complete static releases. Run as the dedicated deploy user."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile

RELEASE_ID = re.compile(r"^[0-9]+-[0-9]+-[a-f0-9]{40}$")
MANIFEST_NAME = '.deploy-manifest.json'


def digest(file):
    value = hashlib.sha256()
    with file.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def inventory(root):
    current = root / 'current'
    if not current.is_symlink():
        return {'release': None, 'files': {}}
    directory = current.resolve()
    if directory.parent != (root / 'releases').resolve() or not RELEASE_ID.fullmatch(directory.name):
        raise ValueError('Invalid current release')
    files = {}
    for file in sorted(directory.rglob('*')):
        if file.is_symlink():
            raise ValueError('Release files cannot be symlinks')
        if file.is_file():
            files[file.relative_to(directory).as_posix()] = digest(file)
    return {'release': directory.name, 'files': files}


def complete_increment(root, staging):
    manifest = staging / MANIFEST_NAME
    if not manifest.exists():
        return  # Backward-compatible complete archive.
    if manifest.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Manifest is too large')
    data = json.loads(manifest.read_text())
    files = data.get('files')
    base = data.get('base')
    if data.get('version') != 1 or not isinstance(files, dict) or len(files) > 50000:
        raise ValueError('Invalid deployment manifest')
    if base is not None and (not isinstance(base, str) or not RELEASE_ID.fullmatch(base)):
        raise ValueError('Invalid base release')
    for name, expected in files.items():
        path = PurePosixPath(name)
        if (not path.parts or path.is_absolute() or '..' in path.parts or str(path) != name
                or name == MANIFEST_NAME or '\\' in name or '\x00' in name
                or not isinstance(expected, str) or not re.fullmatch(r'[a-f0-9]{64}', expected)):
            raise ValueError('Unsafe manifest entry')
    manifest.unlink()
    uploaded = {file.relative_to(staging).as_posix() for file in staging.rglob('*') if file.is_file()}
    if uploaded - files.keys():
        raise ValueError('Archive contains files absent from manifest')
    size = 0
    for name, expected in files.items():
        target = staging / name
        if not target.exists():
            if base is None:
                raise ValueError('Missing uploaded file: ' + name)
            base_directory = root / 'releases' / base
            source = base_directory / name
            if (base_directory.is_symlink() or not source.is_file()
                    or not source.resolve().is_relative_to(base_directory.resolve())):
                raise ValueError('Missing or unsafe reused file: ' + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o644)
        if not target.is_file() or digest(target) != expected:
            raise ValueError('File checksum mismatch: ' + name)
        size += target.stat().st_size
        if size > 1024 ** 3:
            raise ValueError('Release is too large')


def atomic_json(path, value):
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False) + '\n')
    os.replace(temp, path)


def switch(root, release):
    current = root / 'current'
    if current.is_symlink():
        previous = root / '.previous-next'
        previous.unlink(missing_ok=True)
        previous.symlink_to(os.readlink(current))
        os.replace(previous, root / 'previous')
    elif current.exists():
        raise ValueError('current must be a symlink; refusing to overwrite an existing directory')
    link = root / '.current-next'
    link.unlink(missing_ok=True)
    link.symlink_to('releases/' + release)
    os.replace(link, current)


def validate(directory):
    required = ['index.html', 'blog/index.html', 'search/index.html', 'search.json',
                'rss.xml', 'pagefind/pagefind.js', 'pagefind/pagefind-entry.json']
    for name in required:
        file = directory / name
        if not file.is_file() or file.stat().st_size == 0:
            raise ValueError('Incomplete release: ' + name)
    index = json.loads((directory / 'search.json').read_text())
    if not isinstance(index, list):
        raise ValueError('Invalid search index')
    if (directory / '.prerender').exists() or (directory / 'server').exists():
        raise ValueError('Only public static files may be deployed')


def extract(archive, target):
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        if len(members) > 50000 or sum(m.size for m in members) > 1024 ** 3:
            raise ValueError('Archive is too large')
        for member in members:
            parts = Path(member.name).parts
            if Path(member.name).is_absolute() or '..' in parts or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe archive member')
            destination = target / member.name
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                source = tar.extractfile(member)
                with source, destination.open('xb') as output:
                    shutil.copyfileobj(source, output)
                destination.chmod(0o644)


def publish(root, archive, release, run):
    if not RELEASE_ID.fullmatch(release):
        raise ValueError('Invalid release ID')
    receipt_file = root / 'receipt.json'
    receipt = json.loads(receipt_file.read_text()) if receipt_file.exists() else {}
    if run < receipt.get('latest_run', 0):
        return {'status': 'skipped', 'reason': 'A newer run has already been published'}
    if (root / 'current').is_symlink() and os.readlink(root / 'current') == 'releases/' + release:
        return {'status': 'unchanged', 'release': release}
    releases = root / 'releases'
    releases.mkdir(exist_ok=True)
    target = releases / release
    with tempfile.TemporaryDirectory(prefix='.incoming-', dir=root) as temp:
        staging = Path(temp) / 'site'
        staging.mkdir()
        extract(archive, staging)
        complete_increment(root, staging)
        validate(staging)
        # Keep content-addressed assets available to readers who still have an older page open.
        shared = root / 'shared'
        for name in ['_astro', '_fonts']:
            if (staging / name).is_dir():
                shutil.copytree(staging / name, shared / name, dirs_exist_ok=True)
        for file in (staging / 'pagefind').rglob('*'):
            if file.suffix in {'.pf_fragment', '.pf_index', '.pf_meta'}:
                dest = shared / file.relative_to(staging)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.copy2(file, dest)
        if target.exists():
            raise ValueError('This release ID already exists; use a new run attempt')
        os.replace(staging, target)
    switch(root, release)
    result = {'status': 'published', 'release': release, 'latest_run': run}
    atomic_json(receipt_file, result)
    return result


def rollback(root, release):
    if release == 'previous':
        previous = root / 'previous'
        if not previous.is_symlink():
            raise ValueError('No previous release exists')
        release = Path(os.readlink(previous)).name
    if not RELEASE_ID.fullmatch(release):
        raise ValueError('Invalid release ID')
    validate(root / 'releases' / release)
    switch(root, release)
    # Preserve latest_run so a delayed older build cannot undo this rollback.
    receipt_file = root / 'receipt.json'
    receipt = json.loads(receipt_file.read_text()) if receipt_file.exists() else {}
    receipt.update(status='rolled_back', release=release)
    atomic_json(receipt_file, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['publish', 'rollback', 'manifest'])
    parser.add_argument('--root', required=True)
    parser.add_argument('--archive')
    parser.add_argument('--release')
    parser.add_argument('--run', type=int, default=0)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if root == Path('/'):
        raise ValueError('A dedicated site directory is required')
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.deploy.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.operation == 'manifest':
            result = inventory(root)
        elif not args.release:
            parser.error('--release is required for publish and rollback')
        else:
            result = publish(root, args.archive, args.release, args.run) if args.operation == 'publish' else rollback(root, args.release)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
