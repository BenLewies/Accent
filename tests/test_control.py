import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('control', Path(__file__).resolve().parents[1] / 'dist/omarchy/control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)

class ServiceControlTests(unittest.TestCase):
    def test_unknown_action_cannot_execute_commands(self):
        with patch.object(control.subprocess, 'run') as run:
            with self.assertRaises(ValueError): control.main('stop; touch /tmp/unwanted')
            run.assert_not_called()

    def test_pause_has_fixed_unprivileged_arguments(self):
        with patch.object(control.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'active\n', '')) as run:
            control.main('stop')
            self.assertEqual(run.call_args_list[0].args[0], ['busctl', '--user', '--timeout=2', 'call', control.NAME, control.OBJECT, control.NAME, 'Quit'])
            self.assertNotIn('shell', run.call_args_list[0].kwargs)

    def test_failed_service_action_is_reported(self):
        with patch.object(control.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['systemctl'])):
            with self.assertRaises(subprocess.CalledProcessError): control.main('restart')

    def test_missing_daemon_is_inactive_without_a_service_dependency(self):
        with patch.object(control, 'call', return_value=subprocess.CompletedProcess([], 1, '')), patch.object(control, 'preferences', return_value={'autostart': True}):
            self.assertEqual(control.status(), {'state': 'inactive', 'autostart': True, 'error': ''})

if __name__ == '__main__': unittest.main()
