from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Tuple, Optional
import os

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
    """Execute the backlog in phases and return paths and runtime URL summary.

    Phases:
    1) Moroni (architecture)
    2) Q and Edna (implementation/UI) in parallel
    3) Mario (DevOps) last; may start local runtime
    """
    from concurrent.futures import ThreadPoolExecutor, wait

    docs_dir.mkdir(parents=True, exist_ok=True)

    agents = {agent.name: agent for agent in default_agents()}
    executed_tasks: list[Task] = []
    runtime_summary: Optional[str] = None

    # Partition tasks by owner
    moroni_tasks = [t for t in backlog if t.owner == "Moroni"]
    q_tasks = [t for t in backlog if t.owner == "Q"]
    edna_tasks = [t for t in backlog if t.owner == "Edna"]
    mario_tasks = [t for t in backlog if t.owner == "Mario"]

    # Helper: emit structured event to OCEAN_EVENTS_FILE
    def emit(kind: str, **data):
        path = os.getenv("OCEAN_EVENTS_FILE")
        if not path:
            return
        try:
            with open(path, "a", encoding="utf-8") as f:
                payload = {"event": kind, **data}
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass

    # Phase 1: Moroni
    if moroni_tasks:
        print(f"🤖 Executing {len(moroni_tasks)} tasks for Moroni...")
        emit("phase_start", agent="Moroni", count=len(moroni_tasks))
        for t in moroni_tasks:
            emit("task_start", agent="Moroni", title=t.title)
        executed_tasks.extend(agents["Moroni"].execute(moroni_tasks, spec))
        for t in moroni_tasks:
            emit("task_end", agent="Moroni", title=t.title)
        emit("phase_end", agent="Moroni")

    # Phase 2: Q and Edna in parallel
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = []
        if q_tasks:
            print(f"🤖 Executing {len(q_tasks)} tasks for Q...")
            emit("phase_start", agent="Q", count=len(q_tasks))
            for t in q_tasks:
                emit("task_start", agent="Q", title=t.title)
            futures.append(pool.submit(agents["Q"].execute, q_tasks, spec))
        if edna_tasks:
            print(f"🤖 Executing {len(edna_tasks)} tasks for Edna...")
            emit("phase_start", agent="Edna", count=len(edna_tasks))
            for t in edna_tasks:
                emit("task_start", agent="Edna", title=t.title)
            futures.append(pool.submit(agents["Edna"].execute, edna_tasks, spec))
        if futures:
            done, _ = wait(futures)
            for fut in done:
                executed_tasks.extend(fut.result())
            for t in q_tasks:
                emit("task_end", agent="Q", title=t.title)
            for t in edna_tasks:
                emit("task_end", agent="Edna", title=t.title)
            if q_tasks:
                emit("phase_end", agent="Q")
            if edna_tasks:
                emit("phase_end", agent="Edna")

    # Phase 3: Mario
    if mario_tasks:
        print(f"🤖 Executing {len(mario_tasks)} tasks for Mario...")
        emit("phase_start", agent="Mario", count=len(mario_tasks))
        for t in mario_tasks:
            emit("task_start", agent="Mario", title=t.title)
        executed_tasks.extend(agents["Mario"].execute(mario_tasks, spec))
        for t in mario_tasks:
            emit("task_end", agent="Mario", title=t.title)
        emit("phase_end", agent="Mario")
        runtime_summary = getattr(agents["Mario"], "last_runtime_summary", None)

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
