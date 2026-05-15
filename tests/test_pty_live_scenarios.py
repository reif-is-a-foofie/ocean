"""Opt-in live PTY scenarios (real pseudo-TTY; no network)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from ocean import pty_harness

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "pty_chat_repl_crew.yaml"


def _live_pty_wanted() -> bool:
    if os.getenv("OCEAN_LIVE_HARNESS", "").strip() != "1":
        return False
    return sys.stdin.isatty() or os.getenv("OCEAN_FORCE_LIVE_PTY", "").strip() == "1"


@pytest.mark.skipif(sys.platform == "win32", reason="PTY harness targets POSIX")
def test_load_pty_scenario_yaml_expands_python() -> None:
    data = pty_harness.load_pty_scenario_yaml(FIXTURE)
    assert isinstance(data["command"], list)
    assert data["command"][0] == sys.executable


@pytest.mark.live_pty
@pytest.mark.skipif(sys.platform == "win32", reason="PTY harness targets POSIX")
@pytest.mark.skipif(not _live_pty_wanted(), reason="set OCEAN_LIVE_HARNESS=1 on a TTY (or OCEAN_FORCE_LIVE_PTY=1)")
def test_live_yaml_chat_repl_crew_skill_discovery() -> None:
    r = pty_harness.run_under_pty_scenario_file(
        FIXTURE,
        cwd=REPO_ROOT,
        env={**dict(**__import__("os").environ), "OCEAN_TEST": "1"},
        total_timeout_s=120.0,
    )
    plain = pty_harness.strip_ansi(r.output)
    assert "Skill discovery" in plain, pty_harness.tail_plain(r.output)
    assert not r.timed_out, pty_harness.tail_plain(r.output)
