from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import inbox_archive, inbox_pending, runtime_root


def _now_iso() -> str:
    return datetime.now().isoformat()


def ingest(
    message: str,
    attachments: list[Path] | None = None,
    *,
    cwd: Path | None = None,
) -> Path:
    """Write one inbox message to `.ocean/inbox/pending`. Returns path to message file."""
    rd = runtime_root(cwd)
    pending = inbox_pending(rd)
    mid = str(uuid.uuid4())
    paths = [str(p.resolve()) for p in (attachments or []) if p]
    payload: dict[str, Any] = {
        "id": mid,
        "ts": _now_iso(),
        "text": message.strip(),
        "attachments": paths,
        "consumed": False,
    }
    out = pending / f"msg-{mid}.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out


def list_pending(cwd: Path | None = None) -> list[dict[str, Any]]:
    rd = runtime_root(cwd)
    pending = inbox_pending(rd)
    rows: list[dict[str, Any]] = []
    for p in sorted(pending.glob("msg-*.json")):
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return rows


def drain_pending_to_archive(
    cwd: Path | None = None,
) -> list[dict[str, Any]]:
    """Move all pending messages to archive; return payloads (for merging into state)."""
    rd = runtime_root(cwd)
    pending = inbox_pending(rd)
    arch = inbox_archive(rd)
    moved: list[dict[str, Any]] = []
    for p in sorted(pending.glob("msg-*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        data["consumed"] = True
        data["consumed_at"] = _now_iso()
        dest = arch / p.name
        dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        try:
            p.unlink()
        except Exception:
            pass
        moved.append(data)
    return moved
