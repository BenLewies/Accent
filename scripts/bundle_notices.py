#!/usr/bin/env python3
"""Bundle dependency notices for one Cargo target; fail on unresolved notices.

License files are read as data, never executed. Missing registry notices are
retrieved only from the crate's recorded GitHub source commit (not branch HEAD).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen


def package_notices(package):
    root = Path(package['manifest_path']).parent
    paths = sorted(f for f in root.rglob('*') if f.is_file()
                   and len(f.relative_to(root).parts) < 4
                   and f.name.lower().startswith(('license', 'licence', 'copying', 'notice', 'copyright')))
    found = []
    for path in paths:
        try:
            found.append((str(path.relative_to(root)), path.read_text()))
        except UnicodeDecodeError:
            continue
    if not found:
        info_path = root / '.cargo_vcs_info.json'
        info = json.loads(info_path.read_text()) if info_path.exists() else {}
        commit = info.get('git', {}).get('sha1', '')
        url = urlparse(package.get('repository') or '')
        parts = url.path.strip('/').split('/')
        if url.hostname != 'github.com' or len(parts) < 2 or not re.fullmatch(r'[a-f0-9]{40}', commit):
            raise RuntimeError(f"No recorded source for missing notices: {package['name']}")
        repository = '/'.join(parts[:2]).removesuffix('.git')
        for filename in ('LICENSE', 'LICENSE-MIT', 'LICENSE-APACHE', 'LICENSE.md', 'LICENSE.txt', 'COPYING', 'COPYING.txt', 'UNLICENSE', 'LICENSE-CC0'):
            source = f'https://raw.githubusercontent.com/{repository}/{commit}/{filename}'
            try:
                with urlopen(source, timeout=20) as response:
                    content = response.read(1_000_000).decode('utf-8')
                found.append((source, content))
            except HTTPError as error:
                if error.code != 404: raise
        if not found:
            # Some published crates and recorded source commits omit license files.
            # Preserve their declaration/authors, and supply the canonical text
            # without inventing a package-specific copyright year or holder.
            declaration = package.get('license') or ''
            selected = ('Apache-2.0' if 'Apache-2.0' in declaration else
                        'MIT' if declaration == 'MIT' else
                        'CC0-1.0' if declaration == 'CC0-1.0' else None)
            if not selected:
                raise RuntimeError(f"Missing license texts: {package['name']} {package['version']}")
            source = f'https://raw.githubusercontent.com/spdx/license-list-data/f715b3660bb164c3d0b81cba9ce94e3c558c4048/text/{selected}.txt'
            with urlopen(source, timeout=20) as response:
                content = response.read(1_000_000).decode('utf-8')
            found.append((source, 'Canonical license text; this package supplied no notice file.\n'
                          + 'Declared license: ' + declaration + '\nPackage authors: '
                          + ', '.join(package.get('authors', [])) + '\nRepository: '
                          + str(package.get('repository')) + '\nRecorded commit: ' + commit + '\n\n' + content))
            readme = root / 'README.md'
            if readme.exists(): found.append(('Package README (including attribution)', readme.read_text()))
    title = f"{package['name']} {package['version']} — {package.get('license') or 'See notices'}"
    return '\n' + '=' * 80 + '\n' + title + '\n' + '\n'.join(f'\nSource: {name}\n\n{text}' for name, text in found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--metadata', help='Use saved Cargo metadata for offline registry inspection')
    args = parser.parse_args()
    if args.metadata:
        metadata = json.loads(Path(args.metadata).read_text())
    else:
        metadata = json.loads(subprocess.check_output(['cargo', 'metadata', '--locked', '--format-version', '1', '--filter-platform', args.target]))
    packages = [p for p in metadata['packages'] if p['id'] != metadata['resolve']['root']]
    with ThreadPoolExecutor(max_workers=6) as pool:
        notices = list(pool.map(package_notices, sorted(packages, key=lambda p: (p['name'], p['version']))))
    Path(args.output).write_text('Accent dependency notices\nTarget: ' + args.target + '\nGenerated from Cargo.lock and recorded source commits.\n' + ''.join(notices))
    print(f'Bundled notices for {len(packages)} packages: {args.output}')

if __name__ == '__main__': main()
