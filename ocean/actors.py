from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Actor:
    id: str
    name: str
    role: str
    mission: str
    phase: str
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    active: bool = True


TEAM_STANDARDS: list[dict[str, str]] = [
    {"id": "value", "name": "Value", "standard": "The work has a clear user benefit and feedback becomes the next decision."},
    {"id": "experience", "name": "Experience", "standard": "The user path is understandable and usable."},
    {"id": "build", "name": "Build", "standard": "The implementation is scoped, integrated, and maintainable."},
    {"id": "ship", "name": "Ship", "standard": "The work is verified, runnable, and ready to hand off."},
    {"id": "money", "name": "Money", "standard": "Adoption, monetization, and capability proof are considered."},
]


DEFAULT_ACTORS: list[Actor] = [
    Actor(
        id="captain",
        name="Captain",
        role="Orchestrator",
        mission="Turns the conversation into the smallest valuable next move, then hands Cursor a discrete job.",
        phase="value",
        skills=["product judgment", "scope control", "job writing", "feedback routing"],
        tools=["chat", "filesystem", "ocean_turn"],
    ),
    Actor(
        id="edna",
        name="Edna",
        role="UX and Product Feel",
        mission="Keeps setup, screens, copy, and workflows understandable to the intended user.",
        phase="experience",
        skills=["UX writing", "onboarding", "screenshots", "interface critique"],
        tools=["chat", "screenshots", "filesystem"],
    ),
    Actor(
        id="q",
        name="Q",
        role="Builder",
        mission="Translates the selected job into pragmatic code and file changes using the existing repo style.",
        phase="build",
        skills=["implementation", "integration", "tests", "tooling"],
        tools=["Cursor", "Codex", "filesystem"],
    ),
    Actor(
        id="mario",
        name="Mario",
        role="Ship and Verify",
        mission="Makes sure the work runs, can be tested, and has a clean handoff path.",
        phase="ship",
        skills=["runtime", "verification", "CI", "deployment", "release notes"],
        tools=["shell", "pytest", "browser", "logs"],
    ),
    Actor(
        id="scrooge",
        name="Scrooge",
        role="Impact and Money",
        mission="Challenges the team with: what benefit does this create, who adopts it, and how could it make money?",
        phase="money",
        skills=["monetization", "distribution", "open-source strategy", "ROI", "demo power"],
        tools=["positioning", "roadmap", "chat"],
    ),
]


def actor_store_path(project_root: str | Path | None = None) -> Path:
    root = Path(project_root or ".").expanduser().resolve()
    return root / ".ocean" / "actors.json"


def load_actors(project_root: str | Path | None = None) -> list[dict[str, Any]]:
    path = actor_store_path(project_root)
    default = [asdict(actor) for actor in DEFAULT_ACTORS]
    if not path.exists():
        return save_actors(default, project_root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = default
    if not isinstance(data, list):
        data = default

    # Keep the product intentionally small: five known actors max. Preserve any
    # user tuning for those actors, ignore older expanded-crew entries.
    by_id = {actor.get("id"): actor for actor in data if isinstance(actor, dict)}
    merged: list[dict[str, Any]] = []
    for base in default:
        existing = by_id.get(base["id"], {})
        merged.append(
            _normalize_actor(
                {
                    **base,
                    "skills": _merge_unique(base["skills"], existing.get("skills")),
                    "tools": _merge_unique(base["tools"], existing.get("tools")),
                    "active": existing.get("active", base["active"]),
                    "id": base["id"],
                }
            )
        )
    return save_actors(merged[:5], project_root)


def save_actors(actors: list[dict[str, Any]], project_root: str | Path | None = None) -> list[dict[str, Any]]:
    path = actor_store_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [_normalize_actor(actor) for actor in actors[:5]]
    path.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
    return normalized


def update_actor(actor_id: str, patch: dict[str, Any], project_root: str | Path | None = None) -> dict[str, Any]:
    actors = load_actors(project_root)
    for actor in actors:
        if actor["id"] == actor_id:
            actor.update({key: value for key, value in patch.items() if key in actor})
            actor["skills"] = _string_list(actor.get("skills"))
            actor["tools"] = _string_list(actor.get("tools"))
            actor["active"] = bool(actor.get("active", True))
            save_actors(actors, project_root)
            return actor
    raise ValueError("Ocean keeps five actors max; tune an existing actor instead of adding another one.")


def add_actor_skill(actor_id: str, skill: str, project_root: str | Path | None = None) -> dict[str, Any]:
    skill = skill.strip()
    if not skill:
        raise ValueError("skill is required")
    actor = next((item for item in load_actors(project_root) if item["id"] == actor_id), None)
    if not actor:
        raise ValueError(f"unknown actor: {actor_id}")
    skills = actor["skills"]
    if skill not in skills:
        skills.append(skill)
    return update_actor(actor_id, {"skills": skills}, project_root)


def coverage_report(project_root: str | Path | None = None) -> dict[str, Any]:
    actors = [actor for actor in load_actors(project_root) if actor.get("active", True)]
    by_phase: dict[str, list[dict[str, Any]]] = {standard["id"]: [] for standard in TEAM_STANDARDS}
    for actor in actors:
        by_phase.setdefault(actor.get("phase") or "build", []).append(actor)
    standards = []
    for standard in TEAM_STANDARDS:
        assigned = by_phase.get(standard["id"], [])
        standards.append(
            {
                **standard,
                "covered": bool(assigned),
                "actors": [{"id": actor["id"], "name": actor["name"], "role": actor["role"]} for actor in assigned],
            }
        )
    return {
        "standards": standards,
        "phases": standards,
        "gaps": [standard for standard in standards if not standard["covered"]],
        "active_actor_count": len(actors),
        "max_actor_count": 5,
    }


def _normalize_actor(actor: dict[str, Any]) -> dict[str, Any]:
    actor_id = str(actor.get("id") or actor.get("name") or "actor").strip().lower().replace(" ", "-")
    return {
        "id": actor_id,
        "name": str(actor.get("name") or actor_id.replace("-", " ").title()).strip(),
        "role": str(actor.get("role") or "Agent").strip(),
        "mission": str(actor.get("mission") or "").strip(),
        "phase": str(actor.get("phase") or "build").strip(),
        "skills": _string_list(actor.get("skills")),
        "tools": _string_list(actor.get("tools")),
        "active": bool(actor.get("active", True)),
    }


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _merge_unique(base: list[str], extra: Any) -> list[str]:
    merged: list[str] = []
    for item in [*base, *_string_list(extra)]:
        if item not in merged:
            merged.append(item)
    return merged
