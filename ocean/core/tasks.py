from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import uuid


@dataclass
class TaskItem:
    id: str
    title: str
    status: str  # pending | done

    @classmethod
    def create(cls, title: str) -> TaskItem:
        return cls(id=uuid.uuid4().hex[:8], title=title.strip(), status="pending")


def task_to_dict(t: TaskItem) -> dict[str, Any]:
    return asdict(t)
