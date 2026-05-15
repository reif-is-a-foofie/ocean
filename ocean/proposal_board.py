"""Local proposal board: per-persona files under ``docs/proposals/`` with a machine index."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_WRITERS = frozenset({"Moroni", "Q", "Edna", "Mario", "Tony"})


def proposals_root(project_root: Path | str) -> Path:
    return Path(project_root).resolve() / "docs" / "proposals"


def current_round_dir(project_root: Path | str) -> Path:
    return proposals_root(project_root) / "current"


def board_path(project_root: Path | str) -> Path:
    return proposals_root(project_root) / "board.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def publish_proposal(project_root: Path | str, persona: str, payload: dict[str, Any]) -> Path:
    """Write ``docs/proposals/current/<Persona>.json`` and refresh ``board.json`` index."""
    if persona not in ALLOWED_WRITERS:
        raise ValueError(f"persona {persona!r} cannot publish; allowed={sorted(ALLOWED_WRITERS)}")
    root = Path(project_root).resolve()
    cur = current_round_dir(root)
    cur.mkdir(parents=True, exist_ok=True)
    out = cur / f"{persona}.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    _touch_board_index(root, persona, out)
    return out


def _touch_board_index(root: Path, persona: str, proposal_path: Path) -> None:
    bp = board_path(root)
    proposals_root(root).mkdir(parents=True, exist_ok=True)
    data = _read_json(bp)
    if not data.get("round"):
        data["round"] = datetime.now(timezone.utc).date().isoformat()
    data.setdefault("status", "open")
    props = data.get("proposals")
    if not isinstance(props, dict):
        props = {}
    rel = proposal_path.relative_to(proposals_root(root))
    props[persona] = {
        "path": str(rel).replace("\\", "/"),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    data["proposals"] = props
    _write_json(bp, data)


def read_peer(project_root: Path | str, reader: str, peer: str) -> dict[str, Any] | None:
    """Global read: any crew name may load another persona's published JSON."""
    _ = reader
    path = current_round_dir(project_root) / f"{peer}.json"
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def revise_own(project_root: Path | str, persona: str, payload: dict[str, Any]) -> Path:
    """Merge ``payload`` into this persona's file (local write only)."""
    if persona not in ALLOWED_WRITERS:
        raise ValueError(f"persona {persona!r} cannot revise; allowed={sorted(ALLOWED_WRITERS)}")
    cur = current_round_dir(project_root)
    existing: dict[str, Any] = {}
    p = cur / f"{persona}.json"
    if p.exists():
        prev = read_peer(project_root, persona, persona)
        if isinstance(prev, dict):
            existing = dict(prev)
    merged = {**existing, **payload}
    return publish_proposal(project_root, persona, merged)


def list_board(project_root: Path | str) -> dict[str, Any]:
    """Return parsed ``board.json`` plus whether each indexed file still exists."""
    root = Path(project_root).resolve()
    data = dict(_read_json(board_path(root)))
    props = data.get("proposals")
    out_props: dict[str, Any] = {}
    if isinstance(props, dict):
        base = proposals_root(root)
        for name, meta in props.items():
            if not isinstance(meta, dict):
                continue
            rel = meta.get("path")
            exists = False
            if isinstance(rel, str):
                exists = (base / rel).is_file()
            out_props[str(name)] = {**meta, "exists": exists}
    data["proposals"] = out_props
    return data


def finalize_round(project_root: Path | str, label: str | None = None) -> Path:
    """Copy ``current/*.json`` into ``archive/<label>/`` and mark the board archived."""
    root = Path(project_root).resolve()
    cur = current_round_dir(root)
    cur.mkdir(parents=True, exist_ok=True)
    tag = label or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = proposals_root(root) / "archive" / tag
    dest.mkdir(parents=True, exist_ok=True)
    for p in sorted(cur.glob("*.json")):
        shutil.copy2(p, dest / p.name)
    bp = board_path(root)
    data = _read_json(bp)
    data["status"] = "archived"
    data["archived_as"] = tag
    _write_json(bp, data)
    return dest
