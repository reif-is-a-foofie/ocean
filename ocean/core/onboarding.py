"""Textual-first Moroni-style clarify flow (no Rich prompts; answers via command line)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .project_spec import default_vision_and_identity, load_project_dict, save_project_dict

_KINDS: frozenset[str] = frozenset({"web", "api", "cli", "mobile", "desktop"})


Phase = Literal["name", "kind", "description", "goals", "constraints", "complete"]


@dataclass
class OnboardingFlow:
    """Finite-state clarify until ``docs/project.json`` exists."""

    cwd: Path
    phase: Phase | None = field(init=False, default=None)
    draft: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if load_project_dict(self.cwd) is not None:
            self.phase = "complete"
        else:
            self.phase = "name"

    @property
    def active(self) -> bool:
        return self.phase is not None and self.phase != "complete"

    @property
    def phase_export(self) -> str | None:
        if self.phase is None or self.phase == "complete":
            return None
        return self.phase

    def bootstrap_events(self) -> list[tuple[str, str]]:
        if self.phase == "complete":
            return [
                (
                    "Ocean",
                    "Found docs/project.json — project already configured. Type `help` for commands.",
                )
            ]
        return [
            ("Ocean", "Welcome to Ocean."),
            ("Ocean", "Let’s run a short onboarding (Moroni-style clarify). Answer each prompt below."),
            ("Moroni", "What should we call this project? (short name)"),
        ]

    def process_answer(self, line: str) -> list[tuple[str, str]]:
        """Return feed lines (author, text) after processing one user reply during onboarding."""
        if not self.active:
            return []
        raw = line.strip()
        out: list[tuple[str, str]] = []
        if not raw:
            out.append(("Ocean", "I need a non-empty answer — try again."))
            out.extend(self._repeat_prompt())
            return out

        if self.phase == "name":
            self.draft["name"] = raw
            self.phase = "kind"
            out.append(("Moroni", f"Got it — **{raw}**. What type of project is this?"))
            out.append(("Moroni", "Reply with one of: web, api, cli, mobile, desktop"))
            return out

        if self.phase == "kind":
            k = raw.lower().strip()
            if k not in _KINDS:
                out.append(("Ocean", f"Type must be one of: {', '.join(sorted(_KINDS))}."))
                out.extend(self._repeat_prompt())
                return out
            self.draft["kind"] = k
            self.phase = "description"
            out.append(("Moroni", "One-line description — what is this for?"))
            return out

        if self.phase == "description":
            self.draft["description"] = raw
            self.phase = "goals"
            out.append(("Moroni", "Primary goals — comma-separated (e.g. ship MVP, learn, iterate)."))
            return out

        if self.phase == "goals":
            goals = [g.strip() for g in raw.split(",") if g.strip()]
            self.draft["goals"] = goals
            self.phase = "constraints"
            out.append(("Moroni", "Constraints — comma-separated, or type `none`."))
            return out

        if self.phase == "constraints":
            cons = [] if raw.lower() in ("none", "-", "n/a") else [c.strip() for c in raw.split(",") if c.strip()]
            self.draft["constraints"] = cons
            return self._finalize(out)

        return out

    def _repeat_prompt(self) -> list[tuple[str, str]]:
        if self.phase == "name":
            return [("Moroni", "What should we call this project? (short name)")]
        if self.phase == "kind":
            return [
                ("Moroni", "What type of project is this?"),
                ("Moroni", "One of: web, api, cli, mobile, desktop"),
            ]
        if self.phase == "description":
            return [("Moroni", "One-line description — what is this for?")]
        if self.phase == "goals":
            return [("Moroni", "Primary goals — comma-separated.")]
        if self.phase == "constraints":
            return [("Moroni", "Constraints — comma-separated, or `none`.")]
        return []

    def _finalize(self, prefix: list[tuple[str, str]]) -> list[tuple[str, str]]:
        name = str(self.draft.get("name", "My Project")).strip() or "My Project"
        kind = str(self.draft.get("kind", "web")).lower()
        desc = str(self.draft.get("description", "")).strip()
        goals = [str(g) for g in self.draft.get("goals", []) if str(g).strip()]
        constraints = [str(c) for c in self.draft.get("constraints", []) if str(c).strip()]
        vision, ai_identity = default_vision_and_identity(name, desc, goals)
        spec = {
            "name": name,
            "kind": kind,
            "description": desc,
            "goals": goals,
            "constraints": constraints,
            "vision": vision,
            "ai_identity": ai_identity,
            "createdAt": datetime.now().isoformat(),
        }
        path = save_project_dict(spec, self.cwd)
        self.phase = "complete"
        out = list(prefix)
        out.append(("Ocean", f"Saved project spec to {path.relative_to(self.cwd)} ✅"))
        out.append(("Ocean", f"Summary — {name} ({kind}) — goals: {', '.join(goals) or '(none)'}"))
        out.append(("Ocean", "Onboarding complete. Use `help`, `agents`, or `task add …` next."))
        return out

    def abandon(self) -> list[tuple[str, str]]:
        self.phase = "complete"
        self.draft.clear()
        return [("Ocean", "Onboarding skipped. You can run `ocean clarify` later or edit docs/project.json.")]
