from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ocean.models import ProjectSpec
from ocean.planner import execute_backlog, generate_backlog

from .inbox import drain_pending_to_archive
from .paths import runtime_root
from .state import ProductState


def _token_estimate_per_task() -> int:
    try:
        return max(100, int(os.getenv("OCEAN_TOKEN_ESTIMATE_PER_TASK", "4000")))
    except Exception:
        return 4000


def _estimate_cycle_tokens(task_count: int) -> int:
    return task_count * _token_estimate_per_task()


@dataclass
class CycleResult:
    ok: bool
    cycle: int
    message: str
    backlog_json: Path | None = None
    skipped_execution: bool = False


def _load_spec(docs: Path) -> ProjectSpec | None:
    path = docs / "project.json"
    if not path.exists():
        return None
    try:
        return ProjectSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def _sync_vision_from_spec(state: ProductState, spec: ProjectSpec) -> None:
    if not state.vision_summary.strip():
        bits = [spec.description.strip()] if spec.description else []
        bits.extend(spec.goals[:3])
        state.vision_summary = " ".join(b for b in bits if b)[:2000] or spec.name


def run_cycle(
    *,
    root: Path | None = None,
    docs_dir: Path | None = None,
    max_tokens: int | None = None,
) -> CycleResult:
    """One autonomous cycle: drain inbox → refresh state → generate/execute backlog.

    Token budget is a soft cap using a coarse per-task estimate (see OCEAN_TOKEN_ESTIMATE_PER_TASK).
    """
    from ocean.feed import feed

    cwd = root or Path.cwd()
    docs = docs_dir or (cwd / "docs")
    rd = runtime_root(cwd)
    state = ProductState.load(rd)
    if state.tokens_budget_per_cycle is not None and max_tokens is None:
        max_tokens = state.tokens_budget_per_cycle
    if max_tokens is None:
        raw = os.getenv("OCEAN_BUDGET_TOKENS_PER_CYCLE", "").strip()
        if raw.isdigit():
            max_tokens = int(raw)

    # Drain human input
    drained = drain_pending_to_archive(cwd)
    for msg in drained:
        text = str(msg.get("text", ""))
        atts = msg.get("attachments") or []
        tail = f" [attachments: {', '.join(atts)}]" if atts else ""
        line = f"[inbox] {text}{tail}"
        state.user_notes.append(line[:4000])
        state.log_decision("You", text, attachments=atts)

    spec = _load_spec(docs)
    if spec is None:
        state.save(rd)
        return CycleResult(
            ok=False,
            cycle=state.cycle_count,
            message="No docs/project.json — run `ocean clarify` or add a project spec.",
        )

    _sync_vision_from_spec(state, spec)

    backlog = generate_backlog(spec)
    n_tasks = len(backlog)
    est = _estimate_cycle_tokens(n_tasks)

    if max_tokens is not None and est > max_tokens:
        state.cycle_count += 1
        state.last_cycle_at = datetime.now().isoformat()
        state.tokens_used_last_cycle = 0
        state.log_decision(
            "system",
            f"Skipped execution: estimated {est} tokens > budget {max_tokens} (tasks={n_tasks}).",
        )
        state.save(rd)
        feed(
            f"🌊 Ocean: cycle {state.cycle_count}: skipped execution (est_tokens={est}, max={max_tokens})."
        )
        return CycleResult(
            ok=True,
            cycle=state.cycle_count,
            message="budget_skip",
            skipped_execution=True,
        )

    state.cycle_count += 1
    state.last_cycle_at = datetime.now().isoformat()
    feed(f"🌊 Ocean: cycle {state.cycle_count}: planning {n_tasks} task(s)…")

    bj, _pm, _runtime = execute_backlog(backlog, docs, spec)
    state.tokens_used_last_cycle = est
    state.log_decision("system", f"Executed backlog ({n_tasks} tasks), est_tokens={est}.")
    state.save(rd)

    feed(f"🌊 Ocean: cycle {state.cycle_count} complete — backlog at {bj}")
    return CycleResult(
        ok=True,
        cycle=state.cycle_count,
        message="ok",
        backlog_json=bj,
        skipped_execution=False,
    )
