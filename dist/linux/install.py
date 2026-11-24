#!/usr/bin/env python3
"""Install Accent's runtime and Omarchy plugin together; never run on widget load."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
from urllib.request import urlopen

REPOSITORY = 'https://github.com/BenLewies/Accent'
ASSET = 'accent-linux-x86_64.tar.gz'
RUNTIME_PACKAGES = ['libxkbcommon', 'libevdev', 'libx11', 'libxcb', 'libxi', 'libxtst',
                    'wayland', 'fontconfig', 'alsa-lib', 'mesa', 'wl-clipboard']
BUILD_PACKAGES = ['base-devel', 'rust', 'pkgconf', 'libxkbcommon-x11', 'libxcursor',
                  'libxrandr', 'libxinerama']
NOTICES = ['LICENSE', 'NOTICE.md', 'THIRD_PARTY_NOTICES.md', 'RUST_DEPENDENCY_LICENSES.txt']
MAX_ARCHIVE = 150 * 1024 * 1024
MAX_UNPACKED = 300 * 1024 * 1024


def run(*args, check=True, timeout=60, **kwargs):
    return subprocess.run([str(a) for a in args], check=check, text=True,
                          timeout=timeout, **kwargs)


def capture(*args, check=True):
    return run(*args, check=check, timeout=10, capture_output=True).stdout.strip()


def version_at(root):
    return tomllib.loads((root / 'Cargo.toml').read_text())['package']['version']


def download(url, destination, limit):
    # All install URLs are constructed locally from a fixed HTTPS repository.
    with urlopen(url, timeout=30) as response, destination.open('wb') as output:
        if not response.geturl().startswith('https://'):
            raise RuntimeError('Release download redirected away from HTTPS')
        count = 0
        while chunk := response.read(64 * 1024):
            count += len(chunk)
            if count > limit:
                raise RuntimeError('Download exceeds the expected size limit')
            output.write(chunk)


def verify_checksum(archive, sums):
    matches = []
    for line in sums.splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64}) [ *](\S+)', line)
        if match and match[2] == ASSET:
            matches.append(match[1].lower())
    if len(matches) != 1:
        raise RuntimeError('Release must contain exactly one checksum for ' + ASSET)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != matches[0]:
        raise RuntimeError('Release checksum mismatch; the downloaded program was not installed')


def extract_package(archive, destination):
    """Validate every member before writing; reject links and special files."""
    with tarfile.open(archive, 'r:gz') as source:
        members = source.getmembers()
        if not members or len(members) > 5000 or sum(m.size for m in members) > MAX_UNPACKED:
            raise RuntimeError('Invalid or oversized release archive')
        seen = set()
        for member in members:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or '..' in name.parts or not name.parts
                    or name.parts[0] != 'accent-linux-x86_64'
                    or member.name in seen or not (member.isfile() or member.isdir())):
                raise RuntimeError('Unsafe release archive member: ' + member.name)
            seen.add(member.name)
        # Manual extraction avoids tar's symlink, ownership and special-file semantics.
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as data, target.open('wb') as output:
                    shutil.copyfileobj(data, output)
                target.chmod(0o755 if target.name == 'accent' else 0o644)
    package = destination / 'accent-linux-x86_64'
    for name in ['accent', 'BUILD.json', *NOTICES]:
        if not (package / name).is_file():
            raise RuntimeError('Release package is incomplete: ' + name)
    return package


def release_package(root, temporary, version):
    tag = os.environ.get('ACCENT_VERSION', 'v' + version)
    if tag != 'v' + version:
        raise RuntimeError('Installer and release versions must match; check out the requested release tag')
    base = f'{REPOSITORY}/releases/download/{tag}'
    archive = temporary / ASSET
    sums = temporary / 'SHA256SUMS'
    print('Downloading Accent ' + tag, flush=True)
    download(base + '/' + ASSET, archive, MAX_ARCHIVE)
    download(base + '/SHA256SUMS', sums, 64 * 1024)
    verify_checksum(archive, sums.read_text())
    package = extract_package(archive, temporary)
    build = json.loads((package / 'BUILD.json').read_text())
    commit = capture('git', '-C', root, 'rev-parse', 'HEAD')
    if build.get('version') != version or build.get('commit') != commit:
        raise RuntimeError('Release does not match this checkout; use the release tag or --from-source')
    if shutil.which('gh') and run('gh', 'auth', 'status', check=False,
                                  capture_output=True).returncode == 0:
        run('gh', 'attestation', 'verify', archive, '--repo', 'BenLewies/Accent', timeout=90)
    return package


def build_package(root, temporary, version):
    run('cargo', 'build', '--release', '--locked', cwd=root, timeout=1200)
    package = temporary / 'source-package'
    package.mkdir()
    target = Path(os.environ.get('CARGO_TARGET_DIR', str(root / 'target')))
    if not target.is_absolute():
        target = root / target
    shutil.copy2(target / 'release/accent', package / 'accent')
    for name in ['LICENSE', 'NOTICE.md', 'THIRD_PARTY_NOTICES.md']:
        shutil.copy2(root / name, package / name)
    run(sys.executable, root / 'scripts/bundle_notices.py', '--target',
        'x86_64-unknown-linux-gnu', '--output', package / NOTICES[-1], cwd=root, timeout=600)
    (package / 'BUILD.json').write_text(json.dumps({
        'version': version, 'commit': capture('git', '-C', root, 'rev-parse', 'HEAD')}))
    return package


def keyboard_paths():
    result = []
    for event in sorted(Path('/dev/input').glob('event*')):
        # evdev identifies keyboard-capable devices using their key capability bitmap.
        capabilities = Path('/sys/class/input') / event.name / 'device/capabilities/key'
        try:
            words = capabilities.read_text().split()
            # KEY_A=30 and KEY_Z=44 fit the least-significant 64-bit word.
            bits = int(words[-1], 16)
            if bits & (1 << 30) and bits & (1 << 44):
                result.append(event)
        except (OSError, ValueError, IndexError):
            continue
    return result


def input_access():
    keyboards = keyboard_paths()
    return (bool(keyboards) and all(os.access(p, os.R_OK | os.W_OK) for p in keyboards)
            and os.access('/dev/uinput', os.R_OK | os.W_OK))


def preflight():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise RuntimeError('This installer supports Omarchy on Linux x86_64')
    if os.geteuid() == 0:
        raise RuntimeError('Run as your desktop user, without sudo; only device setup requests administrator access')
    for command in ['omarchy', 'omarchy-shell', 'omarchy-plugin-validate', 'git', 'systemctl', 'pacman', 'busctl']:
        if not shutil.which(command):
            raise RuntimeError('Required Omarchy command is missing: ' + command)
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        raise RuntimeError('Run this installer from a terminal in your Omarchy desktop session')
    run('systemctl', '--user', 'show-environment', capture_output=True)
    capture('omarchy-shell', 'shell', 'ping')


def dependencies(from_source):
    packages = RUNTIME_PACKAGES + (BUILD_PACKAGES if from_source else [])
    missing = [p for p in packages if run('pacman', '-Q', '--', p, check=False,
                                         capture_output=True).returncode != 0]
    if missing:
        print('Installing required packages: ' + ', '.join(missing), flush=True)
        run('omarchy', 'pkg', 'add', *missing, timeout=1200)


def configure_input(root):
    if input_access():
        return
    print('Accent needs access to keyboard devices and a virtual keyboard.\n'
          'The administrator prompt grants access to the active local session;\n'
          'it does not add you to the input group or require a reboot.', flush=True)
    elevation = 'sudo' if sys.stdin.isatty() and sys.stdout.isatty() else 'pkexec'
    if not shutil.which(elevation):
        raise RuntimeError('Cannot request administrator access: ' + elevation + ' is missing')
    run(elevation, 'bash', root / 'dist/linux/setup-input.sh', timeout=120)
    if not input_access():
        raise RuntimeError('Keyboard access is not ready. Keep the local session active and rerun the installer; no success was reported')


class FileChanges:
    """Back up replaced user files and roll them back if installation fails."""
    def __init__(self, backup):
        self.backup = backup
        self.entries = []

    def write(self, target, data, mode=0o644):
        target.parent.mkdir(parents=True, exist_ok=True)
        saved = None
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_file():
                raise RuntimeError('Refusing to replace a non-regular file: ' + str(target))
            saved = self.backup / str(len(self.entries))
            shutil.copy2(target, saved)
        self.entries.append((target, saved))
        (self.backup / 'files.json').write_text(json.dumps([
            {'path': str(p), 'backup': str(b) if b else None} for p, b in self.entries], indent=2))
        temporary = target.with_name('.' + target.name + '.accent-new')
        temporary.write_bytes(data)
        temporary.chmod(mode)
        os.replace(temporary, target)

    def rollback(self):
        for target, saved in reversed(self.entries):
            target.with_name('.' + target.name + '.accent-new').unlink(missing_ok=True)
            if saved is None:
                target.unlink(missing_ok=True)
            else:
                restored = target.with_name('.' + target.name + '.accent-restore')
                shutil.copy2(saved, restored)
                os.replace(restored, target)


def install_runtime(root, package, home, changes):
    binary = home / '.local/bin/accent'
    if any(c in str(binary) for c in ['\n', '\r', '%']):
        raise RuntimeError('Home path cannot contain newlines or systemd specifiers')
    changes.write(binary, (package / 'accent').read_bytes(), 0o755)
    unit = (root / 'dist/linux/accent.service').read_text()
    # Quoting is required for home directories containing spaces.
    executable = str(binary).replace('\\', '\\\\').replace('"', '\\"')
    unit = unit.replace('ExecStart=/usr/bin/accent --daemon', f'ExecStart="{executable}" --daemon')
    changes.write(home / '.config/systemd/user/accent.service', unit.encode())
    desktop = (root / 'dist/linux/accent.desktop').read_text()
    desktop_exec = str(binary).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    desktop = desktop.replace('Exec=accent --settings', f'Exec="{desktop_exec}" --settings')
    changes.write(home / '.local/share/applications/accent.desktop', desktop.encode())
    for name in NOTICES:
        changes.write(home / '.local/share/licenses/accent' / name, (package / name).read_bytes())
    for source, size, extension in [('icon-app.svg', 'scalable', 'svg'),
                                   ('icon-app-256.png', '256x256', 'png'),
                                   ('icon-app-512.png', '512x512', 'png')]:
        changes.write(home / '.local/share/icons/hicolor' / size / 'apps' / ('accent.' + extension),
                      (root / 'assets' / source).read_bytes())
    changes.write(home / '.local/share/accent/BUILD.json', (package / 'BUILD.json').read_bytes())


def prepare_plugin(root, home):
    target = home / '.config/omarchy/plugins/bjl.accent'
    if target.resolve() == root.resolve():
        run('omarchy-plugin-validate', root)
        return target, None
    # No file in a different existing checkout is replaced without a full backup.
    if target.exists():
        manifest = json.loads((target / 'manifest.json').read_text())
        if manifest.get('id') != 'bjl.accent' or target.is_symlink():
            raise RuntimeError('The Accent plugin path is occupied by another plugin or a symlink')
        if (target / '.git').exists() and capture('git', '-C', target, 'status', '--porcelain'):
            raise RuntimeError('Accent plugin has local changes; commit or stash them before upgrading')
    if capture('git', '-C', root, 'status', '--porcelain'):
        raise RuntimeError('Commit source changes before installing the plugin from another checkout')
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.accent-install-', dir=target.parent))
    try:
        run('git', 'clone', '--quiet', '--no-hardlinks', '--', root, stage)
        run('git', '-C', stage, 'remote', 'set-url', 'origin', REPOSITORY + '.git')
        run('omarchy-plugin-validate', stage)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return target, stage


def health(home):
    binary = home / '.local/bin/accent'
    checks = {'binary': binary.is_file() and os.access(binary, os.X_OK),
              'keyboard_access': input_access(),
              'service': capture('systemctl', '--user', 'is-active', 'accent.service', check=False) == 'active',
              'autostart': capture('systemctl', '--user', 'is-enabled', 'accent.service', check=False) == 'enabled',
              'daemon_responding': run('busctl', '--user', '--timeout=2', 'call', 'io.github.BenLewies.Accent',
                  '/io/github/BenLewies/Accent', 'org.freedesktop.DBus.Peer', 'Ping',
                  check=False, capture_output=True).returncode == 0}
    readiness = run('busctl', '--user', '--timeout=2', 'call', 'io.github.BenLewies.Accent',
        '/io/github/BenLewies/Accent', 'io.github.BenLewies.Accent', 'InputReady',
        check=False, capture_output=True)
    checks['virtual_keyboard'] = readiness.returncode == 0 and readiness.stdout.strip() == 'b true'
    try:
        plugins = json.loads(capture('omarchy', 'plugin', 'list', '--json'))
        checks['bar_plugin'] = any(p.get('id') == 'bjl.accent' and p.get('enabled') for p in plugins)
    except (ValueError, subprocess.SubprocessError):
        checks['bar_plugin'] = False
    try:
        expected = json.loads((home / '.local/share/accent/BUILD.json').read_text())['version']
        plugin_version = json.loads((home / '.config/omarchy/plugins/bjl.accent/manifest.json').read_text())['version']
        checks['matching_versions'] = (expected == plugin_version and capture(binary, '--version') == 'accent ' + expected)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        checks['matching_versions'] = False
    return checks


def install(root, home, from_source):
    version = version_at(root)
    dependencies(from_source)
    with tempfile.TemporaryDirectory(prefix='accent-install-') as scratch:
        temporary = Path(scratch)
        package = build_package(root, temporary, version) if from_source else release_package(root, temporary, version)
        # Fail before changing an existing installation if its linked libraries are unavailable.
        linked = run('ldd', package / 'accent', capture_output=True)
        if 'not found' in linked.stdout:
            raise RuntimeError('Required runtime libraries are missing: ' + linked.stdout)
        reported = capture(package / 'accent', '--version')
        if reported != 'accent ' + version:
            raise RuntimeError('The downloaded program reports an unexpected version: ' + reported)
        target, stage = prepare_plugin(root, home)
        backup_root = home / '.local/state/accent/install-backups'
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix=time.strftime('%Y%m%d-%H%M%S-'), dir=backup_root))
        changes = FileChanges(backup)
        old_plugin = None
        previous_service = capture('systemctl', '--user', 'is-active', 'accent.service', check=False) == 'active'
        previous_plugin_enabled = any(p.get('id') == 'bjl.accent' and p.get('enabled')
            for p in json.loads(capture('omarchy', 'plugin', 'list', '--json')))
        previous_enabled = capture('systemctl', '--user', 'is-enabled', 'accent.service', check=False) == 'enabled'
        try:
            configure_input(root)
            install_runtime(root, package, home, changes)
            if stage:
                if target.exists():
                    old_plugin = backup / 'plugin'
                    shutil.move(target, old_plugin)
                stage.rename(target)
            run('systemctl', '--user', 'daemon-reload')
            run('systemctl', '--user', 'enable', 'accent.service')
            run('systemctl', '--user', 'restart', 'accent.service')
            run('omarchy-shell', 'shell', 'rescanPlugins')
            for attempt in range(30):
                listing = json.loads(capture('omarchy', 'plugin', 'list', '--json'))
                if any(p.get('id') == 'bjl.accent' for p in listing):
                    break
                time.sleep(.2)
            else:
                raise RuntimeError('Omarchy did not discover the installed plugin')
            run('omarchy', 'plugin', 'enable', 'bjl.accent')
            checks = {}
            for attempt in range(30):
                checks = health(home)
                if all(checks.values()):
                    break
                time.sleep(.2)
            else:
                raise RuntimeError('Readiness checks failed: ' + ', '.join(k for k, v in checks.items() if not v))
        except BaseException:
            run('systemctl', '--user', 'stop', 'accent.service', check=False)
            changes.rollback()
            if stage and target.exists() and not stage.exists():
                shutil.rmtree(target)
            if old_plugin and old_plugin.exists():
                shutil.move(old_plugin, target)
            if stage and stage.exists():
                shutil.rmtree(stage)
            run('systemctl', '--user', 'daemon-reload', check=False)
            if not previous_enabled:
                run('systemctl', '--user', 'disable', 'accent.service', check=False)
            if previous_service:
                run('systemctl', '--user', 'start', 'accent.service', check=False)
            if not previous_plugin_enabled:
                run('omarchy', 'plugin', 'disable', 'bjl.accent', check=False)
            run('omarchy-shell', 'shell', 'rescanPlugins', check=False)
            print('Previous user files and service state restored. Backup: ' + str(backup)
                  + '\nInstalled system packages and device-access rules are retained; '
                    'rule backups are beside the managed files in /etc.', file=sys.stderr)
            raise
    print('Accent ' + version + ' is installed and ready.\n'
          'Click Á in the bar for settings. Hold a letter and press Space to choose an accent.\n'
          'Preferences were preserved. Backup: ' + str(backup))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-source', action='store_true', help='Build this checkout instead of using the matching release')
    parser.add_argument('--check', action='store_true', help='Report installation readiness without changing anything')
    parser.add_argument('--yes', action='store_true', help='Skip the installer summary prompt; administrator authentication still applies')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    home = Path.home()
    preflight()
    if args.check:
        checks = health(home)
        print(json.dumps({'ready': all(checks.values()), 'checks': checks}, indent=2))
        return 0 if all(checks.values()) else 1
    from_source = args.from_source or os.environ.get('INSTALL_FROM_SOURCE') == '1'
    print('Install Accent for this user: program, dependencies, keyboard access,\n'
          'launcher, automatic startup, and the Omarchy bar plugin. Existing preferences are kept.')
    if not args.yes and input('Continue? [y/N] ').strip().lower() not in ('y', 'yes'):
        print('Cancelled. No changes were made.')
        return 1
    install(root, home, from_source)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('Installation cancelled.', file=sys.stderr)
        sys.exit(130)
    except (OSError, RuntimeError, ValueError, tarfile.TarError, subprocess.SubprocessError, EOFError) as error:
        print('Accent installation failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
