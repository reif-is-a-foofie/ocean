"""Run a :mod:`ocean.testing.real_scenarios` onboarding flow inside **tmux** (real pseudo-TTY).

Usage (from repo root, venv active)::

    python -m ocean.testing.tmux_scenario_run tic_tac_toe_localhost

Exit code **0** when onboarding completes and ``docs/project.json`` matches expectations.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ocean.testing.real_scenarios import get_scenario


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ocean_bin(root: Path) -> Path:
    v = root / "venv" / "bin" / "ocean"
    if v.is_file() and os.access(v, os.X_OK):
        return v
    raise SystemExit(f"missing executable: {v} (create venv and pip install -e .)")


def _tmux_send(session: str, text: str) -> None:
    # tmux send-keys parses words; pass literal as one argument
    subprocess.run(
        ["tmux", "send-keys", "-t", session, text, "C-m"],
        check=True,
        timeout=30,
    )


def _tmux_capture(session: str, lines: int = 120) -> str:
    r = subprocess.run(
        ["tmux", "capture-pane", "-t", session, "-p", "-S", f"-{lines}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return r.stdout or ""


def run_scenario(scenario_id: str, *, root: Path | None = None) -> int:
    if not shutil.which("tmux"):
        print("tmux not found on PATH", file=sys.stderr)
        return 2

    root = root or _repo_root()
    scen = get_scenario(scenario_id)
    work = Path(tempfile.mkdtemp(prefix="ocean-tmux-"))
    session = f"ocean-scen-{os.getpid()}"

    ocean = _ocean_bin(root)
    try:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", session, "-c", str(work), str(ocean)],
            check=True,
            timeout=30,
        )
    except subprocess.CalledProcessError as e:
        print(f"tmux new-session failed: {e}", file=sys.stderr)
        return 3

    time.sleep(0.6)
    try:
        for line in scen.iter_all_commands():
            _tmux_send(session, line)
            time.sleep(0.35)
        time.sleep(0.8)
        pane = _tmux_capture(session)
        proj = work / "docs" / "project.json"
        if not proj.is_file():
            print("FAIL: docs/project.json missing", file=sys.stderr)
            print("--- pane tail ---\n", pane[-4000:], file=sys.stderr)
            return 4
        data = json.loads(proj.read_text(encoding="utf-8"))
        exp = scen.expect_spec_keys or {}
        for k, v in exp.items():
            if data.get(k) != v:
                print(f"FAIL: project.json {k}={data.get(k)!r} expected {v!r}", file=sys.stderr)
                return 5
        if "Onboarding complete" not in pane and "Saved project spec" not in pane:
            # file is authoritative; pane text may strip markup
            print("WARN: completion banner not found in capture (spec OK)", file=sys.stderr)
        print(f"OK scenario={scenario_id} workspace={work}")
        print(json.dumps({"project": data, "pane_preview": pane[-1200:]}, indent=2)[:8000])
        return 0
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) != 1:
        print("usage: python -m ocean.testing.tmux_scenario_run <scenario_id>", file=sys.stderr)
        from ocean.testing.real_scenarios import list_scenario_ids

        print("  ids:", ", ".join(list_scenario_ids()), file=sys.stderr)
        return 2
    return run_scenario(argv[0])


if __name__ == "__main__":
    raise SystemExit(main())
