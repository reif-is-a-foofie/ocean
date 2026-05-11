#!/usr/bin/env bash
# CI-like / smoke run in a *real* terminal: finishes without blocking (mirrors tests/test_ocean_entry_smoke.py).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export OCEAN_DISABLE_WORKSPACE=1
export OCEAN_DISABLE_CODEX=1
export OCEAN_SIMPLE_FEED=1
export OCEAN_SKIP_BACKEND_PROMPT=1
export OCEAN_SKIP_REPO_PROMPT=1
export OCEAN_NO_SELF_UPDATE=1
export OCEAN_TEST=1
export OCEAN_ALLOW_QUESTIONS=0

RUNNER="${OCEAN_SMOKE_RUNNER:-venv}"
if [[ "$RUNNER" == "npm" ]]; then
  exec npm start
elif [[ "$RUNNER" == "npx" ]]; then
  exec npx ocean
else
  exec ./venv/bin/ocean "$@"
fi
