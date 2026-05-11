import json
from pathlib import Path

from ocean.agents import default_agents
from ocean.models import ProjectSpec
from ocean.planner import generate_backlog, write_backlog


def test_generate_backlog_includes_each_crew_agent() -> None:
    spec = ProjectSpec(name="FullCrew", kind="web")
    backlog = generate_backlog(spec)
    owners = {t.owner for t in backlog}
    for agent in default_agents():
        assert agent.name in owners, f"backlog missing tasks for {agent.name}"


def test_generate_backlog_and_write(tmp_path: Path):
    spec = ProjectSpec(name="X", kind="web")
    backlog = generate_backlog(spec)
    assert backlog, "Backlog should not be empty"
    bj, pm = write_backlog(backlog, tmp_path)
    assert bj.exists() and pm.exists()
    data = json.loads(bj.read_text())
    assert isinstance(data, list) and data, "Backlog JSON contains tasks"


def test_execute_backlog_dry_plan_only(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("OCEAN_CODEGEN_BACKEND", "dry_plan_only")
    from ocean.planner import execute_backlog, generate_backlog

    spec = ProjectSpec(name="X", kind="web")
    backlog = generate_backlog(spec)
    bj, pm, runtime = execute_backlog(backlog, tmp_path, spec)
    assert runtime is None
    assert bj.exists() and pm.exists()

