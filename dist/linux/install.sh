#!/usr/bin/env bash
# Compatibility entry point for the standard plugin installation.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
exec bash "$ROOT/install.sh" "$@"
