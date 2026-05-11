"""Detect and repair local dev environment (venv, editable install, optional pytest)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from rich.console import Console

Notify = Callable[[str], None]

_CHECK = r"""
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
repo_ocean = (root / "ocean").resolve()
sys.path.insert(0, str(root))
try:
    import typer  # noqa: F401
    import pytest  # noqa: F401
    import httpx  # noqa: F401
    import ocean
except Exception:
    raise SystemExit(2)
got = Path(ocean.__file__).resolve().parent
raise SystemExit(0 if got == repo_ocean else 3)
"""


def resolve_ocean_repo_root(start: Path | None = None) -> Path:
    """Find repo root containing pyproject.toml and ocean/__init__.py."""
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "ocean" / "__init__.py").exists():
            return p
    raise RuntimeError(
        "Could not find Ocean repo root (need pyproject.toml + ocean/). "
        "cd into the ocean repository and try again."
    )


def _venv_python(vdir: Path) -> Path | None:
    if sys.platform == "win32":
        p = vdir / "Scripts" / "python.exe"
        return p if p.exists() else None
    for name in ("python3", "python"):
        cand = vdir / "bin" / name
        if cand.exists():
            return cand
    return None


def _interpreter_ok(repo: Path, py: Path) -> bool:
    """True if `py` imports deps and loads this repo's `ocean` package."""
    r = subprocess.run(
        [str(py), "-c", _CHECK, str(repo.resolve())],
        cwd=str(repo.resolve()),
        capture_output=True,
        text=True,
        timeout=90,
    )
    return r.returncode == 0


def _pick_interpreter(repo: Path) -> tuple[Path | None, bool]:
    """First working interpreter: ./venv if valid, else current ``sys.execut``."""
    repo = repo.resolve()
    vp = _venv_python(repo / "venv")
    if vp and _interpreter_ok(repo, vp):
        return vp, True
    cur = Path(sys.executable).resolve()
    if _interpreter_ok(repo, cur):
        return cur, False
    return None, False


def ensure_smart(
    repo: Path,
    *,
    console: Console,
    notify: Notify | None = None,
    full_pytest: bool = False,
    prefer_venv: bool = True,
) -> int:
    """Ensure editable install + deps. No-op when already healthy; repair only when needed.

    Pytest runs when ``full_pytest``, when a repair ran, or when ``OCEAN_ALWAYS_SETUP_PYTEST=1``.
    Skip pytest entirely with ``OCEAN_SKIP_SETUP_PYTEST=1``.
    """
    repo = repo.resolve()
    dot_ocean = repo / ".ocean"
    dot_ocean.mkdir(parents=True, exist_ok=True)

    def _n(msg: str) -> None:
        if notify:
            notify(msg)

    py, _used_venv = _pick_interpreter(repo)
    repaired = False

    if py is None:
        if prefer_venv:
            vdir = repo / "venv"
            if not vdir.exists():
                _n("🌊 Ocean: No usable Python env for this repo — creating ./venv …")
                console.print("[cyan]Creating venv[/cyan] → " + str(vdir))
                r = subprocess.run([sys.executable, "-m", "venv", str(vdir)], cwd=str(repo))
                if r.returncode != 0:
                    console.print("[red]venv creation failed[/red]")
                    return r.returncode
                repaired = True
            py = _venv_python(repo / "venv") or Path(sys.executable)
        else:
            py = Path(sys.executable)

        _n("🌊 Ocean: Installing editable Ocean + dependencies …")
        console.print("[cyan]pip install -e .[/cyan]")
        inst = subprocess.run([str(py), "-m", "pip", "install", "-e", "."], cwd=str(repo))
        if inst.returncode != 0:
            console.print("[red]pip install -e . failed[/red]")
            return inst.returncode
        repaired = True

        if not _interpreter_ok(repo, py):
            console.print("[red]Environment check failed after pip install[/red]")
            return 2

    skip_py = os.getenv("OCEAN_SKIP_SETUP_PYTEST", "").lower() in ("1", "true", "yes")
    tests_dir = repo / "tests"
    always_py = os.getenv("OCEAN_ALWAYS_SETUP_PYTEST", "").lower() in ("1", "true", "yes")
    run_tests = (
        not skip_py
        and tests_dir.is_dir()
        and (full_pytest or repaired or always_py)
    )

    if run_tests:
        console.print("[cyan]pytest tests/[/cyan]")
        tp = subprocess.run([str(py), "-m", "pytest", str(tests_dir), "-q"], cwd=str(repo))
        if tp.returncode != 0:
            _n("🌊 Ocean: pytest failed — fix tests before relying on codegen.")
            return tp.returncode
        if repaired or full_pytest:
            _n("🌊 Ocean: pytest OK.")

    stamp = dot_ocean / "dev_ready.json"
    try:
        stamp.write_text(
            json.dumps(
                {
                    "ok": True,
                    "at": datetime.now().isoformat(),
                    "python": str(py),
                    "repaired": repaired,
                    "pytest_ran": run_tests,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    if repaired:
        _n("🌊 Ocean: Dev environment ready.")
    return 0


def run_dev_ready(
    repo: Path,
    *,
    console: Console,
    skip_tests: bool = False,
    skip_venv: bool = False,
) -> int:
    """``ocean onboard`` — verify/install; respect skip flags."""
    os.environ.pop("OCEAN_SKIP_SETUP_PYTEST", None)
    if skip_tests:
        os.environ["OCEAN_SKIP_SETUP_PYTEST"] = "1"
    try:
        if skip_venv:
            repo = repo.resolve()
            py = Path(sys.executable)
            console.print(f"[cyan]Using current interpreter[/cyan] {py}")
            inst = subprocess.run([str(py), "-m", "pip", "install", "-e", "."], cwd=str(repo))
            if inst.returncode != 0:
                return inst.returncode
            if not skip_tests and (repo / "tests").is_dir():
                tp = subprocess.run([str(py), "-m", "pytest", str(repo / "tests"), "-q"], cwd=str(repo))
                if tp.returncode != 0:
                    return tp.returncode
            elif skip_tests:
                pass
            _write_stamp_minimal(repo)
            console.print("[green]Dev setup complete[/green]")
            return 0
        return ensure_smart(
            repo,
            console=console,
            notify=lambda m: console.print(f"[dim]{m}[/dim]"),
            full_pytest=not skip_tests,
            prefer_venv=True,
        )
    finally:
        if skip_tests:
            os.environ.pop("OCEAN_SKIP_SETUP_PYTEST", None)


def _write_stamp_minimal(repo: Path) -> None:
    dot_ocean = repo / ".ocean"
    dot_ocean.mkdir(parents=True, exist_ok=True)
    try:
        (dot_ocean / "dev_ready.json").write_text(
            json.dumps({"ok": True, "at": datetime.now().isoformat()}, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def should_offer_auto_setup(repo: Path) -> bool:
    """True when interpreters fail the repo-ocean check (for diagnostics only)."""
    if os.getenv("OCEAN_SKIP_AUTO_SETUP", "").lower() in ("1", "true", "yes"):
        return False
    py, _ = _pick_interpreter(repo)
    return py is None
