"""Append structured JSON lines to ``OCEAN_EVENTS_FILE`` for external TUIs (e.g. Toad fork)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def emit_event(event: str, **data: object) -> None:
    path = os.getenv("OCEAN_EVENTS_FILE")
    if not path:
        return
    payload = {"event": event, "ts": datetime.now(timezone.utc).isoformat(), **data}
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def emit_setup(kind: str, **data: object) -> None:
    """Setup/onboarding envelope for hosts tailing ``logs/events-*.jsonl``.

    kinds: phase_start | phase_end | question | answer | info
    Typical fields: id, message, choices (list[str]), codegen_backend (str, non-secret).
    Never include API keys or tokens.
    """
    emit_event("setup", kind=kind, phase="setup", **data)
