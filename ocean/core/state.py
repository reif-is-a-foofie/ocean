from __future__ import annotations

from typing import Any

from .agents import agent_status_snapshot
from .events import event_to_dict
from .orchestrator import Orchestrator
from .tasks import task_to_dict


def build_export_payload(
    *,
    orchestrator: Orchestrator,
    current_screen: str,
    focused_widget: str | None,
    command_input_value: str,
) -> dict[str, Any]:
    """JSON-serializable snapshot for tests and external agents."""
    return {
        "current_screen": current_screen,
        "focused_widget": focused_widget,
        "visible_events": [event_to_dict(e) for e in orchestrator.events[-80:]],
        "active_agents": agent_status_snapshot(),
        "pending_tasks": [task_to_dict(t) for t in orchestrator.tasks],
        "last_error": orchestrator.last_error,
        "command_input_value": command_input_value,
        "onboarding_phase": orchestrator.onboarding_phase,
        "project_configured": orchestrator.project_configured,
    }
