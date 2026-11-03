#!/usr/bin/env python3
"""Check listing structure and required attribution without network access."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'manifest.json').read_text())
assert manifest['id'] == 'bjl.accent'
assert not manifest['id'].startswith('omarchy.')
assert (root / manifest['entryPoints']['barWidget']).is_file()
assert len(list(root.glob('**/manifest.json'))) == 1, 'Ship one root plugin manifest'
for name in ('README.md', 'LICENSE', 'NOTICE.md', 'THIRD_PARTY_NOTICES.md', 'preview.png'):
    assert (root / name).is_file(), f'Missing {name}'
license_text = (root / 'LICENSE').read_text()
assert 'Copyright (c) 2026 Victor Masson' in license_text
assert 'Permission is hereby granted, free of charge' in license_text
notices = (root / 'THIRD_PARTY_NOTICES.md').read_text()
for owner in ('Microsoft Corporation', 'Unicode', 'Nicolas Patry', 'Jerome Froelich'):
    assert owner in notices, f'Missing attribution: {owner}'
workflow = (root / '.github/workflows/release.yml').read_text()
assert 'cp LICENSE NOTICE.md THIRD_PARTY_NOTICES.md "$STAGE/"' in workflow
assert 'cp LICENSE NOTICE.md THIRD_PARTY_NOTICES.md "$APP/Contents/Resources/"' in workflow
assert 'cp RUST_DEPENDENCY_LICENSES.txt' in workflow
assert 'scripts/bundle_notices.py' in workflow
assert 'yay -S accent-bin' not in workflow, 'Do not advertise an unpublished AUR package'
import tomllib
assert manifest['version'] == tomllib.loads((root / 'Cargo.toml').read_text())['package']['version'], 'Plugin and binary versions must agree'
assert '--daemon' in (root / 'dist/linux/accent.service').read_text()
assert 'Exec=accent --settings' in (root / 'dist/linux/accent.desktop').read_text()
assert 'ExecStart=$BIN_DIR/accent --daemon' in (root / 'dist/linux/install.sh').read_text()
print('Listing structure, attribution, distribution notices, and launch modes: OK')
