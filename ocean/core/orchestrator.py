from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List

from .events import OceanEvent
from .onboarding import OnboardingFlow
from .project_spec import load_project_dict
from .tasks import TaskItem


class CommandResult(Enum):
    OK = 0
    QUIT = 1


class Orchestrator:
    """Command dispatch + Textual-first onboarding until ``docs/project.json`` exists."""

    def __init__(self, cwd: Path | None = None) -> None:
        self.cwd = Path(cwd or Path.cwd()).resolve()
        self.events: List[OceanEvent] = []
        self.tasks: List[TaskItem] = []
        self.last_error: str | None = None
        self._onboarding = OnboardingFlow(self.cwd)
        for author, text in self._onboarding.bootstrap_events():
            self._append(author, text)

    @property
    def onboarding_phase(self) -> str | None:
        return self._onboarding.phase_export

    @property
    def project_configured(self) -> bool:
        return load_project_dict(self.cwd) is not None

    def _append(self, author: str, text: str) -> None:
        self.events.append(OceanEvent.now(author, text))

    def handle_command(self, raw: str) -> CommandResult:
        line = (raw or "").strip()
        if not line:
            return CommandResult.OK
        self.last_error = None
        lower = line.lower()
        parts = line.split(maxsplit=2)

        if self._onboarding.active:
            self._append("You", line)
            if lower in ("quit", "exit", "q"):
                self._append("Ocean", "Goodbye.")
                return CommandResult.QUIT
            if lower == "help" or lower == "?":
                self._append(
                    "Ocean",
                    "You are in onboarding — answer Moroni’s question above, or type `skip` to exit onboarding.",
                )
                return CommandResult.OK
            if lower == "skip":
                for author, text in self._onboarding.abandon():
                    self._append(author, text)
                return CommandResult.OK
            for author, text in self._onboarding.process_answer(line):
                self._append(author, text)
            return CommandResult.OK

        self._append("You", line)

        if lower in ("quit", "exit", "q"):
            self._append("Ocean", "Goodbye.")
            return CommandResult.QUIT

        if lower == "help" or lower == "?":
            self._append(
                "Ocean",
                "Commands: help | task add <title> | task done <id> | agents | clear | quit",
            )
            return CommandResult.OK

        if lower == "agents":
            self._append("Ocean", "Agent roster is shown in the Agents panel (idle).")
            return CommandResult.OK

        if lower == "clear":
            self.events.clear()
            self._append("Ocean", "Feed cleared.")
            return CommandResult.OK

        if len(parts) >= 2 and parts[0].lower() == "task":
            sub = parts[1].lower()
            if sub == "add" and len(parts) >= 3:
                title = parts[2].strip()
                if not title:
                    self._set_error("task add requires a title")
                    return CommandResult.OK
                t = TaskItem.create(title)
                self.tasks.append(t)
                self._append("Ocean", f"Task created [{t.id}] {t.title} (pending)")
                return CommandResult.OK
            if sub == "done" and len(parts) >= 3:
                tid = parts[2].strip()
                for t in self.tasks:
                    if t.id == tid:
                        t.status = "done"
                        self._append("Ocean", f"Task {tid} marked done.")
                        return CommandResult.OK
                self._set_error(f"Unknown task id: {tid}")
                return CommandResult.OK

        self._set_error(f"Unknown command: {parts[0]!r}")
        return CommandResult.OK

    def _set_error(self, msg: str) -> None:
        self.last_error = msg
        self._append("Ocean", f"Error: {msg}")
