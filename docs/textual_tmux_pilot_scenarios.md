# Textual + Pilot + tmux: real-life test scenarios

Ocean’s Textual shell runs **Moroni-style onboarding** (five answers) then writes **`docs/project.json`**. After that you can queue **`task add …`** lines the same way you would in a real session.

This doc ties together:

1. **Scenario catalogue** — `ocean/testing/real_scenarios.py` (`TextualProductScenario`).
2. **Textual Pilot** — in-process tests in `tests/test_textual_real_scenarios.py` (fast CI).
3. **tmux** — `python -m ocean.testing.tmux_scenario_run <id>` (real pseudo-TTY, closer to how you run `ocean` in iTerm).

> These scenarios prove **spec capture + task queueing** in the Textual shell. They do **not** compile or ship a full game build; codegen still flows through **`ocean chat`** / Codex / your editor.

## Scenario IDs

| ID | Intent |
|----|--------|
| `tic_tac_toe_localhost` | Browser tic-tac-toe on localhost; three follow-up tasks (board, win detection, dev server docs). |
| `paddle_wars_keen` | Keen-style paddle arena; three follow-up tasks (paddle/ball, bricks/HUD, pause/restart). |
| `cli_devtools_scratch` | Small **cli** utility; one follow-up task. |

## Pilot (pytest)

```bash
pytest tests/test_textual_real_scenarios.py -q --tb=short
```

Parametrized over every scenario in `SCENARIOS`.

## tmux (manual or optional CI)

From the **repository root** (venv with `ocean` installed):

```bash
python -m ocean.testing.tmux_scenario_run tic_tac_toe_localhost
python -m ocean.testing.tmux_scenario_run paddle_wars_keen
```

Or the thin wrapper:

```bash
bash scripts/tmux_ocean_scenario.sh paddle_wars_keen
```

Requirements: **`tmux`** on `PATH`, **`./venv/bin/ocean`** executable.

The driver creates a **temporary workspace**, starts **`ocean`** inside tmux (so stdin/stdout are TTYs), **types each line** with pauses, then checks **`docs/project.json`** on disk.

## Adding a scenario

1. Append a new `TextualProductScenario(...)` to `ocean/testing/real_scenarios.py` and register it in `SCENARIOS`.
2. Keep **`onboarding_lines` ASCII-only** and avoid embedded quotes (tmux `send-keys` passes each Python `str` as one argument — spaces are fine).
3. Run Pilot + tmux smoke for the new id.

## Failure triage

Use `ocean.testing.scenarios.pilot_failure_report(...)` from a failing Pilot test to capture **`export_state()`**, recent feed lines, and a traceback for agents.
