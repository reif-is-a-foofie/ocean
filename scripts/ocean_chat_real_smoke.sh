#!/usr/bin/env bash
# Real CLI smoke: invokes the same ``ocean`` entrypoint users run, with ``chat`` subcommand.
# Uses non-interactive env so CI / regression can finish without a TTY or keys.
# For a fully manual run in Terminal.app / iTerm: omit these env vars and run:
#   ./venv/bin/ocean chat
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OCEAN_BIN="$ROOT/venv/bin/ocean"
if [[ ! -x "$OCEAN_BIN" ]]; then
  echo "ocean_chat_real_smoke: skip (no $OCEAN_BIN — run: pip install -e .)"
  exit 0
fi

tmp="$(mktemp "${TMPDIR:-/tmp}/ocean-chat-smoke.XXXXXX")"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

# Bundle matches tests/test_ocean_entry_smoke.py + stable chat defaults.
# Invokes bare ``ocean`` (no args) — same code path as ``ocean chat`` after entrypoint routing.
env \
  OCEAN_DISABLE_WORKSPACE=1 \
  OCEAN_DISABLE_CODEX=1 \
  OCEAN_SIMPLE_FEED=1 \
  OCEAN_SKIP_BACKEND_PROMPT=1 \
  OCEAN_SKIP_REPO_PROMPT=1 \
  OCEAN_SKIP_MODEL_PROMPT=1 \
  OCEAN_NO_SELF_UPDATE=1 \
  OCEAN_TEST=1 \
  OCEAN_ALLOW_QUESTIONS=0 \
  "$OCEAN_BIN" >"$tmp" 2>&1

grep -q "Crew assembled" "$tmp" || { echo "---- ocean output ----"; cat "$tmp"; exit 1; }
grep -q "Session complete" "$tmp" || { echo "---- ocean output ----"; cat "$tmp"; exit 1; }
echo "OK ocean (bare entrypoint → chat, real subprocess, bounded env)"
