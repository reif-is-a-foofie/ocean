from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class OceanEvent:
    ts: str
    author: str
    text: str

    @classmethod
    def now(cls, author: str, text: str) -> OceanEvent:
        return cls(ts=datetime.now().strftime("%H:%M:%S"), author=author, text=text)


def event_to_dict(ev: OceanEvent) -> dict[str, Any]:
    return asdict(ev)
