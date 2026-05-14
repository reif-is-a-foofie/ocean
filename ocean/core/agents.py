from __future__ import annotations

from typing import Any


def agent_status_snapshot() -> list[dict[str, Any]]:
    """Read-only view of default crew for UI and export_state (delegates to existing agents)."""
    from ocean.agents import default_agents

    rows: list[dict[str, Any]] = []
    for agent in default_agents():
        rows.append(
            {
                "name": getattr(agent, "name", "?"),
                "role": getattr(agent, "role", ""),
                "status": "idle",
            }
        )
    return rows
