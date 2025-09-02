from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Tuple, Optional

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


def execute_backlog(backlog: Iterable[Task], docs_dir: Path, spec: ProjectSpec) -> tuple[Path, Path, Optional[str]]:
    """Execute the backlog using agent execution capabilities.

    Returns (backlog_json_path, plan_md_path, runtime_summary_if_any).
    """
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Group tasks by agent
    agent_tasks = {}
    for task in backlog:
        if task.owner not in agent_tasks:
            agent_tasks[task.owner] = []
        agent_tasks[task.owner].append(task)
    
    # Execute tasks using each agent's execute method
    agents = {agent.name: agent for agent in default_agents()}
    executed_tasks = []
    runtime_summary: Optional[str] = None
    
    for agent_name, tasks in agent_tasks.items():
        if agent_name in agents:
            print(f"🤖 Executing {len(tasks)} tasks for {agent_name}...")
            executed = agents[agent_name].execute(tasks, spec)
            executed_tasks.extend(executed)
            if agent_name == "Mario":
                # best-effort fetch of runtime summary
                summary = getattr(agents[agent_name], "last_runtime_summary", None)
                if summary:
                    runtime_summary = summary
        else:
            print(f"⚠️ Agent {agent_name} not found, skipping tasks")
    
    # Write documentation
    bj, pm = write_backlog(executed_tasks, docs_dir)
    return bj, pm, runtime_summary


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
