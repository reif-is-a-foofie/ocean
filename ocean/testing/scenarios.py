"""Pilot / scenario helpers — structured failure blobs for agents."""

from __future__ import annotations

import traceback
from typing import Any


def pilot_failure_report(
    *,
    scenario: str,
    expected: str,
    actual: str,
    app: Any | None = None,
    exc: BaseException | None = None,
) -> dict[str, Any]:
    """Structured report when a Pilot-style assertion or workflow fails."""
    export: dict[str, Any] | None = None
    recent_events: list[dict[str, Any]] = []
    if app is not None and hasattr(app, "export_state"):
        try:
            export = app.export_state()  # type: ignore[assignment]
            recent_events = list(export.get("visible_events") or [])[-24:]
        except Exception:
            export = {"error": "export_state_failed"}

    tb: str | None = None
    if exc is not None:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    suspected: str | None = None
    if exc and tb:
        for prefix, label in (
            ("ocean/core/", "ocean.core"),
            ("ocean/cli.py", "ocean.cli"),
        ):
            if prefix in tb:
                suspected = label
                break

    return {
        "scenario": scenario,
        "expected_behavior": expected,
        "actual_behavior": actual,
        "exported_app_state": export,
        "recent_event_feed": recent_events,
        "traceback": tb or None,
        "suspected_module": suspected,
    }
