from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now().isoformat()


@dataclass
class ProductState:
    """Shared product context for autonomous cycles (persisted under `.ocean/`)."""

    schema_version: int = 1
    vision_summary: str = ""
    audience: str = ""
    cycle_count: int = 0
    last_cycle_at: str | None = None
    tokens_used_last_cycle: int = 0
    tokens_budget_per_cycle: int | None = None
    user_notes: list[str] = field(default_factory=list)
    decision_log: list[dict[str, Any]] = field(default_factory=list)
    open_conflicts: list[dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def state_path(runtime: Path) -> Path:
        return runtime / "product_state.json"

    @classmethod
    def load(cls, runtime: Path) -> ProductState:
        path = cls.state_path(runtime)
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return cls()
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            vision_summary=str(data.get("vision_summary", "")),
            audience=str(data.get("audience", "")),
            cycle_count=int(data.get("cycle_count", 0)),
            last_cycle_at=data.get("last_cycle_at"),
            tokens_used_last_cycle=int(data.get("tokens_used_last_cycle", 0)),
            tokens_budget_per_cycle=data.get("tokens_budget_per_cycle"),
            user_notes=list(data.get("user_notes", [])),
            decision_log=list(data.get("decision_log", [])),
            open_conflicts=list(data.get("open_conflicts", [])),
        )

    def save(self, runtime: Path) -> Path:
        runtime.mkdir(parents=True, exist_ok=True)
        # Cap unbounded lists
        if len(self.decision_log) > 500:
            self.decision_log = self.decision_log[-500:]
        if len(self.user_notes) > 200:
            self.user_notes = self.user_notes[-200:]
        path = self.state_path(runtime)
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def log_decision(self, actor: str, text: str, **extra: Any) -> None:
        entry: dict[str, Any] = {"ts": _now_iso(), "actor": actor, "text": text}
        if extra:
            entry["meta"] = extra
        self.decision_log.append(entry)
