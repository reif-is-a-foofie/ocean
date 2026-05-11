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
