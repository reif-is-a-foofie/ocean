#!/usr/bin/env bash
# Regression: pytest + Ocean MCP stdio smoke + CLI sanity.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/venv/bin/python" ]]; then
  PY="$ROOT/venv/bin/python"
elif [[ -n "${PYTHON:-}" ]]; then
  PY="$PYTHON"
else
  PY="$(command -v python3 || command -v python)"
fi

echo "== Ocean regression: pytest =="
"$PY" -m pytest tests/ -q

echo "== Ocean regression: MCP stdio smoke =="
"$PY" "$ROOT/scripts/mcp_stdio_smoke.py"

echo "== Ocean regression: CLI smoke =="
"$PY" -m ocean --help >/dev/null
"$PY" -m ocean --version

echo "== Ocean regression: ocean (bare → chat, real venv entrypoint) =="
bash "$ROOT/scripts/ocean_chat_real_smoke.sh"

echo "== OK =="
