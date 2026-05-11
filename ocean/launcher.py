"""Bare ``ocean`` on a TTY: ``exec`` Toad when installed; try to install if missing."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

_INSTALL_TIMEOUT_S = 300

# Shown when ``ocean tui`` fails or similar — keep short.
TOAD_INSTALL_LINES = (
    "Toad isn’t available here. Install (AGPL):",
    "  curl -fsSL https://batrachian.ai/install | sh",
    "Or Python 3.14+ in this repo’s venv: pip install -e .  (adds `toad` next to `ocean`).",
)

TOAD_FALLBACK_HINT = (
    "Toad not found — opening Ocean chat instead. "
    "Install: https://batrachian.ai/install  |  sh"
)


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


def skip_toad() -> bool:
    return os.getenv("OCEAN_SKIP_TOAD", "").strip().lower() in ("1", "true", "yes")


def auto_install_toad_enabled() -> bool:
    return os.getenv("OCEAN_AUTO_INSTALL_TOAD", "1").strip().lower() not in ("0", "false", "no")


def _prepend_path(*dirs: str) -> None:
    parts = [d for d in dirs if d and Path(d).is_dir()]
    if not parts:
        return
    os.environ["PATH"] = os.pathsep.join(parts) + os.pathsep + os.environ.get("PATH", "")


def ensure_toad_installed() -> bool:
    """Best-effort install so ``toad`` appears on PATH or next to ``sys.executable``.

    Order: pip (``batrachian-toad``) → ``uv tool`` → upstream curl installer.
    Skipped in automation / non-TTY / ``OCEAN_AUTO_INSTALL_TOAD=0``.
    """
    if toad_binary():
        return True
    if is_automation() or skip_toad() or not auto_install_toad_enabled():
        return False
    if not is_interactive_terminal():
        return False

    print("Ocean: Toad not found — installing (may take a minute)…", file=sys.stderr)

    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "batrachian-toad>=0.6.16"],
            capture_output=True,
            text=True,
            timeout=_INSTALL_TIMEOUT_S,
        )
        if r.returncode == 0 and toad_binary():
            print("Ocean: Toad ready (pip).", file=sys.stderr)
            return True
    except (subprocess.TimeoutExpired, OSError):
        pass

    uv = shutil.which("uv")
    if uv:
        try:
            r = subprocess.run(
                [uv, "tool", "install", "--upgrade", "batrachian-toad"],
                capture_output=True,
                text=True,
                timeout=_INSTALL_TIMEOUT_S,
            )
            _prepend_path(str(Path.home() / ".local" / "bin"))
            if r.returncode == 0 and toad_binary():
                print("Ocean: Toad ready (uv).", file=sys.stderr)
                return True
        except (subprocess.TimeoutExpired, OSError):
            pass

    if sys.platform == "win32":
        print(
            "Ocean: use WSL or install Toad manually on Windows.",
            file=sys.stderr,
        )
        return False

    try:
        r = subprocess.run(
            ["/bin/sh", "-c", "curl -fsSL https://batrachian.ai/install | sh"],
            capture_output=True,
            text=True,
            timeout=_INSTALL_TIMEOUT_S,
        )
        _prepend_path(
            str(Path.home() / ".local" / "bin"),
            "/opt/homebrew/bin",
            "/usr/local/bin",
        )
        if r.returncode == 0 and shutil.which("toad") and toad_binary():
            print("Ocean: Toad ready (batrachian installer).", file=sys.stderr)
            return True
    except (subprocess.TimeoutExpired, OSError):
        pass

    return False


def toad_binary() -> str | None:
    if skip_toad():
        return None
    found = shutil.which("toad")
    if found:
        return found
    bindir = Path(sys.executable).resolve().parent
    for name in ("toad", "toad.exe"):
        p = bindir / name
        try:
            if p.is_file() and os.access(p, os.X_OK):
                return str(p)
        except OSError:
            continue
    return None


def print_toad_required(msg: str | None = None) -> None:
    if msg:
        print(msg, file=sys.stderr)
    for line in TOAD_INSTALL_LINES:
        print(line, file=sys.stderr)


def exit_without_toad(msg: str | None = None) -> NoReturn:
    print_toad_required(msg)
    raise SystemExit(2)


def handoff_default_shell() -> None:
    """On an interactive TTY, replace this process with Toad when available."""
    if is_automation() or not is_interactive_terminal():
        return
    if want_chat_instead_of_tui() or skip_toad():
        return

    tb = toad_binary()
    if not tb:
        ensure_toad_installed()
        tb = toad_binary()
    if not tb:
        return
    try:
        os.execvp(tb, ["toad"])
    except OSError as e:
        exit_without_toad(f"Could not start toad ({tb}): {e}")


def resolve_bare_ocean_argv() -> list[str]:
    """After ``handoff_default_shell()``: subcommand when Toad did not ``exec``."""
    if is_automation() or not is_interactive_terminal() or want_chat_instead_of_tui() or skip_toad():
        return ["chat"]
    if not toad_binary():
        ensure_toad_installed()
    if not toad_binary():
        print(TOAD_FALLBACK_HINT, file=sys.stderr)
        return ["chat"]
    print(
        "Ocean: expected Toad to replace this process — falling back to chat.",
        file=sys.stderr,
    )
    return ["chat"]


def launch_toad_or_die() -> NoReturn:
    """For ``ocean tui``: replace with Toad or exit."""
    if not is_interactive_terminal():
        exit_without_toad("Need a TTY for Toad.")
    tb = toad_binary()
    if not tb:
        ensure_toad_installed()
        tb = toad_binary()
    if not tb:
        exit_without_toad()
    try:
        os.execvp(tb, ["toad"])
    except OSError as e:
        exit_without_toad(f"Could not start toad ({tb}): {e}")
    raise RuntimeError("unreachable")  # pragma: no cover
