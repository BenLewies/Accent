import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bar_control', Path(__file__).resolve().parents[1] / 'dist/omarchy/control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


def reply(text='', code=0):
    return subprocess.CompletedProcess([], code, text, '')


class BarControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        directory = Path(self.temp.name)
        self.patch = patch.object(control, 'config_dir', return_value=directory)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_clean_install_starts_without_service_or_device_setup(self):
        with patch.object(control, 'binary'), patch.object(control.subprocess, 'run', return_value=reply('', 1)) as run:
            result = control.initialize()
        self.assertTrue(result['should_run'])
        self.assertTrue(control.preferences()['migrated'])
        commands = [call.args[0] for call in run.call_args_list]
        self.assertFalse(any('sudo' in c or 'pkexec' in c or 'disable' in c for c in commands))
        self.assertFalse(any('/dev/input' in str(c) for c in commands))

    def test_legacy_service_is_migrated_once_and_keeps_startup_preference(self):
        old = str(Path.home() / '.local/bin/accent')
        def run(args, **kwargs):
            if 'show' in args:
                return reply('{ path=' + old + ' ; argv[]=' + old + ' --daemon ; }')
            if 'is-enabled' in args:
                return reply('disabled\n', 1)
            return reply('', 1) if args[0] == 'busctl' else reply()
        with patch.object(control, 'binary'), patch.object(control.subprocess, 'run', side_effect=run) as calls:
            result = control.initialize()
            self.assertFalse(result['should_run'])
            self.assertEqual(sum('disable' in c.args[0] for c in calls.call_args_list), 1)
            calls.reset_mock()
            control.initialize()
            self.assertFalse(any('disable' in c.args[0] for c in calls.call_args_list))

    def test_unrelated_service_is_not_stopped(self):
        with patch.object(control, 'binary'), patch.object(control.subprocess, 'run', return_value=reply('path=/usr/bin/another-app ;')) as run:
            control.initialize()
        self.assertFalse(any('disable' in c.args[0] for c in run.call_args_list))

    def test_settings_resumes_paused_runtime_and_requests_window(self):
        with patch.object(control, 'call', return_value=reply('', 1)):
            result = control.main('settings')
        self.assertTrue(result['should_run'])
        self.assertTrue(result['open_settings'])

    def test_input_conflict_is_reported_and_not_mistaken_for_ready(self):
        with patch.object(control, 'call', side_effect=[reply('b false\n'), reply('s "Another input method is already using this seat."\n')]):
            result = control.status()
        self.assertEqual(result['state'], 'inactive')
        self.assertIn('Another input method', result['error'])

    def test_unknown_actions_do_not_run_commands(self):
        with patch.object(control.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                control.main('start; echo injected')
        run.assert_not_called()

    def test_startup_toggle_does_not_edit_typing_or_theme_preferences(self):
        typing = control.config_dir() / 'config.toml'
        typing.write_text('theme="graphite-gold"\n')
        with patch.object(control, 'call', return_value=reply('', 1)):
            control.main('disable')
        self.assertFalse(control.preferences()['autostart'])
        self.assertEqual(typing.read_text(), 'theme="graphite-gold"\n')
