#!/usr/bin/env bash
# Compatibility entry point: use Omarchy's ordinary plugin installation.
set -euo pipefail
if [[ ${1:-} == --check ]]; then
  ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  exec python3 "$ROOT/dist/omarchy/control.py" status
fi
if [[ $# -gt 1 || ( $# -eq 1 && $1 != --yes ) ]]; then
  echo 'Usage: ./install.sh [--yes|--check]' >&2
  echo 'Source builds: see docs/INSTALL.md. No separate installer is required.' >&2
  exit 2
fi
if [[ -d "$HOME/.config/omarchy/plugins/bjl.accent/.git" ]]; then
  omarchy plugin update bjl.accent "$@"
  exec omarchy plugin enable bjl.accent
fi
exec omarchy plugin add https://github.com/BenLewies/Accent --enable "$@"
