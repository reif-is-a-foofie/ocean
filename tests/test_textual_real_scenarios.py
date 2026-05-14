"""Pilot tests driven by ``ocean.testing.real_scenarios`` (product-shaped flows)."""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from textual.widgets import Input

from ocean.testing.real_scenarios import SCENARIOS
from ocean.ui.app import OceanTextualApp

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("scenario_id", sorted(SCENARIOS.keys()))
def test_pilot_scenario_onboarding_and_tasks(scenario_id: str, tmp_path, monkeypatch) -> None:
    scen = SCENARIOS[scenario_id]
    monkeypatch.chdir(tmp_path)

    async def run() -> None:
        app = OceanTextualApp(cwd=tmp_path)
        async with app.run_test(size=(110, 36)) as pilot:
            for line in scen.iter_all_commands():
                inp = pilot.app.query_one("#command-input", Input)
                inp.focus()
                inp.value = line
                await pilot.press("enter")
            st = pilot.app.export_state()
            assert st["project_configured"] is True
            assert st["onboarding_phase"] is None
            assert len(st["pending_tasks"]) == len(scen.post_save_commands)
            data = json.loads((tmp_path / "docs" / "project.json").read_text(encoding="utf-8"))
            for k, v in (scen.expect_spec_keys or {}).items():
                assert data.get(k) == v, (k, data.get(k), v)

    asyncio.run(run())


@pytest.mark.skipif(not shutil.which("tmux"), reason="tmux not on PATH")
def test_tmux_scenario_smoke_tic_tac_toe() -> None:
    """End-to-end tmux + real TTY: slower; validates the same story outside Pilot."""
    r = subprocess.run(
        [sys.executable, "-m", "ocean.testing.tmux_scenario_run", "tic_tac_toe_localhost"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stdout + "\n" + r.stderr
