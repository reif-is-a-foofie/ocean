from __future__ import annotations

from datetime import datetime
import os
import sys
import time

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


def _write(line: str) -> None:
    # Normalize leading artifacts from any prior TTY state
    s = (line or "").replace("\r", "").lstrip()
    # Optional typewriter effect (disabled in tests or for very long lines)
    try:
        tw_enabled = os.getenv("OCEAN_TYPEWRITER") in ("1", "true", "True")
        if os.getenv("OCEAN_TEST") == "1":
            tw_enabled = False
        maxlen = int(os.getenv("OCEAN_TYPEWRITER_MAXLEN", "300"))
        delay = float(os.getenv("OCEAN_TYPEWRITER_DELAY", "0.01"))
    except Exception:
        tw_enabled = False
        maxlen = 300
        delay = 0.01
    # Force cursor to column 0 before printing
    try:
        sys.stdout.write("\r")
    except Exception:
        pass
    if tw_enabled and sys.stdout.isatty() and len(s) <= maxlen and delay > 0:
        try:
            for ch in s + "\n":
                sys.stdout.write(ch)
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
                # Avoid sleeping on newline for a snappier end
                if ch != "\n":
                    time.sleep(delay)
            return
        except Exception:
            # Fallback to normal write if anything goes wrong
            pass
    sys.stdout.write(s + "\n")
    try:
        sys.stdout.flush()
    except Exception:
        pass


def feed(msg: str) -> None:
    """Print a simple feed line with timestamp at the end (no Rich, no ANSI)."""
    _write(f"{msg} [{_ts()}]")


def agent_say(agent: str, text: str) -> None:
    icon = EMOJI.get(agent, "🤖")
    # Emoji + name at start, timestamp at end
    _write(f"{icon} {agent}: {text} [{_ts()}]")


def you_say(text: str) -> None:
    _write(f"You: {text} [{_ts()}]")
