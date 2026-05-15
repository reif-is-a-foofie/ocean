"""Bare ``ocean`` launcher helpers.

The default product entry is **terminal chat** (same as ``ocean chat``). The
``entrypoint`` appends ``chat`` when argv is only the program name.
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


def resolve_bare_ocean_argv() -> list[str]:
    """Typer subcommand appended when the user runs bare ``ocean`` (no args)."""
    return ["chat"]
