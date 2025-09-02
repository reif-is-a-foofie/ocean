import json
from pathlib import Path

from ocean.models import ProjectSpec
from ocean.planner import generate_backlog, write_backlog


def test_generate_backlog_and_write(tmp_path: Path):
    spec = ProjectSpec(name="X", kind="web")
    backlog = generate_backlog(spec)
    assert backlog, "Backlog should not be empty"
    bj, pm = write_backlog(backlog, tmp_path)
    assert bj.exists() and pm.exists()
    data = json.loads(bj.read_text())
    assert isinstance(data, list) and data, "Backlog JSON contains tasks"

