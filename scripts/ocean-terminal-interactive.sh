#!/usr/bin/env bash
# Full interactive Ocean (real TTY): planning + codegen after clarify — no OCEAN_TEST=1.
# Use a normal Cursor/iTerm window. Tune backend with OCEAN_CODEGEN_BACKEND or let prompts run.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

unset OCEAN_TEST || true
unset PYTEST_CURRENT_TEST || true
export OCEAN_SIMPLE_FEED="${OCEAN_SIMPLE_FEED:-1}"

# Optional hands-off codegen examples (uncomment one):
# export OCEAN_CODEGEN_BACKEND=dry_plan_only
# export OCEAN_CODEGEN_BACKEND=cursor_handoff
# export OCEAN_SKIP_BACKEND_PROMPT=1

RUNNER="${OCEAN_INTERACTIVE_RUNNER:-venv}"
if [[ "$RUNNER" == "npm" ]]; then
  exec npm start "$@"
elif [[ "$RUNNER" == "npx" ]]; then
  exec npx ocean "$@"
else
  exec ./venv/bin/ocean "$@"
fi
