#!/usr/bin/env bash
# Activate the api-service virtualenv and run the given command (or a shell) with it.
# This avoids accidentally using Homebrew/pyenv interpreters that lack dev deps.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"

if [[ ! -d "$VENV" ]]; then
  echo "error: .venv missing. Run 'hatch env create' in apps/api-service first." >&2
  exit 1
fi

source "$VENV/bin/activate"

python - <<'PY' || { echo "error: interpreter is not .venv" >&2; exit 1; }
import sys
from pathlib import Path

exe = Path(sys.executable)
if ".venv" not in exe.parts:
    raise SystemExit(f"expected .venv interpreter, got {exe}")
print(f"Using virtualenv: {exe.parent.parent}")
PY

if [[ $# -eq 0 ]]; then
  exec "${SHELL:-/bin/bash}"
else
  exec "$@"
fi
