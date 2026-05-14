#!/usr/bin/env bash
# Run a product-shaped Ocean Textual flow inside tmux (real TTY).
# Usage: bash scripts/tmux_ocean_scenario.sh tic_tac_toe_localhost
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec ./venv/bin/python -m ocean.testing.tmux_scenario_run "${1:?scenario id required — see docs/textual_tmux_pilot_scenarios.md}"
