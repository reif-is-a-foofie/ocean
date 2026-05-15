#!/usr/bin/env bash
# Run opt-in live PTY pytest scenarios (requires a TTY for stdin.isatty() unless OCEAN_FORCE_LIVE_PTY=1).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/venv/bin/python" ]]; then
  PY="$ROOT/venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi
export OCEAN_LIVE_HARNESS=1
exec "$PY" -m pytest tests/test_pty_live_scenarios.py -m live_pty -q "$@"
