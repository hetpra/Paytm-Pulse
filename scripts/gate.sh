#!/usr/bin/env bash
# Extension independence gate. Run from any directory: scripts/gate.sh [flag]
set -euo pipefail
FLAG="${1:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

EXT_ENABLED=none ./.venv/Scripts/python.exe -m pytest -q -p no:langsmith --ignore=tests/ext
if [[ -n "$FLAG" ]]; then
  EXT_ENABLED="$FLAG" ./.venv/Scripts/python.exe -m pytest -q -p no:langsmith "tests/ext/test_$FLAG.py"
fi
EXT_ENABLED=all ./.venv/Scripts/python.exe -m pytest -q -p no:langsmith

cd "$ROOT/frontend"
cmd.exe /c "npm run build"
