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
    skills = p.get("skills", [])
    skills_s = ", ".join(str(s) for s in skills[:8]) if isinstance(skills, list) else ""
    background = (p.get("background") or "").strip() if isinstance(p.get("background"), str) else ""
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
    if skills_s and style_level == "max":
        parts.append(f"Apply expertise: {skills_s}.")
    if background and style_level == "max":
        if len(background) > 280:
            background = background[:279] + "…"
        parts.append(f"Background: {background}")
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


_CREW_FEED_ORDER: tuple[str, ...] = ("Moroni", "Q", "Edna", "Mario", "Tony")


def agent_voice_skills_chat_lines(agent: str, *, max_skill_items: int = 12, style_level: str | None = None) -> list[str]:
    """Terminal-chat lines derived from personas.yaml (voice + skills)."""
    lvl = (style_level or (os.getenv("OCEAN_STYLE") or "max")).strip().lower()
    p = load_personas().get(agent, {})
    lines: list[str] = []
    cal = p.get("calibration")
    if isinstance(cal, dict) and cal.get("do"):
        lines.append(str(cal["do"]))
    traits = p.get("traits")
    if lvl == "max" and isinstance(traits, list) and traits:
        lines.append("; ".join(str(t) for t in traits[:2]))
    skills = p.get("skills")
    if isinstance(skills, list) and skills:
        cap = min(max_skill_items, len(skills))
        snippet = " · ".join(str(s) for s in skills[:cap])
        if len(skills) > cap:
            snippet += " …"
        lines.append(f"Skills — {snippet}")
    if not lines:
        lines.append("(No persona in docs/personas.yaml for this agent yet.)")
    return lines


def crew_cards_plain_text(order: tuple[str, ...] | None = None) -> str:
    """Multi-line plaintext card for Chat REPL / quick reference."""
    from .personas import AGENT_EMOJI

    names = order or _CREW_FEED_ORDER
    segments: list[str] = []
    for agent in names:
        ic = AGENT_EMOJI.get(agent, "🤖")
        segments.append(f"{ic} {agent}")
        for part in agent_voice_skills_chat_lines(agent):
            segments.append(f"  · {part}")
        segments.append("")
    return "\n".join(segments).rstrip()
