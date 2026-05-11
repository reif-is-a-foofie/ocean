from __future__ import annotations

from pathlib import Path

from .inbox import list_pending
from .paths import runtime_root
from .state import ProductState


def format_status_text(cwd: Path | None = None) -> str:
    rd = runtime_root(cwd)
    st = ProductState.load(rd)
    pending = list_pending(cwd)
    lines = [
        f"cycle_count={st.cycle_count}",
        f"last_cycle_at={st.last_cycle_at or '(never)'}",
        f"inbox_pending={len(pending)}",
        f"tokens_last_cycle={st.tokens_used_last_cycle}",
        f"budget_per_cycle={st.tokens_budget_per_cycle or '(unset)'}",
        f"decision_log_entries={len(st.decision_log)}",
        f"user_notes={len(st.user_notes)}",
    ]
    if st.vision_summary:
        lines.append(f"vision_summary={st.vision_summary[:120]!r}…" if len(st.vision_summary) > 120 else f"vision_summary={st.vision_summary!r}")
    return "\n".join(lines)
