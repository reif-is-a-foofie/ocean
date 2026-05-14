"""Onboarding flow in ``ocean.core`` (writes ``docs/project.json``)."""

from __future__ import annotations

import json
from pathlib import Path

from ocean.core.orchestrator import Orchestrator
from ocean.core.project_spec import project_json_path


def test_onboarding_writes_project_json(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    o = Orchestrator(cwd=root)
    assert o.onboarding_phase == "name"
    assert not o.project_configured
    o.handle_command("Alpha")
    o.handle_command("web")
    o.handle_command("A CLI helper")
    o.handle_command("ship, learn")
    o.handle_command("none")
    assert o.project_configured
    assert o.onboarding_phase is None
    p = project_json_path(root)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["name"] == "Alpha"
    assert data["kind"] == "web"
    assert data["goals"] == ["ship", "learn"]
    assert data["constraints"] == []


def test_onboarding_skip(tmp_path: Path) -> None:
    root = tmp_path / "ws2"
    root.mkdir()
    o = Orchestrator(cwd=root)
    o.handle_command("skip")
    assert o.onboarding_phase is None
    assert not project_json_path(root).exists()


def test_onboarding_skipped_when_project_json_exists(tmp_path: Path) -> None:
    root = tmp_path / "ws3"
    docs = root / "docs"
    docs.mkdir(parents=True)
    spec = {
        "name": "X",
        "kind": "cli",
        "description": "",
        "goals": [],
        "constraints": [],
        "createdAt": "2099-01-01",
    }
    (docs / "project.json").write_text(json.dumps(spec), encoding="utf-8")
    o = Orchestrator(cwd=root)
    assert o.onboarding_phase is None
    assert o.project_configured
    assert any("already configured" in e.text for e in o.events)
