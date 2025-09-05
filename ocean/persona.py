from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
import os

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"agents": {}}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {"agents": {}}
    # Fallback minimal parser: try JSON first
    try:
        return json.loads(text)
    except Exception:
        return {"agents": {}}


def load_personas(path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Load personas from docs/personas.yaml (or JSON fallback).

    Returns a mapping of agent name -> persona dict. Missing file returns empty mapping.
    """
    p = path or Path("docs/personas.yaml")
    data = _read_yaml(p)
    agents = data.get("agents") or {}
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(agents, dict):
        for k, v in agents.items():
            if isinstance(v, dict):
                out[str(k)] = v
    return out


def voice_brief(agent: str, context: Optional[str] = None, max_chars: int = 400) -> str:
    """Create a short, non-quoting voice guide for an agent.

    - Avoids verbatim quotes; uses traits/diction/style/avoid/context_hooks.
    - Returns a single paragraph suitable to prepend to content instructions.
    """
    p = load_personas().get(agent, {})
    style_level = (os.getenv("OCEAN_STYLE") or "max").strip().lower()
    traits = ", ".join(p.get("traits", [])[:3])
    diction_list = p.get("diction", [])
    # prefer patterns/phrases, but avoid quoting; turn into guidance
    diction = ", ".join([d.replace("\"", "").strip() for d in diction_list[:2]]) if diction_list else ""
    avoid = ", ".join(p.get("avoid", [])[:2])
    style = ", ".join(p.get("style", [])[:2])
    hook = ""
    if context:
        hook = (p.get("context_hooks", {}) or {}).get(context, "")
    # Style toggle: 'max' uses full guidance; 'low' keeps it minimal/neutral
    parts = []
    if traits:
        parts.append(f"Voice traits: {traits}.")
    if diction and style_level == "max":
        parts.append(f"Diction guide (prefer, without quoting): {diction}.")
    if style and style_level == "max":
        parts.append(f"Style: {style}.")
    if avoid and style_level == "max":
        parts.append(f"Avoid: {avoid}.")
    if hook and style_level == "max":
        parts.append(f"Context: {hook}.")
    if style_level != "max":
        # Ensure at least a neutral tone hint
        parts = ["Use a concise, professional tone appropriate for the context."]
    brief = " ".join(x for x in parts if x).strip()
    if len(brief) > max_chars:
        brief = brief[: max_chars - 1] + "…"
    return brief
