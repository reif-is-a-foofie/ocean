"""Single source for crew agent emoji and short labels (feed + codex-wrap)."""

from __future__ import annotations

# Emoji per agent name (Ocean Doctor uses 🤿 in cli — not listed here)
AGENT_EMOJI: dict[str, str] = {
    "Ocean": "🌊",
    "Moroni": "🕹️",
    "Q": "🔧",
    "Edna": "🎨",
    "Mario": "🍄",
    "Tony": "🧪",
    "You": "You",
}

# (short_role, specialty) for crew summary lines — every default_agents() name should appear
CREW_SUMMARY: dict[str, tuple[str, str]] = {
    "Moroni": ("Architect & Brain", "Vision, planning, coordination"),
    "Q": ("Backend engineer", "APIs, services, data models"),
    "Edna": ("Designer & UI/UX", "UI craft, screenshots/visual QA, tokens & a11y"),
    "Mario": ("DevOps & infrastructure", "CI/CD, deployment, monitoring"),
    "Tony": ("Experimenter / test pilot", "Prototypes, stress tests, telemetry"),
}
