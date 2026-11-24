#!/usr/bin/env bash
# Backwards-compatible entry point for the complete Omarchy installer.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$ROOT/dist/linux/install.py" "$@"
