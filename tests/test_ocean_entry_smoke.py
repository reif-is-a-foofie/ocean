"""Smoke-test the real ``ocean`` console entry (venv), not CliRunner — catches broken imports / mid-module ``app()``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
OCEAN_BIN = REPO_ROOT / "venv" / "bin" / "ocean"
if sys.platform == "win32":
    OCEAN_BIN = REPO_ROOT / "venv" / "Scripts" / "ocean.exe"


@pytest.mark.skipif(
    not OCEAN_BIN.exists(),
    reason="no venv setuptools script (pip install -e . from repo root)",
)
def test_bare_ocean_executable_runs_chat_smoke():
    env = os.environ.copy()
    env.update(
        {
            "OCEAN_DISABLE_WORKSPACE": "1",
            "OCEAN_DISABLE_CODEX": "1",
            "OCEAN_SIMPLE_FEED": "1",
            "OCEAN_SKIP_BACKEND_PROMPT": "1",
            "OCEAN_NO_SELF_UPDATE": "1",
            "OCEAN_TEST": "1",
            "OCEAN_ALLOW_QUESTIONS": "0",
        }
    )
    r = subprocess.run(
        [str(OCEAN_BIN)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    blob = r.stdout + r.stderr
    assert r.returncode == 0, blob[-6000:]
    assert "Session complete" in blob
    assert "Crew assembled" in blob
