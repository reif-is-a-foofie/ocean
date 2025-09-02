from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


Kind = Literal["web", "api", "cli"]


@dataclass
class ProjectSpec:
    name: str
    kind: Kind
    description: str = ""
    goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    createdAt: str = field(default_factory=lambda: datetime.now().isoformat())

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ProjectSpec":
        return ProjectSpec(
            name=d.get("name", "My Project"),
            kind=d.get("kind", "web"),
            description=d.get("description", ""),
            goals=list(d.get("goals", [])),
            constraints=list(d.get("constraints", [])),
            createdAt=d.get("createdAt") or datetime.now().isoformat(),
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

