from __future__ import annotations

from datetime import datetime
import os
import re
import sys
import time
import random

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


_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _sanitize(text: str) -> str:
    # Drop ANSI escape sequences and collapse excessive whitespace
    s = text or ""
    s = s.replace("\r", " ")
    s = _ANSI_RE.sub("", s)
    # Collapse runs of spaces and tabs; keep it single-line for the feed
    s = re.sub(r"[\t ]+", " ", s)
    s = s.strip()
    # Guard against extremely long lines from upstream tools
    maxw = int(os.getenv("OCEAN_FEED_MAXCOL", "240"))
    if maxw > 0 and len(s) > maxw:
        s = s[: maxw - 1] + "…"
    return s


def _write(line: str) -> None:
    # Normalize leading artifacts from any prior TTY state
    s = _sanitize(line)
    # Optional typewriter effect (enabled by default; disabled in tests or for very long lines)
    try:
        tw_env = os.getenv("OCEAN_TYPEWRITER")
        # Default ON unless explicitly disabled
        tw_enabled = True if tw_env is None else (tw_env in ("1", "true", "True"))
        if os.getenv("OCEAN_TEST") == "1":
            tw_enabled = False
        maxlen = int(os.getenv("OCEAN_TYPEWRITER_MAXLEN", "300"))
        base_delay = float(os.getenv("OCEAN_TYPEWRITER_DELAY", "0.025"))
        human = os.getenv("OCEAN_TYPEWRITER_HUMAN", "1") not in ("0", "false", "False")
        var = float(os.getenv("OCEAN_TW_VARIANCE", "0.6"))  # fraction +/- around base
        punct_mult = float(os.getenv("OCEAN_TW_PUNCT_MULT", "4.0"))
        comma_mult = float(os.getenv("OCEAN_TW_COMMA_MULT", "2.0"))
        space_mult = float(os.getenv("OCEAN_TW_SPACE_MULT", "0.3"))
        max_delay = float(os.getenv("OCEAN_TW_MAX_DELAY", "0.12"))
    except Exception:
        tw_enabled = True
        maxlen = 300
        base_delay = 0.025
        human = True
        var = 0.6
        punct_mult = 4.0
        comma_mult = 2.0
        space_mult = 0.3
        max_delay = 0.12
    # Force cursor to column 0 before printing
    try:
        sys.stdout.write("\r")
    except Exception:
        pass
    if tw_enabled and sys.stdout.isatty() and len(s) <= maxlen and base_delay > 0:
        try:
            for ch in s + "\n":
                sys.stdout.write(ch)
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
                # Avoid sleeping on newline for a snappier end
                if ch != "\n":
                    if human:
                        mult = 1.0
                        if ch == ' ':
                            mult = space_mult
                        elif ch in '.!?':
                            mult = punct_mult
                        elif ch in ',;:':
                            mult = comma_mult
                        jitter = 1.0 + random.uniform(-var, var)
                        d = min(max(base_delay * mult * jitter, 0.0), max_delay)
                        if d > 0:
                            time.sleep(d)
                    else:
                        time.sleep(base_delay)
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
