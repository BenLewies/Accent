#!/usr/bin/env python3
"""Local lifecycle controls for the runtime shipped inside the plugin.

No downloads, builds, system packages, device permissions or root operations.
The Quickshell Process owns the daemon and releases it on plugin unload.
"""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

NAME = 'io.github.BenLewies.Accent'
OBJECT = '/io/github/BenLewies/Accent'


def config_dir():
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'accent'


def preferences():
    try:
        data = json.loads((config_dir() / 'bar.json').read_text())
        return {'autostart': data.get('autostart', True) is not False, 'migrated': data.get('migrated') is True}
    except (OSError, ValueError, AttributeError):
        return {'autostart': True, 'migrated': False}


def save(data):
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=directory, delete=False) as output:
        json.dump(data, output)
        temporary = output.name
    os.replace(temporary, directory / 'bar.json')


def binary():
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise RuntimeError('The Omarchy plugin currently supports Linux x86_64.')
    path = Path(__file__).resolve().parent / 'runtime/linux-x86_64/accent'
    if not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError('The bundled Accent program is missing. Update or reinstall the plugin.')
    return path


def call(method):
    return subprocess.run(['busctl', '--user', '--timeout=2', 'call', NAME, OBJECT, NAME, method],
                          capture_output=True, text=True, timeout=3)


def status():
    result = call('InputReady')
    ready = result.returncode == 0 and result.stdout.strip() == 'b true'
    error = ''
    if result.returncode == 0 and not ready:
        detail = call('InputError')
        try:
            error = json.loads(detail.stdout.strip()[2:]) if detail.returncode == 0 else ''
        except ValueError:
            pass
    return {'state': 'active' if ready else ('starting' if result.returncode == 0 and not error else 'inactive'),
            'autostart': preferences()['autostart'], 'error': error}


def initialize():
    binary()
    prefs = preferences()
    if not prefs['migrated']:
        # Transition installations made with the old installer to plugin-owned
        # startup. Only stop the unit if it actually runs Accent's old binary.
        unit = subprocess.run(['systemctl', '--user', 'show', 'accent.service', '--property=ExecStart', '--value'],
                              text=True, capture_output=True, timeout=3)
        old_binary = str(Path.home() / '.local/bin/accent')
        if ('path=' + old_binary + ' ;') in unit.stdout:
            enabled = subprocess.run(['systemctl', '--user', 'is-enabled', 'accent.service'],
                                     text=True, capture_output=True, timeout=3)
            prefs['autostart'] = enabled.stdout.strip() == 'enabled'
            subprocess.run(['systemctl', '--user', 'disable', '--now', 'accent.service'],
                           capture_output=True, text=True, timeout=10, check=True)
        prefs['migrated'] = True
        save(prefs)
    return dict(status(), should_run=prefs['autostart'])


def main(action):
    if action == 'initialize':
        return initialize()
    if action == 'status':
        return status()
    if action in ('enable', 'disable'):
        prefs = preferences()
        prefs['autostart'] = action == 'enable'
        save(prefs)
        result = status()
        if action == 'enable':
            result['should_run'] = True
        return result
    if action == 'settings':
        result = call('OpenSettings')
        if result.returncode:
            return dict(status(), should_run=True, open_settings=True)
    elif action in ('stop', 'restart'):
        call('Quit')
        return dict(status(), should_run=action == 'restart')
    elif action == 'start':
        return dict(status(), should_run=True)
    else:
        raise ValueError('Unknown action')
    return status()


if __name__ == '__main__':
    try:
        print(json.dumps(main(sys.argv[1] if len(sys.argv) == 2 else 'status')))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({'error': str(error)}))
        sys.exit(1)
