import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('accent_installer', ROOT / 'dist/linux/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.archive = self.root / installer.ASSET

    def archive_with(self, entries):
        with tarfile.open(self.archive, 'w:gz') as archive:
            for name, kind, contents in entries:
                entry = tarfile.TarInfo(name)
                entry.type = kind
                if kind == tarfile.REGTYPE:
                    entry.size = len(contents)
                    archive.addfile(entry, io.BytesIO(contents))
                else:
                    entry.linkname = '/tmp/unwanted'
                    archive.addfile(entry)

    def test_checksum_rejects_corruption_and_duplicate_entries(self):
        self.archive.write_bytes(b'release archive')
        checksum = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        line = checksum + '  ' + installer.ASSET
        installer.verify_checksum(self.archive, line)
        for invalid in [line + '\n' + line, '0' * 64 + '  ' + installer.ASSET,
                        checksum + '  ../' + installer.ASSET, 'not a checksum']:
            with self.subTest(invalid=invalid), self.assertRaises(RuntimeError):
                installer.verify_checksum(self.archive, invalid)

    def test_archive_rejects_traversal_links_special_files_and_duplicates(self):
        cases = [('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                 ('accent-linux-x86_64/link', tarfile.SYMTYPE),
                 ('accent-linux-x86_64/hardlink', tarfile.LNKTYPE),
                 ('accent-linux-x86_64/device', tarfile.CHRTYPE),
                 ('wrong-root/file', tarfile.REGTYPE)]
        for name, kind in cases:
            self.archive_with([('accent-linux-x86_64/first', tarfile.REGTYPE, b'first'),
                               (name, kind, b'bad')])
            destination = self.root / 'extract'
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                installer.extract_package(self.archive, destination)
            self.assertFalse(destination.exists(), 'Validate all members before extracting any')
        self.archive_with([('accent-linux-x86_64/same', tarfile.REGTYPE, b'one'),
                           ('accent-linux-x86_64/same', tarfile.REGTYPE, b'two')])
        with self.assertRaises(RuntimeError):
            installer.extract_package(self.archive, self.root / 'extract')

    def test_complete_package_extracts_without_inheriting_unsafe_modes(self):
        names = ['accent', 'BUILD.json', *installer.NOTICES]
        self.archive_with([('accent-linux-x86_64/' + name, tarfile.REGTYPE, b'content') for name in names])
        result = installer.extract_package(self.archive, self.root / 'extract')
        self.assertEqual((result / 'accent').stat().st_mode & 0o777, 0o755)
        self.assertEqual((result / 'LICENSE').stat().st_mode & 0o777, 0o644)

    def test_missing_notices_rejected(self):
        self.archive_with([('accent-linux-x86_64/accent', tarfile.REGTYPE, b'program')])
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            installer.extract_package(self.archive, self.root / 'extract')

    def test_mismatched_commit_is_rejected_before_install(self):
        package = self.root / 'package'
        package.mkdir()
        (package / 'BUILD.json').write_text(json.dumps({'version': '1.4.1', 'commit': 'other'}))
        def download(_url, destination, _limit):
            destination.write_text('placeholder')
        with patch.object(installer, 'download', side_effect=download), \
             patch.object(installer, 'verify_checksum'), \
             patch.object(installer, 'extract_package', return_value=package), \
             patch.object(installer, 'capture', return_value='expected'):
            with self.assertRaisesRegex(RuntimeError, 'does not match'):
                installer.release_package(ROOT, self.root, '1.4.1')


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.area = Path(self.temporary.name)
        self.home = self.area / 'desktop user'
        self.home.mkdir()
        self.package = self.area / 'package'
        self.package.mkdir()
        for name in ['accent', 'BUILD.json', *installer.NOTICES]:
            (self.package / name).write_text('new program' if name == 'accent' else json.dumps({'version': installer.version_at(ROOT)}))
        self.target = self.home / '.config/omarchy/plugins/bjl.accent'
        self.stage = self.home / '.config/omarchy/plugins/.accent-install-test'
        self.stage.mkdir(parents=True)
        (self.stage / 'manifest.json').write_text(json.dumps({'id': 'bjl.accent', 'version': installer.version_at(ROOT)}))
        self.state = {'active': False, 'enabled': False, 'plugin_enabled': False, 'fail_enable': False, 'interrupt_enable': False}
        self.commands = []
        self.config = self.home / '.config/accent/config.toml'
        self.config.parent.mkdir(parents=True)
        self.preferences = '# Keep this comment\nlanguages = ["Dutch"]\ntheme = "graphite-gold"\n'
        self.config.write_text(self.preferences)

    def command(self, *args, check=True, **kwargs):
        args = [str(a) for a in args]
        self.commands.append(args)
        output = ''
        result = 0
        if args[0] == 'ldd':
            output = 'all libraries found'
        elif args[-1] == '--version':
            output = 'accent ' + installer.version_at(ROOT)
        elif args[:3] == ['systemctl', '--user', 'is-active']:
            output = 'active' if self.state['active'] else 'inactive'
        elif args[:3] == ['systemctl', '--user', 'is-enabled']:
            output = 'enabled' if self.state['enabled'] else 'disabled'
        elif args[:3] == ['systemctl', '--user', 'enable']:
            self.state['enabled'] = True
        elif args[:3] == ['systemctl', '--user', 'disable']:
            self.state['enabled'] = False
        elif args[:3] in [['systemctl', '--user', 'restart'], ['systemctl', '--user', 'start']]:
            self.state['active'] = True
        elif args[:3] == ['systemctl', '--user', 'stop']:
            self.state['active'] = False
        elif args[:4] == ['omarchy', 'plugin', 'list', '--json']:
            output = json.dumps([{'id': 'bjl.accent', 'enabled': self.state['plugin_enabled']}])
        elif args[:3] == ['omarchy', 'plugin', 'enable']:
            if self.state['interrupt_enable']:
                raise KeyboardInterrupt()
            if self.state['fail_enable']:
                result = 1
            else:
                self.state['plugin_enabled'] = True
        elif args[:3] == ['omarchy', 'plugin', 'disable']:
            self.state['plugin_enabled'] = False
        if result and check:
            raise subprocess.CalledProcessError(result, args)
        return subprocess.CompletedProcess(args, result, output, '')

    def install(self):
        with patch.object(installer, 'run', side_effect=self.command), \
             patch.object(installer, 'dependencies') as dependencies, \
             patch.object(installer, 'configure_input'), \
             patch.object(installer, 'input_access', return_value=True), \
             patch.object(installer, 'release_package', return_value=self.package), \
             patch.object(installer, 'prepare_plugin', return_value=(self.target, self.stage)):
            installer.install(ROOT, self.home, False)
            dependencies.assert_called_once_with(False)

    def test_fresh_install_includes_service_launcher_plugin_and_readiness(self):
        self.install()
        self.assertEqual((self.home / '.local/bin/accent').read_text(), 'new program')
        self.assertTrue((self.target / 'manifest.json').is_file())
        unit = (self.home / '.config/systemd/user/accent.service').read_text()
        self.assertIn('ExecStart="' + str(self.home / '.local/bin/accent') + '" --daemon', unit)
        self.assertIn('ICED_BACKEND=tiny-skia', unit)
        desktop = (self.home / '.local/share/applications/accent.desktop').read_text()
        self.assertIn('" --settings', desktop)
        self.assertTrue(all(self.state[k] for k in ['active', 'enabled', 'plugin_enabled']))
        self.assertEqual(self.config.read_text(), self.preferences)
        self.assertTrue(any(cmd[0] == 'busctl' for cmd in self.commands))

    def test_upgrade_backs_up_previous_files_and_preserves_preferences(self):
        old = self.home / '.local/bin/accent'
        old.parent.mkdir(parents=True)
        old.write_text('old program')
        self.target.mkdir()
        (self.target / 'manifest.json').write_text('{"id":"bjl.accent","old":true}')
        self.state.update(active=True, enabled=True, plugin_enabled=True)
        self.install()
        backups = list((self.home / '.local/state/accent/install-backups').iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / '0').read_text(), 'old program')
        self.assertTrue((backups[0] / 'plugin/manifest.json').is_file())
        self.assertEqual(self.config.read_text(), self.preferences)

    def test_failed_enable_restores_previous_program_plugin_and_service(self):
        old = self.home / '.local/bin/accent'
        old.parent.mkdir(parents=True)
        old.write_text('old program')
        self.target.mkdir()
        old_manifest = '{"id":"bjl.accent","old":true}'
        (self.target / 'manifest.json').write_text(old_manifest)
        self.state.update(active=True, enabled=True, plugin_enabled=True, fail_enable=True)
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertEqual(old.read_text(), 'old program')
        self.assertEqual((self.target / 'manifest.json').read_text(), old_manifest)
        self.assertTrue(self.state['active'])
        self.assertTrue(self.state['enabled'])
        self.assertEqual(self.config.read_text(), self.preferences)

    def test_failed_fresh_install_removes_partial_files_and_disables_service(self):
        self.state['fail_enable'] = True
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertFalse((self.home / '.local/bin/accent').exists())
        self.assertFalse(self.target.exists())
        self.assertFalse(self.state['active'])
        self.assertFalse(self.state['enabled'])
        self.assertFalse(self.state['plugin_enabled'])
        self.assertEqual(self.config.read_text(), self.preferences)

    def test_cancelled_install_rolls_back_partial_user_files(self):
        self.state['interrupt_enable'] = True
        with self.assertRaises(KeyboardInterrupt):
            self.install()
        self.assertFalse((self.home / '.local/bin/accent').exists())
        self.assertFalse(self.target.exists())
        self.assertFalse(self.state['active'])
        self.assertEqual(self.config.read_text(), self.preferences)

    def test_symlink_targets_are_never_overwritten(self):
        outside = self.area / 'outside'
        outside.write_text('keep me')
        target = self.home / 'target'
        target.symlink_to(outside)
        backup = self.area / 'backup'
        backup.mkdir()
        changes = installer.FileChanges(backup)
        with self.assertRaises(RuntimeError):
            changes.write(target, b'replace')
        self.assertEqual(outside.read_text(), 'keep me')


class PermissionTests(unittest.TestCase):
    def test_existing_access_does_not_elevate(self):
        with patch.object(installer, 'input_access', return_value=True), patch.object(installer, 'run') as run:
            installer.configure_input(ROOT)
            run.assert_not_called()

    def test_denied_access_cannot_be_reported_as_installed(self):
        with patch.object(installer, 'input_access', return_value=False), \
             patch.object(installer.shutil, 'which', return_value='/usr/bin/pkexec'), \
             patch.object(installer, 'run'), \
             patch.object(installer.sys.stdin, 'isatty', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'not ready'):
                installer.configure_input(ROOT)

    def test_readiness_checks_include_input_not_only_service_state(self):
        with patch.object(installer, 'input_access', return_value=False), \
             patch.object(installer, 'capture', return_value='active'), \
             patch.object(installer, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')):
            checks = installer.health(Path('/nonexistent'))
            self.assertTrue(checks['service'])
            self.assertFalse(checks['keyboard_access'])
            self.assertFalse(all(checks.values()))


if __name__ == '__main__':
    unittest.main()
