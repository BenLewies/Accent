#!/usr/bin/env python3
"""Small, bounded service controller for the Accent bar widget."""
import json
from pathlib import Path
import subprocess
import sys
import time

UNIT = 'accent.service'

def systemctl(*args, check=True):
    return subprocess.run(['systemctl', '--user', *args, UNIT], text=True,
                          capture_output=True, timeout=10, check=check)

def status():
    return {'state': systemctl('is-active', check=False).stdout.strip() or 'unknown',
            'autostart': systemctl('is-enabled', check=False).stdout.strip() == 'enabled'}

def main(action):
    if action in ('start', 'stop', 'restart', 'enable', 'disable'):
        systemctl(action)
    elif action == 'settings':
        systemctl('start')
        binary = Path.home() / '.local/bin/accent'
        for _ in range(30):
            result = subprocess.run([str(binary), '--settings'], capture_output=True,
                                    text=True, timeout=3)
            if result.returncode == 0:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(result.stderr.strip() or 'Accent settings did not open')
    elif action != 'status':
        raise ValueError('Unknown action')
    return status()

if __name__ == '__main__':
    try:
        print(json.dumps(main(sys.argv[1] if len(sys.argv) == 2 else 'status')))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({'error': str(error)}))
        sys.exit(1)
