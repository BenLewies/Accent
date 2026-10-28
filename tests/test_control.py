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
            self.assertEqual(run.call_args_list[0].args[0], ['systemctl', '--user', 'stop', 'accent.service'])
            self.assertNotIn('shell', run.call_args_list[0].kwargs)

    def test_failed_service_action_is_reported(self):
        with patch.object(control.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['systemctl'])):
            with self.assertRaises(subprocess.CalledProcessError): control.main('restart')

    def test_missing_service_is_distinct_from_paused(self):
        with patch.object(control, 'systemctl', side_effect=[subprocess.CompletedProcess([], 0, 'not-found\n'), subprocess.CompletedProcess([], 1, '')]):
            self.assertEqual(control.status(), {'state': 'missing', 'autostart': False})

if __name__ == '__main__': unittest.main()
