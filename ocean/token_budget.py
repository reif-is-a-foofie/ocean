"""Soft hourly token budget — Ocean tracks usage; warns in-feed (orchestration, not user math)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from .backends import load_prefs

_LEDGER = "token_ledger.json"
_WINDOW_S = 3600


def _ledger_path(cwd: Path | None = None) -> Path:
    root = cwd or Path.cwd()
    d = root / ".ocean"
    d.mkdir(parents=True, exist_ok=True)
    return d / _LEDGER


def budget_cap(cwd: Path | None = None) -> int | None:
    """Max tokens per rolling hour, or None if unset (no limit)."""
    raw = os.getenv("OCEAN_TOKEN_BUDGET_PER_HOUR", "").strip()
    if not raw:
        p = load_prefs(cwd).get("token_budget_per_hour")
        if p is None:
            return None
        raw = str(p).strip()
    try:
        v = int(raw)
        return v if v > 0 else None
    except ValueError:
        return None


def _load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"events": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"events": []}


def _save_ledger(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def usage_recent(path: Path | None = None, *, window_s: int = _WINDOW_S) -> int:
    """Sum of recorded tokens in the last ``window_s`` seconds."""
    p = path or _ledger_path()
    now = time.time()
    data = _load_ledger(p)
    events = data.get("events") or []
    if not isinstance(events, list):
        return 0
    total = 0
    kept: list[dict[str, Any]] = []
    for e in events:
        if not isinstance(e, dict):
            continue
        try:
            t = float(e.get("t", 0))
            n = int(e.get("n", 0))
        except (TypeError, ValueError):
            continue
        if now - t <= window_s:
            total += max(0, n)
            kept.append({"t": t, "n": n})
    if len(kept) != len(events):
        data["events"] = kept
        try:
            _save_ledger(p, data)
        except OSError:
            pass
    return total


def note_usage(tokens: int, cwd: Path | None = None) -> None:
    """Append a token estimate (call from codegen / LLM wrappers when available)."""
    if tokens <= 0:
        return
    p = _ledger_path(cwd)
    data = _load_ledger(p)
    ev = data.setdefault("events", [])
    if not isinstance(ev, list):
        ev = []
        data["events"] = ev
    ev.append({"t": time.time(), "n": int(tokens)})
    # cap list size
    if len(ev) > 2000:
        data["events"] = ev[-2000:]
    try:
        _save_ledger(p, data)
    except OSError:
        pass


def feed_status_if_needed(
    feed: Callable[[str], None],
    cwd: Path | None = None,
) -> None:
    """One line: budget state when configured (user never has to calculate)."""
    cap = budget_cap(cwd)
    if cap is None:
        return
    used = usage_recent(_ledger_path(cwd))
    pct = min(100, int(100 * used / cap)) if cap else 0
    if used >= cap:
        feed(
            f"🌊 Ocean: Token budget (rolling hour): ~{used:,} / {cap:,} — **at or over cap**. "
            "I'll pace codegen; you can raise OCEAN_TOKEN_BUDGET_PER_HOUR or docs/ocean_prefs.json."
        )
    elif used >= int(cap * 0.85):
        feed(
            f"🌊 Ocean: Token budget (rolling hour): ~{used:,} / {cap:,} ({pct}%) — approaching limit; pacing work."
        )
    else:
        feed(f"🌊 Ocean: Token budget (rolling hour): ~{used:,} / {cap:,} ({pct}%) — Ocean is tracking; you just drive goals.")
