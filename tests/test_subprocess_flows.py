"""End-to-end CLI tests via subprocess (no manual terminal).

Uses ``venv/bin/ocean`` when present (local dev); otherwise ``python -m ocean`` (CI).

Assertions focus on **on-disk outcomes** (backlog, plan, runtime state, inbox archive),
not only exit codes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

_REQUIRED_TASK_KEYS = frozenset({"title", "description", "owner", "files_touched"})
_EXPECTED_OWNERS = frozenset({"Moroni", "Q", "Edna", "Mario", "Tony"})


def ocean_argv() -> list[str]:
    vbin = REPO / "venv" / "bin" / "ocean"
    if sys.platform == "win32":
        vbin = REPO / "venv" / "Scripts" / "ocean.exe"
    if vbin.exists():
        return [str(vbin)]
    return [sys.executable, "-m", "ocean"]


def _blob(r: subprocess.CompletedProcess[str]) -> str:
    return (r.stdout or "") + (r.stderr or "")


def _dry_flow_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "OCEAN_DISABLE_WORKSPACE": "1",
            "OCEAN_DISABLE_CODEX": "1",
            "OCEAN_SIMPLE_FEED": "1",
            "OCEAN_SKIP_BACKEND_PROMPT": "1",
            "OCEAN_NO_SELF_UPDATE": "1",
            "OCEAN_SKIP_AUTO_SETUP": "1",
            "OCEAN_CODEGEN_BACKEND": "dry_plan_only",
        }
    )
    return env


def _assert_backlog_and_plan(docs: Path) -> list[dict]:
    backlog_path = docs / "backlog.json"
    plan_path = docs / "plan.md"
    assert backlog_path.is_file(), "cycle should write docs/backlog.json"
    assert plan_path.is_file(), "cycle should write docs/plan.md"
    raw = json.loads(backlog_path.read_text(encoding="utf-8"))
    assert isinstance(raw, list) and len(raw) >= 5, f"expected ≥5 tasks, got {len(raw)}"
    owners: set[str] = set()
    for i, row in enumerate(raw):
        assert isinstance(row, dict), f"task {i} is not an object"
        missing = _REQUIRED_TASK_KEYS - row.keys()
        assert not missing, f"task {i} missing keys {missing}"
        assert row.get("title"), f"task {i} empty title"
        assert row.get("owner") in _EXPECTED_OWNERS, f"unexpected owner {row.get('owner')!r}"
        assert isinstance(row.get("files_touched"), list)
        owners.add(str(row["owner"]))
    assert owners == _EXPECTED_OWNERS, f"expected all five agents represented, got {owners}"
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "# Initial Plan" in plan_text
    assert "## Backlog" in plan_text
    assert "[Moroni]" in plan_text
    return raw


@pytest.fixture
def mini_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    logs = tmp_path / "logs"
    logs.mkdir()
    spec = {
        "name": "SubprocessFlow",
        "kind": "web",
        "description": "integration",
        "goals": [],
        "constraints": [],
        "createdAt": "2026-01-01T00:00:00",
    }
    (docs / "project.json").write_text(json.dumps(spec), encoding="utf-8")
    return tmp_path


def test_subprocess_ocean_version_matches_package() -> None:
    """Packaging smoke: CLI reports the same version as the installed package."""
    import ocean as ocean_pkg

    r = subprocess.run(
        [*ocean_argv(), "--version"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, _blob(r)
    out = _blob(r).strip()
    assert ocean_pkg.__version__ in out


def test_ingest_status_cycle_writes_artifacts_and_state(mini_project: Path) -> None:
    env = _dry_flow_env()
    note = "automated flow note for archive"

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*ocean_argv(), *args],
            cwd=mini_project,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

    r1 = run(["ingest", note])
    assert r1.returncode == 0, _blob(r1)
    pending_dir = mini_project / ".ocean" / "inbox" / "pending"
    assert pending_dir.is_dir()
    assert list(pending_dir.glob("msg-*.json")), "ingest should create a pending JSON file"

    r2 = run(["status"])
    assert r2.returncode == 0, _blob(r2)
    assert "inbox_pending=1" in _blob(r2)

    r3 = run(["cycle"])
    assert r3.returncode == 0, _blob(r3)

    _assert_backlog_and_plan(mini_project / "docs")

    archived = list((mini_project / ".ocean" / "inbox" / "archive").glob("msg-*.json"))
    assert archived, "consumed inbox message should be under .ocean/inbox/archive"
    arc_data = json.loads(archived[-1].read_text(encoding="utf-8"))
    assert arc_data.get("consumed") is True
    assert arc_data.get("text") == note

    state_path = mini_project / ".ocean" / "product_state.json"
    assert state_path.is_file()
    st = json.loads(state_path.read_text(encoding="utf-8"))
    assert st.get("cycle_count") == 1
    assert st.get("last_cycle_at")
    assert st.get("tokens_used_last_cycle", 0) > 0
    log = st.get("decision_log") or []
    actors = {e.get("actor") for e in log if isinstance(e, dict)}
    assert "You" in actors
    assert "system" in actors
    notes = st.get("user_notes") or []
    assert any(note in n for n in notes)

    r4 = run(["status"])
    assert r4.returncode == 0, _blob(r4)
    assert "inbox_pending=0" in _blob(r4)
    assert "cycle_count=1" in _blob(r4)


def test_cycle_fails_without_project_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    env = _dry_flow_env()
    r = subprocess.run(
        [*ocean_argv(), "cycle"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 1
    assert "project.json" in _blob(r).lower() or "clarify" in _blob(r).lower()
    assert not (tmp_path / "docs" / "backlog.json").exists()
