import json
from pathlib import Path

from ocean.runtime import format_status_text, ingest_message, run_cycle
from ocean.runtime.inbox import list_pending


def test_ingest_and_pending(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ingest_message("hello", [])
    pending = list_pending()
    assert len(pending) == 1
    assert pending[0]["text"] == "hello"


def test_cycle_dry_plan_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OCEAN_CODEGEN_BACKEND", "dry_plan_only")
    (tmp_path / "docs").mkdir()
    spec = {
        "name": "T",
        "kind": "web",
        "description": "test",
        "goals": [],
        "constraints": [],
        "createdAt": "2026-01-01",
    }
    (tmp_path / "docs" / "project.json").write_text(json.dumps(spec), encoding="utf-8")
    ingest_message("note", [])
    res = run_cycle()
    assert res.ok
    assert not res.skipped_execution
    assert res.backlog_json and res.backlog_json.exists()
    assert not list_pending()
    data = json.loads(res.backlog_json.read_text(encoding="utf-8"))
    assert len(data) >= 5
    plan = (tmp_path / "docs" / "plan.md").read_text(encoding="utf-8")
    assert "Backlog" in plan
    st_path = tmp_path / ".ocean" / "product_state.json"
    assert st_path.is_file()
    st = json.loads(st_path.read_text(encoding="utf-8"))
    assert st["cycle_count"] == 1


def test_cycle_budget_skip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OCEAN_CODEGEN_BACKEND", "dry_plan_only")
    (tmp_path / "docs").mkdir()
    spec = {
        "name": "T",
        "kind": "web",
        "description": "test",
        "goals": [],
        "constraints": [],
        "createdAt": "2026-01-01",
    }
    (tmp_path / "docs" / "project.json").write_text(json.dumps(spec), encoding="utf-8")
    res = run_cycle(max_tokens=1)
    assert res.ok
    assert res.skipped_execution
    assert res.backlog_json is None
    st_path = tmp_path / ".ocean" / "product_state.json"
    st = json.loads(st_path.read_text(encoding="utf-8"))
    assert st["cycle_count"] == 1
    assert st["tokens_used_last_cycle"] == 0
    assert not (tmp_path / "docs" / "backlog.json").exists()


def test_cycle_requires_project_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    res = run_cycle()
    assert not res.ok


def test_status_text(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    s = format_status_text()
    assert "cycle_count=0" in s
