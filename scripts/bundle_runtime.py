#!/usr/bin/env python3
"""Bundle or verify the offline Omarchy runtime with its exact source digest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'dist/omarchy/runtime/linux-x86_64'


def source_digest():
    paths = [ROOT / 'Cargo.toml', ROOT / 'Cargo.lock']
    for directory in ('src', 'assets', 'vendor', 'dist/linux/gnome-extension'):
        paths.extend(p for p in (ROOT / directory).rglob('*') if p.is_file() and 'target' not in p.parts)
    digest = hashlib.sha256()
    for path in sorted(paths):
        name = path.relative_to(ROOT).as_posix().encode()
        data = path.read_bytes()
        digest.update(len(name).to_bytes(8, 'big') + name + len(data).to_bytes(8, 'big') + data)
    return digest.hexdigest()


def verify():
    record = json.loads((RUNTIME / 'BUILD.json').read_text())
    assert record['version'] == tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version']
    assert record['source_sha256'] == source_digest(), 'Bundled runtime is stale; rebuild it from current source'
    assert record['binary_sha256'] == hashlib.sha256((RUNTIME / 'accent').read_bytes()).hexdigest()
    assert (RUNTIME / 'accent').read_bytes()[:4] == b'\x7fELF'
    assert os.access(RUNTIME / 'accent', os.X_OK)
    assert len((RUNTIME / 'RUST_DEPENDENCY_LICENSES.txt').read_bytes()) > 10000
    print('Bundled runtime: version, source, binary checksum, executable mode and notices match')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--notices', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--build-run')
    parser.add_argument('--source-commit')
    args = parser.parse_args()
    if not args.check:
        if not args.binary or not args.notices:
            parser.error('--binary and --notices are required when bundling')
        RUNTIME.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.binary, RUNTIME / 'accent')
        (RUNTIME / 'accent').chmod(0o755)
        shutil.copyfile(args.notices, RUNTIME / 'RUST_DEPENDENCY_LICENSES.txt')
        record = {'version': tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version'],
                  'target': 'x86_64-unknown-linux-gnu', 'source_sha256': source_digest(),
                  'binary_sha256': hashlib.sha256((RUNTIME / 'accent').read_bytes()).hexdigest()}
        if args.build_run:
            record['build_run'] = args.build_run
        if args.source_commit:
            record['source_commit'] = args.source_commit
        (RUNTIME / 'BUILD.json').write_text(json.dumps(record, indent=2) + '\n')
    verify()


if __name__ == '__main__':
    main()
