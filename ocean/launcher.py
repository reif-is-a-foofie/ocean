"""Bare ``ocean`` launcher helpers (TTY / automation detection).

Default UI is the **Textual** shell on an interactive TTY; ``ocean chat`` is used
when non-interactive or in automation (or ``OCEAN_DEFAULT_UI=chat``).
"""

from __future__ import annotations

import os
import sys


def is_interactive_terminal() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def is_automation() -> bool:
    return os.getenv("OCEAN_TEST") == "1" or os.getenv("PYTEST_CURRENT_TEST") is not None


def want_chat_instead_of_tui() -> bool:
    v = os.getenv("OCEAN_DEFAULT_UI", "").strip().lower()
    return v in ("chat", "feed", "cli")


def resolve_bare_ocean_argv() -> list[str]:
    """Typer subcommand when bare ``ocean`` should not start the Textual shell."""
    return ["chat"]
