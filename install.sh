#!/usr/bin/env bash
# Review this checkout, then run ./install.sh from your desktop terminal.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ROOT/dist/linux/install.py" "$@"
