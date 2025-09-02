from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .agents import default_agents
from .models import ProjectSpec, Task


def generate_backlog(spec: ProjectSpec) -> list[Task]:
    tasks: list[Task] = []
    for agent in default_agents():
        tasks.extend(agent.propose_tasks(spec))
    # Deduplicate by (title, owner)
    seen: set[tuple[str, str]] = set()
    uniq: list[Task] = []
    for t in tasks:
        key = (t.title, t.owner)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(t)
    return uniq


def write_backlog(backlog: Iterable[Task], docs_dir: Path) -> tuple[Path, Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    backlog_json = docs_dir / "backlog.json"
    plan_md = docs_dir / "plan.md"
    data = [
        {
            "title": t.title,
            "description": t.description,
            "owner": t.owner,
            "files_touched": t.files_touched,
        }
        for t in backlog
    ]
    backlog_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    lines = ["# Initial Plan", "", "## Backlog", ""]
    for t in data:
        files = ", ".join(t["files_touched"]) if t["files_touched"] else "(tbd)"
        lines.append(f"- [{t['owner']}] {t['title']} — {files}")
    plan_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return backlog_json, plan_md

