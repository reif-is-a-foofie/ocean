"""Fast PTY harness smoke tests (real pseudo-TTY; no network)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ocean import pty_harness

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(sys.platform == "win32", reason="PTY harness targets POSIX")
def test_pty_ocean_version() -> None:
    """PTY + ``ocean --version`` should print version."""
    py = sys.executable
    r = pty_harness.run_under_pty(
        [py, "-m", "ocean", "--version"],
        cwd=REPO_ROOT,
        env={**dict(**__import__("os").environ), "OCEAN_TEST": "1"},
        timeout_s=15.0,
    )
    plain = pty_harness.strip_ansi(r.output)
    assert "ocean" in plain.lower()


def test_pty_harness_strip_ansi() -> None:
    raw = "\x1b[31mocean\x1b[0m"
    assert pty_harness.strip_ansi(raw) == "ocean"


def test_tail_plain_truncates() -> None:
    blob = "\n".join(f"line-{i}" for i in range(100))
    t = pty_harness.tail_plain(blob, lines=5)
    assert "line-99" in t
    assert "line-0" not in t


def test_run_under_pty_scenario_rejects_empty_steps() -> None:
    with pytest.raises(pty_harness.PtyScenarioError):
        pty_harness.run_under_pty_scenario({"command": [sys.executable, "-c", "pass"], "steps": []}, cwd=REPO_ROOT)
@pytest.mark.skipif(sys.platform == "win32", reason="PTY harness targets POSIX")
def test_pty_chat_repl_crew_smoke() -> None:
    """Scripted PTY: chat-repl receives ``crew`` and prints persona skills (TTY path)."""
    py = sys.executable
    r = pty_harness.run_under_pty_scripted(
        [py, "-m", "ocean", "chat-repl"],
        [
            (r"(?i)ocean\s*>", "crew"),
            (r"Skills", "exit"),
        ],
        cwd=REPO_ROOT,
        env={
            **dict(**__import__("os").environ),
            "OCEAN_TEST": "1",
            "TERM": "dumb",
            "COLUMNS": "120",
            "LINES": "40",
        },
        total_timeout_s=60.0,
    )
    plain = pty_harness.strip_ansi(r.output)
    assert "Skills" in plain
    assert not r.timed_out, plain[-2000:]
