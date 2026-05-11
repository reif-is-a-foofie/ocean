from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


Kind = Literal["web", "api", "cli", "mobile", "desktop"]


@dataclass
class ProjectSpec:
    name: str
    kind: Kind
    description: str = ""
    goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    createdAt: str = field(default_factory=lambda: datetime.now().isoformat())
    # Product north star + how the assistant presents (Ocean orchestrates; user steers)
    vision: str = ""
    ai_identity: str = ""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ProjectSpec":
        k = str(d.get("kind", "web")).lower()
        if k not in ("web", "api", "cli", "mobile", "desktop"):
            k = "web"
        return ProjectSpec(
            name=d.get("name", "My Project"),
            kind=k,  # type: ignore[arg-type]
            description=d.get("description", ""),
            goals=list(d.get("goals", [])),
            constraints=list(d.get("constraints", [])),
            createdAt=d.get("createdAt") or datetime.now().isoformat(),
            vision=str(d.get("vision") or ""),
            ai_identity=str(d.get("ai_identity") or ""),
        )


@dataclass
class Task:
    title: str
    description: str
    owner: str
    files_touched: list[str] = field(default_factory=list)


@dataclass
class Message:
    author: str
    text: str
    ts: str = field(default_factory=lambda: datetime.now().isoformat())

