"""Gemini key resolution for setup / early-brain: user key first, then release-embedded key."""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

Source = Literal["user", "embedded", "none"]


def user_gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


def embedded_gemini_key() -> str:
    if os.getenv("OCEAN_DISABLE_EMBEDDED_GEMINI", "").strip().lower() in ("1", "true", "yes", "on"):
        return ""
    try:
        from ocean import _release_embedded as _emb

        raw = getattr(_emb, "EMBEDDED_GEMINI_SETUP_KEY", "")
        return raw.strip() if isinstance(raw, str) else ""
    except Exception:
        return ""


def _usage_path() -> Path:
    d = Path.home() / ".ocean"
    d.mkdir(parents=True, exist_ok=True)
    return d / "embedded_gemini_daily.json"


def _daily_cap() -> int:
    try:
        return max(0, int(os.getenv("OCEAN_EMBEDDED_GEMINI_DAILY_CAP", "48")))
    except ValueError:
        return 48


def embedded_quota_allows() -> bool:
    cap = _daily_cap()
    if cap <= 0:
        return False
    today = date.today().isoformat()
    p = _usage_path()
    if not p.exists():
        return True
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return True
        if data.get("day") != today:
            return True
        n = int(data.get("count", 0))
        return n < cap
    except Exception:
        return True


def record_embedded_gemini_use() -> None:
    today = date.today().isoformat()
    p = _usage_path()
    count = 1
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("day") == today:
                count = int(data.get("count", 0)) + 1
    except Exception:
        pass
    payload = {"day": today, "count": count, "updated": datetime.now(timezone.utc).isoformat()}
    try:
        p.write_text(json.dumps(payload, indent=0) + "\n", encoding="utf-8")
    except Exception:
        pass


def resolve_gemini_key_for_early_brain() -> tuple[str | None, Source]:
    """Prefer user env keys; else non-empty embedded key if quota allows."""
    u = user_gemini_key()
    if u:
        return u, "user"
    e = embedded_gemini_key()
    if not e:
        return None, "none"
    if not embedded_quota_allows():
        return None, "none"
    return e, "embedded"
