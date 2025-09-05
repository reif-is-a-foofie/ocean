from __future__ import annotations

from datetime import datetime
from rich.console import Console

console = Console()

EMOJI = {
    "Ocean": "🌊",
    "Moroni": "🕹️",
    "Q": "🔫",
    "Edna": "🍩",
    "Mario": "🍄",
    "Tony": "🧪",
    "You": "You",
}


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def feed(msg: str) -> None:
    """Print a feed line with timestamp at the end.

    Example: "🌊 Ocean: Assembling the crew… [13:07:21]"
    """
    console.print(f"{msg} [{_ts()}]", soft_wrap=True, overflow="fold")


def agent_say(agent: str, text: str) -> None:
    icon = EMOJI.get(agent, "🤖")
    # Emoji + name at start, timestamp at end
    console.print(f"{icon} {agent}: {text} [{_ts()}]", soft_wrap=True, overflow="fold")


def you_say(text: str) -> None:
    console.print(f"You: {text} [{_ts()}]", soft_wrap=True, overflow="fold")
