from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def project_json_path(cwd: Path | None = None) -> Path:
    return (cwd or Path.cwd()).resolve() / "docs" / "project.json"


def load_project_dict(cwd: Path | None = None) -> dict[str, Any] | None:
    p = project_json_path(cwd)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_project_dict(data: dict[str, Any], cwd: Path | None = None) -> Path:
    root = (cwd or Path.cwd()).resolve()
    out = project_json_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def default_vision_and_identity(name: str, description: str, goals: list[str]) -> tuple[str, str]:
    desc_s = description.strip()
    vision = (
        os.getenv("OCEAN_DEFAULT_VISION", "").strip()
        or desc_s
        or (goals[0] if goals else "")
        or "Ship a focused, high-quality version of this product."
    )
    ai_identity = os.getenv("OCEAN_DEFAULT_AI_IDENTITY", "").strip() or (
        f"Your coding partner on **{name or 'this project'}** — "
        "Ocean runs the crew and timing; you steer goals and say when we are done."
    )
    return vision, ai_identity
