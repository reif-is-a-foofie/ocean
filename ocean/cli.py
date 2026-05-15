from __future__ import annotations

import getpass
import json
import os
import subprocess
import sys
from datetime import datetime
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

import typer
from click.exceptions import Abort
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from . import __version__
from .agents import default_agents
from .models import ProjectSpec
from .planner import generate_backlog, execute_backlog
from .mcp import MCP
from . import context as ctx
from . import codex_exec
from .persona import agent_voice_skills_chat_lines, crew_cards_plain_text, voice_brief
from .feed import feed as feed_line, you_say, agent_say as feed_agent_say
from .personas import AGENT_EMOJI, CREW_SUMMARY
from .backends import (
    VALID_BACKENDS,
    get_codegen_backend,
    prompt_codegen_backend_if_needed,
    prompt_codegen_model_if_needed,
    apply_backend_env_from_prefs,
    probe_snapshot,
)
from .dotenv_merge import merge_dotenv_assignments
from .events_emit import emit_setup
from .runtime import format_status_text, ingest_message, run_cycle
from . import token_budget


def _is_test_env() -> bool:
    """Detect pytest/test runner environment.

    Returns True if either OCEAN_TEST=1 is set or Pytest is invoking
    the CLI (PYTEST_CURRENT_TEST is present)."""
    return (os.getenv("OCEAN_TEST") == "1") or (os.getenv("PYTEST_CURRENT_TEST") is not None)


def _external_startup_disabled() -> bool:
    return _is_test_env() or os.getenv("OCEAN_DISABLE_CODEX") in ("1", "true", "True")

console = Console()
# Route all console output through the feed by default to avoid column offsets and stray ANSI
if os.getenv("OCEAN_FEED_ONLY", "1") not in ("0", "false", "False"):
    import re as _re
    _RICH_TAG = _re.compile(r"\[/?[a-zA-Z][^\[\]]*\]")

    def _cprint_to_feed(*args, **kwargs):  # noqa: ANN001
        try:
            msg = " ".join(str(a) for a in args)
        except Exception:
            msg = " ".join(map(str, args))
        feed(_RICH_TAG.sub("", msg))
    try:
        console.print = _cprint_to_feed  # type: ignore[attr-defined]
    except Exception:
        pass
app = typer.Typer(add_completion=False, no_args_is_help=False, help="OCEAN CLI orchestrator")
# Sub-apps
version_app = typer.Typer(help="Versioning utilities")
token_app = typer.Typer(help="Token diagnostics")
house_app = typer.Typer(help="Housekeeping and cleanup")
app.add_typer(version_app, name="version")
app.add_typer(token_app, name="token")
app.add_typer(house_app, name="cleanup")

ROOT = Path.cwd()
DOCS = ROOT / "docs"
LOGS = ROOT / "logs"
BACKEND = ROOT / "backend"
UI = ROOT / "ui"
DEVOPS = ROOT / "devops"
PROJECTS = ROOT / "projects"

_preflight_intro_sent: bool = False


def ensure_repo_structure() -> None:
    for p in [DOCS, LOGS, BACKEND, UI, DEVOPS, PROJECTS, ROOT / ".github" / "workflows"]:
        p.mkdir(parents=True, exist_ok=True)


def _load_env_file(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE lines, no quotes expansion."""
    try:
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass


def _create_venv(path: Path) -> None:
    """Create a Python venv at path if missing and install basic deps.

    - Installs editable package in root venv
    - Installs FastAPI/uvicorn in workspace venvs for web/api kind
    """
    if not path.exists():
        subprocess.run([sys.executable, "-m", "venv", str(path)], check=False)


def _free_port(start: int = 8000, limit: int = 20) -> int:
    import socket
    p = start
    for _ in range(limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                p += 1
    return start


def _start_local_runtime_simple() -> Optional[str]:
    """Start FastAPI backend in a background thread (single process, no subprocesses).

    The FastAPI app already serves static UI files at /ui via StaticFiles.
    Returns the base URL string or None.
    """
    import threading
    backend_app = BACKEND / "app.py"
    if not backend_app.exists():
        return None
    try:
        import uvicorn
    except ImportError:
        return None
    port = _free_port(8000)
    ui_dir = UI
    if ui_dir.exists():
        try:
            api_base = f"http://127.0.0.1:{port}"
            (ui_dir / "config.js").write_text(f"window.API_BASE=\"{api_base}\";\n", encoding="utf-8")
        except Exception:
            pass
    t = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": "backend.app:app", "host": "127.0.0.1", "port": port, "log_level": "warning"},
        daemon=True,
    )
    t.start()
    return f"http://127.0.0.1:{port}"


def _ensure_codex_auth() -> None:
    """Ensure Codex CLI is authenticated; always trigger a best-effort login.

    Per user policy: re-auth every time (idempotent), ignore failures.
    """
    if _external_startup_disabled():
        return
    codex = shutil.which("codex")
    if not codex:
        return
    try:
        # Fast-path: discover an existing token on disk before attempting any login
        if not os.getenv("CODEX_AUTH_TOKEN"):
            try:
                tok = subprocess.check_output(
                    "grep -Rho 'ey[A-Za-z0-9_\\-\\.]\\{20,\\}' ~/.codex ~/.config/codex 2>/dev/null | head -n 1",
                    shell=True,
                    text=True,
                ).strip()
                if tok:
                    os.environ["CODEX_AUTH_TOKEN"] = tok
                    os.environ["OCEAN_CODEX_AUTH"] = "1"
                    feed("🌊 Ocean: Found Codex auth token via grep (masked).")
                    return
            except Exception:
                pass
        # If a token already exists or CLI reports logged-in, skip active login
        try:
            from . import codex_exec as _ce
            if os.getenv("CODEX_AUTH_TOKEN") or _ce._logged_in_via_codex():  # type: ignore[attr-defined]
                # Best-effort: ensure token is exported for subprocesses
                for args in (["auth", "print-token"], ["auth", "token"], ["auth", "--show-token"], ["auth", "export"]):
                    try:
                        tok = subprocess.run(["codex", *args], capture_output=True, text=True, timeout=5)
                        cand = (tok.stdout or tok.stderr or "").strip()
                        if cand and len(cand) > 20 and "\n" not in cand:
                            os.environ["CODEX_AUTH_TOKEN"] = cand
                            os.environ["OCEAN_CODEX_AUTH"] = "1"
                            break
                    except Exception:
                        continue
                return
        except Exception:
            pass

        # Attempt a login (idempotent if already authenticated)
        proc = subprocess.run(["codex", "auth", "login"], capture_output=True, text=True, timeout=45, check=False)
        # Try to extract id_token from any success URL printed
        try:
            import re
            import json as _json
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            m = re.search(r"id_token=([A-Za-z0-9\-_.]+)", combined)
            if m:
                tok = m.group(1)
                os.environ["CODEX_AUTH_TOKEN"] = tok
                os.environ["OCEAN_CODEX_AUTH"] = "1"
                # Persist a marker file for detection
                home = Path.home() / ".codex"
                home.mkdir(parents=True, exist_ok=True)
                auth_file = home / "auth.json"
                try:
                    payload = {"id_token": tok, "updatedAt": datetime.now().isoformat(), "source": "ocean"}
                    auth_file.write_text(_json.dumps(payload, indent=2), encoding="utf-8")
                except Exception:
                    pass
        except Exception:
            pass

        # Probe status post-login
        subprocess.run(["codex", "auth"], capture_output=True, text=True, timeout=10)
        # Best-effort: export a token for downstream tools if available.
        if not os.getenv("CODEX_AUTH_TOKEN"):
            for args in (["auth", "print-token"], ["auth", "token"], ["auth", "--show-token"], ["auth", "export"]):
                try:
                    tok = subprocess.run(["codex", *args], capture_output=True, text=True, timeout=5)
                    cand = (tok.stdout or tok.stderr or "").strip()
                    # Heuristic: token-like if long enough and not multi-line
                    if cand and len(cand) > 20 and "\n" not in cand:
                        os.environ["CODEX_AUTH_TOKEN"] = cand
                        os.environ["OCEAN_CODEX_AUTH"] = "1"
                        break
                except Exception:
                    continue
    except Exception:
        pass


def _start_docker_daemon(timeout_s: int = 120) -> bool:
    """Attempt to start the Docker daemon (best effort), then wait until healthy.

    - macOS: open /Applications/Docker.app
    - Linux: systemctl start docker (requires sudo)
    Returns True if daemon became healthy within timeout, else False.
    """
    import platform
    os_name = platform.system().lower()
    try:
        if os_name == "darwin":
            # Launch Docker Desktop
            subprocess.run(["open", "/Applications/Docker.app"], check=False)
        elif os_name == "linux":
            # Try starting service
            subprocess.run(["sudo", "systemctl", "start", "docker"], check=False)
    except Exception:
        pass
    # Wait loop
    import time
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            probe = subprocess.run(["docker", "info"], capture_output=True)
            if probe.returncode == 0:
                return True
        except Exception:
            pass
        time.sleep(5)
    return False

def _install_docker() -> bool:
    """Best-effort Docker/Compose installation by OS.

    Returns True if an install command ran (not necessarily succeeded).
    """
    ran = False
    try:
        if shutil.which("docker"):
            return False
        # Detect OS
        uname = subprocess.run(["uname"], capture_output=True, text=True).stdout.strip().lower()
        if "darwin" in uname or sys.platform == "darwin":
            # macOS: use Homebrew cask if available
            if shutil.which("brew"):
                console.print("[yellow]Installing Docker Desktop via Homebrew…[/yellow]")
                subprocess.run(["brew", "install", "--cask", "docker"], check=False)
                ran = True
                console.print("[yellow]Attempting to launch Docker.app…[/yellow]")
                subprocess.run(["open", "/Applications/Docker.app"], check=False)
        elif Path("/etc/debian_version").exists():
            console.print("[yellow]Installing Docker on Debian/Ubuntu…[/yellow]")
            subprocess.run(["sudo", "apt-get", "update"], check=False)
            subprocess.run(["sudo", "apt-get", "install", "-y", "docker.io", "docker-compose-plugin"], check=False)
            subprocess.run(["sudo", "systemctl", "enable", "--now", "docker"], check=False)
            ran = True
        elif Path("/etc/fedora-release").exists() or Path("/etc/redhat-release").exists():
            console.print("[yellow]Installing Docker on Fedora/RHEL…[/yellow]")
            subprocess.run(["sudo", "dnf", "install", "-y", "docker", "docker-compose-plugin"], check=False)
            subprocess.run(["sudo", "systemctl", "enable", "--now", "docker"], check=False)
            ran = True
        elif Path("/etc/arch-release").exists():
            console.print("[yellow]Installing Docker on Arch…[/yellow]")
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "docker", "docker-compose"], check=False)
            subprocess.run(["sudo", "systemctl", "enable", "--now", "docker"], check=False)
            ran = True
    except Exception:
        pass
    return ran

def _ensure_root_venv() -> None:
    if _is_test_env():
        return
    try:
        from . import setup_flow as _sf

        if _sf.resolve_ocean_repo_root().resolve() == Path.cwd().resolve():
            # ocean repo: chat() already ran ensure_smart()
            return
    except RuntimeError:
        pass
    v = ROOT / "venv"
    if not v.exists():
        console.print("[dim]Creating project venv under ./venv…[/dim]")
        _create_venv(v)
        pip = v / "bin" / "pip"
        if pip.exists():
            # Quiet editable install; log to logs/ if needed
            try:
                res = subprocess.run([str(pip), "install", "-e", "."], capture_output=True, text=True, check=False)
                try:
                    LOGS.mkdir(parents=True, exist_ok=True)
                    (LOGS / "root-venv-install.log").write_text((res.stdout or "") + ("\n" + (res.stderr or "")), encoding="utf-8")
                except Exception:
                    pass
            except Exception:
                pass


def session_log_path() -> Path:
    ensure_repo_structure()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return LOGS / f"session-{ts}.log"


def feed(msg: str) -> None:
    feed_line(msg)


# -----------------------
# Version bump utilities
# -----------------------

def _read_version() -> str:
    """Read current version from pyproject.toml or ocean/__init__.py."""
    try:
        pj = ROOT / "pyproject.toml"
        if pj.exists():
            for line in pj.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("version") and "=" in line:
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    except Exception:
        pass
    try:
        init = ROOT / "ocean" / "__init__.py"
        if init.exists():
            for line in init.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("__version__") and "=" in line:
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    except Exception:
        pass
    return "0.0.0"


def _bump_semver(ver: str, part: str) -> str:
    try:
        major, minor, patch = [int(x) for x in ver.split(".")[:3]]
    except Exception:
        major, minor, patch = 0, 0, 0
    if part == "major":
        major += 1; minor = 0; patch = 0
    elif part == "minor":
        minor += 1; patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def _write_version(new_version: str) -> None:
    # pyproject.toml
    try:
        pj = ROOT / "pyproject.toml"
        if pj.exists():
            lines = pj.read_text(encoding="utf-8").splitlines()
            out = []
            for ln in lines:
                if ln.strip().startswith("version") and "=" in ln:
                    out.append(f"version = \"{new_version}\"")
                else:
                    out.append(ln)
            pj.write_text("\n".join(out) + "\n", encoding="utf-8")
    except Exception:
        pass
    # ocean/__init__.py
    try:
        init = ROOT / "ocean" / "__init__.py"
        if init.exists():
            lines = init.read_text(encoding="utf-8").splitlines()
            out = []
            for ln in lines:
                if ln.strip().startswith("__version__") and "=" in ln:
                    out.append(f"__version__ = \"{new_version}\"")
                else:
                    out.append(ln)
            init.write_text("\n".join(out) + "\n", encoding="utf-8")
    except Exception:
        pass


def _update_changelog(new_version: str, note: str | None = None) -> None:
    """Prepend a simple entry to CHANGELOG.md with date and optional note."""
    path = ROOT / "CHANGELOG.md"
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## {new_version} — {today}\n\n"
    body = f"- {note or 'Automated version bump to align test environment.'}\n\n"
    try:
        if path.exists():
            existing = path.read_text(encoding="utf-8")
        else:
            existing = "# Changelog\n\n"
        path.write_text(existing + header + body if existing.strip() == "# Changelog" else header + body + existing, encoding="utf-8")
    except Exception:
        pass


def _git_commit_and_push(files: list[str], new_version: str) -> tuple[bool, str]:
    """Commit given files and push. Returns (ok, detail)."""
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, capture_output=True)
        subprocess.run(["git", "add", *files], check=True)
        msg = f"chore: bump version to {new_version}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        # If no upstream, set it to origin/<current-branch>
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], capture_output=True, text=True)
        if res.returncode != 0:
            branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
            br = (branch.stdout or "main").strip()
            subprocess.run(["git", "push", "-u", "origin", br], check=True)
        else:
            subprocess.run(["git", "push"], check=True)
        return True, "pushed"
    except subprocess.CalledProcessError as e:
        return False, f"git error: {e}"
    except Exception as e:
        return False, f"error: {e}"


@version_app.command("bump", help="Bump version (patch/minor/major), update changelog, commit and push.")
def version_bump(
    part: str = typer.Option("patch", "--part", "-p", help="Which semver part to bump", case_sensitive=False),
    push: bool = typer.Option(True, "--push/--no-push", help="Push commit to upstream"),
    note: str = typer.Option(None, "--note", help="Changelog note"),
):
    part = part.lower()
    if part not in ("patch", "minor", "major"):
        feed("🌊 Ocean: Invalid part; use patch|minor|major.")
        raise typer.Exit(code=2)
    cur = _read_version()
    new = _bump_semver(cur, part)
    _write_version(new)
    _update_changelog(new, note)
    feed(f"🌊 Ocean: Version bumped {cur} → {new}.")
    files = ["pyproject.toml", "ocean/__init__.py", "CHANGELOG.md"]
    if push:
        ok, detail = _git_commit_and_push(files, new)
        if ok:
            feed("🌊 Ocean: Changes committed and pushed.")
        else:
            feed(f"🌊 Ocean: ⚠️ Push skipped/failure — {detail}.")
    else:
        feed("🌊 Ocean: Push disabled (use --push to enable).")


def _hydrate_tokens() -> None:
    """Make sure tokens from global locations are available to this process.

    - CODEX: read ~/.codex/auth.json and export CODEX_AUTH_TOKEN if missing
    - OPENAI: read home-level .env files (~/.env, ~/.config/ocean/.env) if present
    """
    try:
        # OPENAI-style keys from home-level .env files
        _load_env_file(Path.home() / ".env")
        _load_env_file(Path.home() / ".config" / "ocean" / ".env")
    except Exception:
        pass
    # Announce API key presence once (masked) for easy diagnostics
    try:
        key = os.getenv("OPENAI_API_KEY")
        if key and os.getenv("OCEAN_APIKEY_ANNOUNCED") != "1":
            masked = (key[:6] + "…") if len(key) > 6 else "(set)"
            feed(f"🌊 Ocean: OPENAI_API_KEY detected (len={len(key)}, prefix={masked})")
            os.environ["OCEAN_APIKEY_ANNOUNCED"] = "1"
    except Exception:
        pass
    try:
        # CODEX token from auth.json
        if not os.getenv("CODEX_AUTH_TOKEN"):
            auth = Path.home() / ".codex" / "auth.json"
            if auth.exists():
                import json as _json
                data = _json.loads(auth.read_text(encoding="utf-8"))
                tok = (data.get("id_token") or "").strip()
                if tok:
                    os.environ["CODEX_AUTH_TOKEN"] = tok
                    os.environ["OCEAN_CODEX_AUTH"] = "1"
    except Exception:
        pass


def _interactive_secret_stdin() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _prompt_openai_api_key_if_needed() -> None:
    """If OPENAI_API_KEY is unset, prompt (hidden) and merge into workspace ``.env``."""
    if os.getenv("OPENAI_API_KEY", "").strip():
        return
    if os.getenv("OCEAN_SKIP_OPENAI_KEY_PROMPT") in ("1", "true", "True"):
        return
    if _is_test_env():
        return
    if os.getenv("OCEAN_ALLOW_QUESTIONS", "1") in ("0", "false", "False"):
        return
    emit_setup(
        "question",
        id="openai_api_key",
        message="OPENAI_API_KEY required for openai_api backend (value is not logged).",
        secure=True,
    )
    if not _interactive_secret_stdin():
        emit_setup(
            "info",
            id="openai_api_key",
            skipped="non_tty",
            message="Set OPENAI_API_KEY in the environment or .env; interactive prompt needs a TTY.",
        )
        return
    try:
        raw = getpass.getpass("OPENAI_API_KEY (input hidden): ").strip()
    except Exception:
        raw = ""
    if not raw:
        emit_setup("info", id="openai_api_key", saved=False, empty=True)
        return
    merge_dotenv_assignments(ROOT / ".env", {"OPENAI_API_KEY": raw})
    os.environ["OPENAI_API_KEY"] = raw
    masked = (raw[:6] + "…") if len(raw) > 6 else "(set)"
    emit_setup("phase_end", id="openai_api_key", saved=True, prefix_masked=masked)
    feed(f"🌊 Ocean: OPENAI_API_KEY saved to .env (len={len(raw)}, prefix={masked})")


def _prompt_gemini_api_key_if_needed() -> None:
    """If GEMINI_API_KEY and GOOGLE_API_KEY are unset, prompt (hidden) and merge into ``.env``."""
    if (os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()):
        return
    if os.getenv("OCEAN_SKIP_GEMINI_KEY_PROMPT") in ("1", "true", "True"):
        return
    if _is_test_env():
        return
    if os.getenv("OCEAN_ALLOW_QUESTIONS", "1") in ("0", "false", "False"):
        return
    emit_setup(
        "question",
        id="gemini_api_key",
        message="GEMINI_API_KEY required for gemini_api backend (value is not logged).",
        secure=True,
    )
    if not _interactive_secret_stdin():
        emit_setup(
            "info",
            id="gemini_api_key",
            skipped="non_tty",
            message="Set GEMINI_API_KEY or GOOGLE_API_KEY in the environment or .env; interactive prompt needs a TTY.",
        )
        return
    try:
        raw = getpass.getpass("GEMINI_API_KEY (input hidden): ").strip()
    except Exception:
        raw = ""
    if not raw:
        emit_setup("info", id="gemini_api_key", saved=False, empty=True)
        return
    merge_dotenv_assignments(ROOT / ".env", {"GEMINI_API_KEY": raw})
    os.environ["GEMINI_API_KEY"] = raw
    masked = (raw[:6] + "…") if len(raw) > 6 else "(set)"
    emit_setup("phase_end", id="gemini_api_key", saved=True, prefix_masked=masked)
    feed(f"🌊 Ocean: GEMINI_API_KEY saved to .env (len={len(raw)}, prefix={masked})")


def _run_setup_credentials(backend: str) -> None:
    """Backend-specific credential steps (Codex auth, OpenAI key, or skip)."""
    emit_setup("phase_start", id="credentials", codegen_backend=backend)
    try:
        if backend == "codex":
            if not _external_startup_disabled():
                _ensure_codex_auth()
            emit_setup("info", id="credentials", codex_auth_attempted=not _external_startup_disabled())
        elif backend == "openai_api":
            _prompt_openai_api_key_if_needed()
            _load_env_file(ROOT / ".env")
        elif backend == "gemini_api":
            _prompt_gemini_api_key_if_needed()
            _load_env_file(ROOT / ".env")
        elif backend == "cursor_handoff":
            feed(
                "🌊 Ocean: cursor_handoff — no Ocean-side LLM key required; "
                "use Cursor in the IDE and docs/handoffs/ once plans exist."
            )
            emit_setup("info", id="credentials", message="cursor_handoff_skip_llm_cred")
        elif backend == "dry_plan_only":
            feed("🌊 Ocean: dry_plan_only — backlog/plan only; no LLM credential for Ocean codegen.")
            emit_setup("info", id="credentials", message="dry_plan_only_skip_llm_cred")
    finally:
        emit_setup("phase_end", id="credentials")


def _warmup_codex(model: str | None = None, timeout: int = 25) -> None:
    """Warm Codex up without executing a model.

    - Runs `codex --version` to verify CLI presence
    - Probes `codex auth` to verify subscription auth
    - Attempts a login once if needed (idempotent)
    - Sets OCEAN_CODEX_AUTH=1 on success
    - Emits one concise feed line only on failure
    """
    if _external_startup_disabled():
        return
    try:
        import shutil
        import subprocess
        codex = shutil.which("codex")
        if not codex:
            feed("🌊 Ocean: ❌ Codex CLI not found on PATH (warmup). Install 'codex'.")
            return
        # Version check (presence only)
        v = subprocess.run([codex, "--version"], capture_output=True, text=True, timeout=timeout)
        if v.returncode != 0:
            head = (v.stderr or v.stdout or "").strip().splitlines()[:1]
            feed("🌊 Ocean: ❌ codex --version failed — " + (head[0] if head else "no output"))
            return
        # Auth probe
        a = subprocess.run([codex, "auth"], capture_output=True, text=True, timeout=timeout)
        txt = (a.stdout or a.stderr or "").lower()
        if any(k in txt for k in ("logged in", "authenticated", "already logged")) or os.getenv("CODEX_AUTH_TOKEN"):
            os.environ["OCEAN_CODEX_AUTH"] = "1"
            # Announce subscription once per session
            if os.getenv("OCEAN_CODEX_ANNOUNCED") != "1":
                ver = (v.stdout or v.stderr or "").strip().splitlines()[:1]
                try:
                    feed(
                        "🌊 Ocean: Codex auth OK (CLI responded); successful `codex exec` not verified until probe runs."
                        + (f" ({ver[0]})" if ver else "")
                    )
                except Exception:
                    pass
                os.environ["OCEAN_CODEX_ANNOUNCED"] = "1"
            return
        # Attempt a login (idempotent), then re-probe
        _ensure_codex_auth()
        a2 = subprocess.run([codex, "auth"], capture_output=True, text=True, timeout=timeout)
        txt2 = (a2.stdout or a2.stderr or "").lower()
        if any(k in txt2 for k in ("logged in", "authenticated", "already logged")) or os.getenv("CODEX_AUTH_TOKEN"):
            os.environ["OCEAN_CODEX_AUTH"] = "1"
            if os.getenv("OCEAN_CODEX_ANNOUNCED") != "1":
                ver = (v.stdout or v.stderr or "").strip().splitlines()[:1]
                try:
                    feed(
                        "🌊 Ocean: Codex auth OK (CLI responded); successful `codex exec` not verified until probe runs."
                        + (f" ({ver[0]})" if ver else "")
                    )
                except Exception:
                    pass
                os.environ["OCEAN_CODEX_ANNOUNCED"] = "1"
            return
        # Failure: keep it concise
        head = (a2.stdout or a2.stderr or a.stdout or a.stderr or "").strip().splitlines()[:2]
        feed("🌊 Ocean: ❌ Codex auth not ready — " + (" | ".join(s.strip() for s in head) or "no output"))
    except Exception:
        # Stay silent; normal flow will emit detailed reasons
        pass


def _home_repo_root() -> Path:
    """Return the path to the Ocean 'home' repo (where this package lives)."""
    return Path(__file__).resolve().parent.parent


def _switch_root(new_root: Path) -> None:
    """Rebind module-level path constants to a new repository root."""
    global ROOT, DOCS, LOGS, BACKEND, UI, DEVOPS, PROJECTS
    ROOT = new_root
    DOCS = ROOT / "docs"
    LOGS = ROOT / "logs"
    BACKEND = ROOT / "backend"
    UI = ROOT / "ui"
    DEVOPS = ROOT / "devops"
    PROJECTS = ROOT / "projects"


def _is_workspace(path: Path) -> bool:
    return (path / ".ocean_workspace").exists()


def _prepare_workspace_from_cwd() -> None:
    """If running outside the Ocean home repo, copy the current repo into a safe workspace.

    - Workspace name: ocean_<basename> (e.g., ocean_brython-snake)
    - Created under the Ocean home repo root (sibling to 'ocean', 'docs', etc.)
    - Skips typical transient directories (.git, venv, node_modules, __pycache__, logs)
    - Switches CWD and rebinds ROOT/DOCS/… to the workspace
    """
    if os.getenv("OCEAN_DISABLE_WORKSPACE") in ("1", "true", "True"):
        return
    home = _home_repo_root()
    here = Path.cwd()
    # If we are already in the home repo or a workspace, do nothing
    if here == home or str(here).startswith(str(home)):
        # Still support marker check: if already a workspace, keep it
        return
    # Define workspace destination
    ws_name = f"ocean_{here.name}"
    dest = home / ws_name
    dest.mkdir(parents=True, exist_ok=True)
    # Copy content from current repo to workspace (best-effort incremental)
    def _ignore(dir, names):  # noqa: ANN001
        patterns = {".git", ".hg", ".svn", "__pycache__", ".pytest_cache", "venv", ".venv", "node_modules", "logs", ".mypy_cache", ".DS_Store"}
        return [n for n in names if n in patterns]
    try:
        # shutil.copytree with dirs_exist_ok for incremental sync
        _skip = {".git", ".hg", ".svn", "__pycache__", ".pytest_cache", "venv", ".venv", "node_modules", "logs", ".mypy_cache", ".DS_Store"}
        for item in here.iterdir():
            if item.name in _skip:
                continue
            target = dest / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True, ignore=_ignore)
            else:
                # Skip non-regular files (sockets, pipes, devices)
                if not item.is_file():
                    continue
                try:
                    shutil.copy2(item, target)
                except Exception:
                    pass
        # If source has a .env and workspace lacks one, copy it (for API keys, etc.)
        try:
            src_env = here / ".env"
            dst_env = dest / ".env"
            if src_env.exists() and not dst_env.exists():
                shutil.copy2(src_env, dst_env)
                feed(f"🌊 Ocean: Copied .env to workspace → {dst_env}")
        except Exception:
            pass
        # Write marker
        (dest / ".ocean_workspace").write_text(json.dumps({"source": str(here), "createdAt": datetime.now().isoformat()}, indent=2), encoding="utf-8")
        feed(f"🌊 Ocean: Created/updated workspace at {dest} (source: {here})")
    except Exception as e:
        feed(f"🌊 Ocean: Workspace synchronization warning: {e}")
    # Switch to workspace and rebind roots
    try:
        os.chdir(dest)
        _switch_root(dest)
    except Exception as e:
        feed(f"🌊 Ocean: Failed to switch to workspace: {e}")


def write_log(path: Path, *lines: str) -> None:
    ensure_repo_structure()
    with path.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")


def banner() -> str:
    return (
        "\n"  # leading newline for spacing
        "🌊 Welcome to OCEAN\n"
        "(OCEAN = OCEAN Creates Ex And Nihilo)\n"
        "Multi-Agent Software Engineering Orchestrator\n"
    )


def _slugify(name: str) -> str:
    s = name.strip().lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in {" ", "-", "_"}:
            out.append("-")
    slug = "".join(out).strip("-")
    return slug or "project"


def _load_project_spec() -> Optional[dict]:
    path = DOCS / "project.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_project_spec(data: dict) -> Path:
    ensure_repo_structure()
    out = DOCS / "project.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _load_prd() -> Optional[str]:
    p = DOCS / "prd.md"
    if p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return None
    return None


def _autoprd_from_repo() -> str:
    """Synthesize a PRD from the current git repo and common project files."""
    name = Path.cwd().name
    summary = "Autogenerated from repository contents."
    kind = "web"
    goals: list[str] = []
    constraints: list[str] = []
    tech: list[str] = []

    def read_text(path: Path, limit: int = 100000) -> str:
        try:
            if path.exists():
                return path.read_text(encoding="utf-8", errors="ignore")[:limit]
        except Exception:
            return ""
        return ""

    readme = read_text(ROOT / "README.md")
    if readme:
        # Name from first heading or first non-empty line
        for line in readme.splitlines():
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if line_stripped.startswith("#"):
                name = line_stripped.lstrip("# ").strip() or name
                break
            else:
                summary = line_stripped
                break
        # Summary from first paragraph
        paras = [p.strip() for p in readme.split("\n\n") if p.strip()]
        if paras:
            summary = paras[0].splitlines()[0][:200]

    # Detect kind
    if (ROOT / "backend" / "app.py").exists():
        kind = "web"
    if any((ROOT / d).exists() for d in ["ui", "templates", "static"]):
        kind = "web"
    app_py = read_text(ROOT/"backend"/"app.py")
    if "@app.get" in app_py and "/healthz" in app_py:
        kind = "web"

    # Tech stack indicators
    if (ROOT / "pyproject.toml").exists():
        tech.append("Python/pyproject")
    if (ROOT / "requirements.txt").exists():
        tech.append("requirements.txt")
    if (ROOT / "package.json").exists():
        tech.append("Node/package.json")
    if (ROOT / "Dockerfile").exists():
        tech.append("Dockerfile")
    if (ROOT / ".github" / "workflows").exists():
        tech.append("GitHub Actions")

    # Goals/constraints rough
    if "test" in readme.lower():
        goals.append("testing enabled")
    if "docker" in readme.lower():
        goals.append("containerized")
    compose = read_text(ROOT/"docker-compose.yml")
    if "services:" in compose:
        goals.append("compose staging")
    if "fastapi" in app_py.lower():
        goals.append("fastapi backend")
    if (ROOT/"ui").exists():
        goals.append("static UI")

    lines = [
        f"# {name}",
        "",
        "## Summary",
        summary or "Project initialized under Ocean.",
        "",
        "## Goals",
        *([f"- {g}" for g in goals] if goals else ["- ship", "- reliability", "- clarity"]),
        "",
        "## Constraints",
        *([f"- {c}" for c in constraints] if constraints else ["- minimal dependencies"]),
        "",
        "## Detected",
        f"- Kind: {kind}",
        f"- Tech: {', '.join(tech) if tech else '(unknown)'}",
    ]
    return "\n".join(lines) + "\n"


def _parse_prd(prd_text: str) -> dict:
    """Heuristically parse a PRD into a ProjectSpec-like dict.

    - Title: first markdown heading or first non-empty line
    - One-liner: next non-empty line/paragraph
    - Kind: guess from keywords (web/api/cli)
    - Goals/Constraints: look for sections or bullet lines
    """
    lines = [line.rstrip() for line in prd_text.splitlines()]
    name = "My Project"
    description = ""
    kind = "web"
    goals: list[str] = []
    constraints: list[str] = []

    # Title
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        if line.startswith("#"):
            name = line.lstrip("# ").strip() or name
            start_idx = i + 1
            break
        else:
            name = line.strip()
            start_idx = i + 1
            break
    else:
        start_idx = 0

    # One-liner
    for line in lines[start_idx:]:
        if line.strip():
            description = line.strip()
            break

    blob = prd_text.lower()
    if any(k in blob for k in ["fastapi", "endpoint", "/healthz", "api"]):
        kind = "api"
    if any(k in blob for k in ["ui", "frontend", "web", "html", "css", "react", "vite"]):
        kind = "web"
    if any(k in blob for k in ["cli", "command line", "terminal"]):
        kind = "cli"

    # Collect goals/constraints from sections
    current = None
    for line in lines:
        low = line.lower()
        if low.startswith("## goals") or low.startswith("### goals"):
            current = "goals"
            continue
        if low.startswith("## constraints") or low.startswith("### constraints"):
            current = "constraints"
            continue
        if low.startswith("## "):
            current = None
        if line.strip().startswith("-") and current:
            item = line.lstrip("- ").strip()
            if current == "goals":
                goals.append(item)
            else:
                constraints.append(item)

    return {
        "name": name,
        "kind": kind,
        "description": description,
        "goals": goals,
        "constraints": constraints,
    }


def _prompt_project_directory_if_needed(log: Path) -> None:
    """Interactive: confirm cwd or chdir to a pasted absolute path (piggybacks on chosen LLM cwd)."""
    if _is_test_env():
        return
    if os.getenv("OCEAN_SKIP_REPO_PROMPT", "").lower() in ("1", "true", "yes"):
        return
    try:
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return
    except Exception:
        return

    emit_setup("phase_start", id="project_root")
    cwd = Path.cwd()
    feed(
        "🌊 Ocean: **Project directory** — crew + docs + logs live here. "
        "**Codex / OpenAI / Cursor** (your pick in the next step) does the coding; Ocean routes work there."
    )
    feed(f"🌊 Ocean: Current directory: {cwd}")
    emit_setup(
        "question",
        id="project_root",
        message="Confirm or change project root",
        choices=["1", "2"],
    )
    choice = _ask(
        "[1] Use current directory  |  [2] Paste absolute path to another project",
        default="1",
        choices=["1", "2"],
    )
    emit_setup("answer", id="project_root", choice=choice)
    if choice == "1":
        feed("🌊 Ocean: Using current directory.")
        emit_setup("phase_end", id="project_root")
        return

    raw = _ask("Absolute path to project root (no quotes)", default="").strip()
    if not raw:
        feed("🌊 Ocean: Empty path — staying in current directory.")
        emit_setup("phase_end", id="project_root")
        return
    dest = Path(raw).expanduser().resolve()
    if not dest.is_dir():
        feed(f"🌊 Ocean: Not a directory: {dest} — staying in {cwd}")
        emit_setup("phase_end", id="project_root")
        return
    try:
        os.chdir(dest)
        _switch_root(dest)
        ensure_repo_structure()
        feed(f"🌊 Ocean: Project root → {dest}")
        write_log(log, "[OCEAN] Switched project root", str(dest))
    except Exception as e:
        feed(f"🌊 Ocean: Could not switch root: {e}")
    emit_setup("phase_end", id="project_root")


def _noninteractive_prompt_answer(default: str, choices: Optional[list[str]]) -> str:
    """Fallback when stdin is not a real teletype (CI, pipes, agent runners)."""
    if default:
        return default
    if choices:
        return choices[0]
    return ""


def _ask(label: str, default: str = "", choices: Optional[list[str]] = None) -> str:
    """Robust prompt helper.

    - Uses Rich Prompt under pytest / ``OCEAN_TEST`` so tests can monkeypatch ``Prompt.ask``.
    - Uses defaults when stdin is not a TTY outside tests (no Rich ``Aborted`` on EOF).
    - Uses Typer's prompt in normal interactive runs for better TTY behavior.
    - Validates choices if provided.
    """
    import os as _os

    # If questions disabled globally, return default immediately
    if os.getenv("OCEAN_ALLOW_QUESTIONS", "1") in ("0", "false", "False"):
        if default:
            return default
        # Choose first choice if provided, else empty string
        return (choices[0] if choices else "") if choices else ""

    # Pytest harness: Rich Prompt stays monkeypatch-friendly.
    if _is_test_env():
        return Prompt.ask(label, default=default, choices=choices)

    # Non-interactive stdin: avoid Rich Prompt (EOF prints "Aborted." and exits).
    if not sys.stdin.isatty():
        return _noninteractive_prompt_answer(default, choices)

    # Simple combined-feed mode: inline prompt using input() with a consistent prefix
    if _os.getenv("OCEAN_SIMPLE_FEED") == "1":
        # Print label as a feed line, then show a single-line You> prompt
        console.print(f"[bold blue]🌊 OCEAN:[/bold blue] {label}")
        hint = f" (default: {default})" if default else ""
        if choices:
            console.print(f"[dim]Choices: {', '.join(choices)}[/dim]")
        try:
            ans = input("You> ").strip()
        except EOFError:
            ans = ""
        if not ans:
            ans = default
        else:
            you_say(ans)
        if choices and ans not in choices:
            console.print(f"[yellow]Please choose one of: {', '.join(choices)}[/yellow]")
            return _ask(label, default, choices)
        return ans

    # Build label with choices hint if provided
    hint = f" [choices: {', '.join(choices)}]" if choices else ""
    while True:
        try:
            ans = typer.prompt(f"{label}{hint}", default=default)
        except (EOFError, Abort):
            ans = _noninteractive_prompt_answer(default, choices)
        if choices and ans not in choices:
            console.print(f"[yellow]Please choose one of: {', '.join(choices)}[/yellow]")
            continue
        return ans


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(None, "--version", help="Show version and exit", is_eager=True),
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Show detailed agent and orchestration steps"),
    ask: bool = typer.Option(True, "--ask/--no-ask", help="Allow agents to ask the user clarifying questions"),
    style: str = typer.Option("max", "--style", help="Persona style intensity: 'max' or 'low'", show_default=True),
    no_ui: bool = typer.Option(False, "--no-ui", help="Run in streaming mode (no full-screen UI)"),
    feed: bool = typer.Option(True, "--feed/--no-feed", help="Combine output and prompts in a single feed (no spinners)", show_default=True),
):
    if version:
        rprint(f"ocean {__version__}")
        raise typer.Exit(code=0)
    # Disable Rich styling in feed mode to avoid spacing issues
    os.environ.setdefault("RICH_NO_COLOR", "1")
    os.environ.setdefault("RICH_DISABLE", "1")
    # Propagate verbosity to subprocess-aware modules
    os.environ["OCEAN_VERBOSE"] = "1" if verbose else "0"
    os.environ["OCEAN_ALLOW_QUESTIONS"] = (
        "0" if not ask else os.environ.get("OCEAN_ALLOW_QUESTIONS", "1")
    )
    # Persona style toggle (default: max)
    s = (style or "max").strip().lower()
    if s not in {"max", "low"}:
        s = "max"
    os.environ["OCEAN_STYLE"] = s
    if no_ui:
        os.environ["OCEAN_NO_UI"] = "1"
    if feed:
        os.environ["OCEAN_SIMPLE_FEED"] = "1"
        # Dynamic Codex mode; allow API fallback if available
        os.environ.pop("OCEAN_FORCE_CODEX", None)
        # Disable CrewAI integration to keep flow simple and local
        os.environ.setdefault("OCEAN_USE_CREWAI", "0")
        # Use existing PRD if present; only synthesize from repo when there is none
        os.environ.setdefault("OCEAN_REFRESH_PRD", "0")
    else:
        os.environ.pop("OCEAN_SIMPLE_FEED", None)

    # Always activate a safe workspace when running outside the Ocean home repo
    try:
        _prepare_workspace_from_cwd()
    except Exception:
        # Non-fatal; proceed in-place if workspace prep fails
        pass

    if ctx.invoked_subcommand is None:
        from .core.loop import run as _run_loop
        _run_loop(cwd=ROOT)


@app.command(help="Run onboarding: codegen → credentials → crew → clarify → planning → staging")
def chat(
    prd: Optional[str] = typer.Option(None, "--prd", help="Path to PRD file or '-' to read from stdin"),
    stage: bool = typer.Option(True, "--stage/--no-stage", help="Auto-deploy to local staging after build"),
    prod: bool = typer.Option(False, "--prod", help="Prepare for production and pause before go-live"),
):
    """Main interactive conversation flow"""
    ensure_repo_structure()
    # Load environment from local .env if present (e.g., BRAVE_API_KEY)
    _hydrate_tokens()
    _load_env_file(ROOT / ".env")
    try:
        key = os.getenv("OPENAI_API_KEY")
        if key and os.getenv("OCEAN_APIKEY_ANNOUNCED") != "1":
            masked = (key[:6] + "…") if len(key) > 6 else "(set)"
            feed(f"🌊 Ocean: OPENAI_API_KEY detected (len={len(key)}, prefix={masked})")
            os.environ["OCEAN_APIKEY_ANNOUNCED"] = "1"
    except Exception:
        pass

    # Create session log
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = LOGS / f"session-{timestamp}.log"
    write_log(log, "OCEAN session started", datetime.now().isoformat())
    # Create structured events file (feed / integrations)
    events_file = LOGS / f"events-{timestamp}.jsonl"
    os.environ["OCEAN_EVENTS_FILE"] = str(events_file)
    try:
        events_file.touch(exist_ok=True)
    except Exception:
        pass

    _prompt_project_directory_if_needed(log)

    try:
        from . import setup_flow as _setup_flow

        _repo_hint = _setup_flow.resolve_ocean_repo_root()
        if (
            _repo_hint.resolve() == Path.cwd().resolve()
            and not _is_test_env()
            and os.getenv("OCEAN_SKIP_AUTO_SETUP", "").lower() not in ("1", "true", "yes")
        ):
            _code = _setup_flow.ensure_smart(
                _repo_hint,
                console=console,
                notify=feed_line,
                full_pytest=False,
                prefer_venv=True,
            )
            if _code != 0:
                feed_line(f"🌊 Ocean: Automatic dev setup reported exit code {_code}.")
    except RuntimeError:
        pass

    emit_setup("phase_start", id="welcome")
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        _auto_self_update_and_version()
        feed("🌊 Ocean: Ahoy! I'm Ocean — caffeinated and ready to ship.")
        feed(f"🌊 Ocean: Workspace: {Path.cwd()}")
        feed(
            "🌊 Ocean: **You drive goals.** I run the crew, timing, and token budget—you never orchestrate specialists yourself."
        )
        feed(
            "🌊 Ocean: Each crewmate has voicing + skills in docs/personas.yaml — emoji lines in chat show who’s speaking."
        )
    else:
        console.print(banner())
        console.print(
            "\n[bold blue]🌊 OCEAN:[/bold blue] Hello! We'll pick where codegen runs, sign you in when needed, "
            "meet the crew, then capture what you're building.\n"
        )
    emit_setup("phase_end", id="welcome")

    emit_setup("phase_start", id="backend_choice")
    emit_setup("info", id="codegen_backend_probes", probe=probe_snapshot(Path.cwd()))
    emit_setup(
        "question",
        id="codegen_backend",
        message="Pick coding brain (LLM / IDE path)",
        choices=sorted(VALID_BACKENDS),
    )
    try:
        _bk_choice = prompt_codegen_backend_if_needed(Path.cwd())
        feed(f"🌊 Ocean: Codegen backend → {_bk_choice}")
        emit_setup("answer", id="codegen_backend", codegen_backend=_bk_choice)
    except Exception:
        _bk_choice = get_codegen_backend()
    emit_setup("phase_end", id="backend_choice")

    token_budget.feed_status_if_needed(feed)

    _run_setup_credentials(get_codegen_backend())

    emit_setup("phase_start", id="model_choice")
    emit_setup(
        "question",
        id="codegen_model",
        message="Pick API model (OpenAI / Gemini backends only; stored in docs/ocean_prefs.json)",
    )
    try:
        _bk_for_model = get_codegen_backend()
        _model_pick = prompt_codegen_model_if_needed(_bk_for_model, Path.cwd())
        if _model_pick:
            feed(f"🌊 Ocean: Codegen model → {_model_pick}")
            emit_setup("answer", id="codegen_model", model=_model_pick, codegen_backend=_bk_for_model)
    except Exception:
        pass
    emit_setup("phase_end", id="model_choice")

    if not _is_test_env():
        try:
            from .brain_client import early_brain_enabled, fetch_early_loop_brain_text

            if early_brain_enabled():
                tip = fetch_early_loop_brain_text(cwd=ROOT, timeout=20.0)
                if tip:
                    feed("🌊 Ocean: Early brain (doctrine → next focus):")
                    for raw in tip.splitlines():
                        line = raw.strip()
                        if line:
                            feed(f"   {line}")
        except Exception:
            pass

    _codex_startup_needed = get_codegen_backend() == "codex"

    if not _external_startup_disabled():
        MCP.ensure_started(log)
    # Ensure project-level venv for convenience
    _ensure_root_venv()
    # Warm up Codex session early so codegen runs without delays (Codex backend only)
    if _codex_startup_needed:
        _warmup_codex()
    # Quick e2e probe when using Codex CLI backend
    if _codex_startup_needed and not _external_startup_disabled():
        try:
            ok, detail, category = _codex_e2e_test(timeout=8)
        except Exception:
            ok, detail, category = False, "unknown error", None
        if not ok:
            hint = ""
            if category == "quota_billing":
                hint = " Possible quota or billing limit — check your Codex/OpenAI account."
            elif category == "rate_limit":
                hint = " Rate limited — retry later."
            elif category == "auth_permission":
                hint = " Auth or permission issue — try `codex auth login`."
            loose = (
                os.getenv("OCEAN_LOOSE_CODEX") in ("1", "true", "True")
                or os.getenv("OCEAN_STRICT_CODEX") in ("0", "false", "False")
            )
            if loose:
                feed(
                    f"🌊 Ocean: ⚠️ Codex exec probe failed ({category or 'unknown'}) — {detail}.{hint} "
                    "Continuing (OCEAN_LOOSE_CODEX=1)."
                )
            else:
                feed(
                    f"🌊 Ocean: ❌ Codex exec unavailable — {detail}.{hint} "
                    "Fix auth/quota or switch backend (docs/ocean_prefs.json). "
                    "Set OCEAN_LOOSE_CODEX=1 to continue anyway. Aborting."
                )
                raise typer.Exit(code=2)
    # In feed mode we require Codex for codegen phases; errors are surfaced during plan/execute
    if not _external_startup_disabled():
        MCP.status()

    # If PRD provided, persist to docs/prd.md
    if prd:
        prd_text = None
        if prd == "-":
            console.print("[bold blue]🌊 OCEAN:[/bold blue] Paste your PRD content. Press Ctrl-D (Ctrl-Z on Windows) when done.\n")
            prd_text = sys.stdin.read()
        else:
            prd_path = Path(prd)
            if prd_path.exists():
                prd_text = prd_path.read_text(encoding="utf-8")
            else:
                console.print(f"[yellow]⚠️ PRD file not found: {prd_path}[/yellow]")
        if prd_text:
            (DOCS / "prd.md").write_text(prd_text, encoding="utf-8")
            write_log(log, "[OCEAN] PRD saved to docs/prd.md", f"[OCEAN] PRD length: {len(prd_text)} chars")
    
    emit_setup("phase_start", id="crew_intro")
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: Assembling the crew…")
        _do_crew(log)
    else:
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Here's your engineering crew.\n")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task_c = progress.add_task("OCEAN is assembling the crew...", total=None)
            _do_crew(log)
            progress.update(task_c, completed=True, description="✅ OCEAN assembled the crew")
    emit_setup("phase_end", id="crew_intro")

    emit_setup("phase_start", id="project_clarify")
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: Consulting with Moroni (Architect)…")
    else:
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Let's capture what you're building.")
        console.print("[dim]OCEAN is consulting with Moroni (Architect)…[/dim]")
    _do_clarify(log)
    emit_setup("phase_end", id="project_clarify")

    spec_after = _load_project_spec()
    if spec_after and os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed(f"🌊 Ocean: Project locked in → {spec_after.get('name', '?')}")

    # Optional CrewAI orchestration path (legacy). When OCEAN_CREWAI_BY_MORONI=1 (default),
    # Moroni will initialize CrewAI during agent execution instead of the CLI doing it here.
    if (
        (not _is_test_env())
        and (os.getenv("OCEAN_USE_CREWAI", "1") not in ("0", "false", "False"))
        and (os.getenv("OCEAN_CREWAI_BY_MORONI", "1") in ("0", "false", "False"))
    ):
        prd_text = _load_prd() or ""
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] CrewAI mode enabled — orchestrating agents via CrewAI while Codex writes code…")
        try:
            # Ensure MCP instances exist for agents
            for agent_name in ("Moroni", "Q", "Edna", "Mario"):
                MCP.start_for_agent(agent_name, LOGS)
            from .crewai_adapter import CrewRunner
            runner = CrewRunner()
            runner.run_project(prd_text)
            console.print("✅ [bold blue]🌊 OCEAN:[/bold blue] Crew completed initial deliverables via Codex MCP.")
        except Exception as e:
            console.print(f"[red]❌ CrewAI integration failed: {e}[/red]")
            raise typer.Exit(code=1)
        console.print("🔗 Use 'ocean provision' for a workspace with Docker + venv.")
        return

    # Non-interactive phases: either spinner (default) or combined-feed prints (simple feed)
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        if _is_test_env():
            feed("🌊 Ocean: Test mode: skipping planning and execution.")
            feed("🌊 Ocean: Session complete.")
            feed(f"📝 Session log: {log}")
            return
        # Proceed with planning and execution, but keep Codex disabled in feed
        feed("🌊 Ocean: Creating your project plan…")
        # Preflight codegen readiness (depends on saved backend)
        _be_preflight = get_codegen_backend()
        if _be_preflight == "openai_api":
            if not os.getenv("OPENAI_API_KEY"):
                feed("🌊 Ocean: ❌ Backend openai_api requires OPENAI_API_KEY.")
                raise typer.Exit(code=1)
            feed("🌊 Ocean: Preflight: using OpenAI API backend (skipping Codex CLI check).")
        elif _be_preflight == "gemini_api":
            if not (os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()):
                feed("🌊 Ocean: ❌ Backend gemini_api requires GEMINI_API_KEY or GOOGLE_API_KEY.")
                raise typer.Exit(code=1)
            feed("🌊 Ocean: Preflight: using Gemini API backend (skipping Codex CLI check).")
        elif _be_preflight in ("cursor_handoff", "dry_plan_only"):
            feed(f"🌊 Ocean: Preflight: backend={_be_preflight} (skipping Codex execution readiness).")
        elif os.getenv("OCEAN_DISABLE_CODEX") not in ("1", "true", "True"):
            try:
                from . import codex_client as _cc
                st = _cc.check()
                if not st.ok:
                    feed("🌊 Ocean: Attempting Codex auth…")
                    _ensure_codex_auth()
                    st = _cc.check()
                if not st.ok:
                    feed("🌊 Ocean: ❌ Codex not ready — install/login or set OPENAI_API_KEY.")
                    raise typer.Exit(code=1)
                else:
                    mode = st.mode
                    feed(f"🌊 Ocean: Codex ready (mode: {mode}).")
            except typer.Exit:
                raise
            except Exception:
                # If preflight check fails unexpectedly, proceed and let execution handle errors
                pass
        try:
            _do_plan(log)
        except Exception as e:
            feed(f"🌊 Ocean: ❌ Execution failed — {e}")
            raise typer.Exit(code=1)
        feed("🌊 Ocean: Session complete.")
        feed(f"📝 Session log: {log}")
        return
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if _is_test_env():
                console.print("[dim]Test mode: skipping planning and execution.[/dim]")
                console.print("\n🎉 [green]OCEAN has completed your project setup![/green]")
                console.print(f"📝 Session log: [blue]{log}[/blue]")
                return

            task3 = progress.add_task("OCEAN is creating your project plan...", total=None)
            _do_plan(log)
            progress.update(task3, completed=True, description="✅ OCEAN created your plan")
    
    console.print("\n🎉 [green]OCEAN has completed your project setup![/green]")
    console.print(f"📝 Session log: [blue]{log}[/blue]")
    console.print("📋 Project spec: [blue]docs/project.json[/blue]")
    console.print("📋 Backlog: [blue]docs/backlog.json[/blue]")
    console.print("📋 Plan: [blue]docs/plan.md[/blue]")
    console.print("\n🌊 [bold blue]OCEAN:[/bold blue] Your AI engineering team is ready!")
    console.print("💡 Tip: Use 'ocean provision' to create an isolated workspace under 'projects/'.")

    # Auto-stage by default using Docker Compose (fallback to local runtime inside deploy)
    try:
        deploy(dry_run=False)  # type: ignore[arg-type]
    except SystemExit:
        # deploy exits via typer.Exit; ignore here
        pass


@app.command(name="mcp-server", help="Run Ocean as a stdio MCP server for Cursor/Codex")
def mcp_server():
    """Expose Ocean's product loop as MCP tools over stdio."""
    from .mcp_server import main as run_mcp_server

    run_mcp_server()


def _do_clarify(log: Path) -> None:
    """OCEAN consults with Moroni to clarify the project vision"""
    ensure_repo_structure()
    
    feed("🌊 Ocean: Preparing project context…")
    prd = None
    # Force refresh if requested (default in feed/workspace mode)
    if os.getenv("OCEAN_REFRESH_PRD") not in ("0", "false", "False"):
        feed("🌊 Ocean: Synthesizing PRD from repository context…")
        prd = _autoprd_from_repo()
        (DOCS/"prd.md").write_text(prd, encoding="utf-8")
        write_log(log, "[OCEAN] PRD synthesized from repo (refresh)", f"[OCEAN] PRD length: {len(prd)}")
    else:
        prd = _load_prd()
        if not prd:
            feed("🌊 Ocean: No PRD found — synthesizing from repo…")
            prd = _autoprd_from_repo()
            (DOCS/"prd.md").write_text(prd, encoding="utf-8")
            write_log(log, "[OCEAN] PRD synthesized from repo", f"[OCEAN] PRD length: {len(prd)}")
    if prd:
        (DOCS / "prd.md").write_text(prd, encoding="utf-8")
        write_log(log, "[OCEAN] PRD captured to docs/prd.md", f"[OCEAN] PRD length: {len(prd)}")

    inferred = _parse_prd(prd or "")
    name = inferred.get("name") or _ask("📝 🌊 OCEAN: Project name — What should we call this project?", default="My Project")
    kind = inferred.get("kind") or _ask(
        "🏗️ 🌊 OCEAN: Project type — What type of project is this?",
        choices=["web", "api", "cli", "mobile", "desktop"],
        default="web",
    )
    description = inferred.get("description") or _ask("💭 🌊 OCEAN: Short description — Can you describe it in one line?", default="")
    goals = ", ".join(inferred.get("goals") or []) or _ask("🎯 🌊 OCEAN: Goals — What are the primary goals?", default="prototype, learn, ship")
    constraints = ", ".join(inferred.get("constraints") or []) or _ask("⚠️ 🌊 OCEAN: Constraints — Any constraints I should know about?", default="")

    name_s = name.strip()
    desc_s = description.strip()
    goals_list = [g.strip() for g in goals.split(",") if g.strip()]
    vision_default = (
        os.getenv("OCEAN_DEFAULT_VISION", "").strip()
        or desc_s
        or (goals_list[0] if goals_list else "")
        or "Ship a focused, high-quality version of this product."
    )
    ai_id_default = os.getenv("OCEAN_DEFAULT_AI_IDENTITY", "").strip() or (
        f"Your coding partner on **{name_s or 'this project'}** — "
        "Ocean runs the crew and timing; you steer goals and say when we're done."
    )
    _no_extra_questions = _is_test_env() or os.getenv("OCEAN_ALLOW_QUESTIONS", "1") in ("0", "false", "False")
    if _no_extra_questions:
        vision = vision_default
        ai_identity = ai_id_default
    else:
        vision = _ask(
            "🔭 🌊 OCEAN: Vision — In one sentence, what does “done” look like?",
            default=vision_default,
        ).strip()
        ai_identity = _ask(
            "🤖 🌊 OCEAN: Who is the AI to you? (tone / role — Ocean still routes specialists)",
            default=ai_id_default,
        ).strip()

    spec = {
        "name": name_s,
        "kind": kind.strip().lower(),
        "description": desc_s,
        "goals": goals_list,
        "constraints": [c.strip() for c in constraints.split(",") if c.strip()],
        "vision": vision,
        "ai_identity": ai_identity,
        "createdAt": datetime.now().isoformat(),
    }
    
    # Basic validation
    errors: list[str] = []
    if not spec["name"]:
        errors.append("name must be non-empty")
    if spec["kind"] not in {"web", "api", "cli", "mobile", "desktop"}:
        errors.append("kind must be one of: web, api, cli, mobile, desktop")
    if not isinstance(spec.get("goals", []), list):
        errors.append("goals must be a list")
    if not isinstance(spec.get("constraints", []), list):
        errors.append("constraints must be a list")

    if errors:
        console.print("[red]❌ Invalid project spec:[/red] " + "; ".join(errors))
        write_log(log, "[OCEAN] Clarification failed: invalid spec", json.dumps({"errors": errors}))
        raise typer.Exit(code=1)

    out = _save_project_spec(spec)
    write_log(
        log,
        "[OCEAN] Moroni completed clarification.",
        json.dumps(spec),
        f"[OCEAN] Summary: name={spec['name']}, kind={spec['kind']}, goals={len(spec['goals'])}",
    )
    
    feed("🌊 Ocean: ✅ Moroni has clarified your vision.")
    
    # Show summary (compact in feed mode)
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed(f"🌊 Ocean: Summary — Name: {spec['name']}")
        feed(f"🌊 Ocean: Summary — Type: {spec['kind']}")
        if spec.get("description"):
            feed(f"🌊 Ocean: Summary — Description: {spec['description']}")
        if spec.get("goals"):
            feed(f"🌊 Ocean: Summary — Goals: {', '.join(spec['goals'])}")
        if spec.get("constraints"):
            feed(f"🌊 Ocean: Summary — Constraints: {', '.join(spec['constraints'])}")
        if spec.get("vision"):
            feed(f"🌊 Ocean: Summary — Vision: {spec['vision']}")
        if spec.get("ai_identity"):
            feed(f"🌊 Ocean: Summary — AI identity: {spec['ai_identity']}")
    else:
        table = Table(title="📋 Project Summary (from Moroni's analysis)")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Name", spec["name"])
        table.add_row("Type", spec["kind"])
        table.add_row("Description", spec["description"])
        table.add_row("Goals", ", ".join(spec["goals"]))
        if spec["constraints"]:
            table.add_row("Constraints", ", ".join(spec["constraints"]))
        if spec.get("vision"):
            table.add_row("Vision", spec["vision"])
        if spec.get("ai_identity"):
            table.add_row("AI identity", spec["ai_identity"])
        console.print(table)
    feed(f"🌊 Ocean: Moroni saved your project spec to {out}")


def _do_crew(log: Path) -> None:
    """OCEAN assembles and introduces the crew.

    If ``docs/project.json`` is missing (e.g. before Moroni clarify), uses the
    current directory name as a display label only — nothing is written to disk.
    """
    ensure_repo_structure()
    spec = _load_project_spec()
    if not spec:
        label = Path.cwd().name or "this workspace"
        spec = {
            "name": label,
            "kind": "cli",
            "description": "",
            "goals": [],
            "constraints": [],
            "createdAt": datetime.now().isoformat(),
        }
        feed("🌊 Ocean: Introducing the crew — we’ll lock in your project details next.")

    write_log(log, "[OCEAN] Assembling crew for project:", json.dumps(spec))
    
    feed(f"🌊 Ocean: Assembling the crew for '{spec['name']}'…")
    feed("🌊 Ocean: Each agent brings unique expertise to your project…")
    
    crew_lines: list[tuple[str, str, str]] = []
    for agent in default_agents():
        intro_full = agent.introduce()
        feed_agent_say(agent.name, agent.introduce_detail())
        for vx in agent_voice_skills_chat_lines(agent.name, search_start=ROOT):
            ich = AGENT_EMOJI.get(agent.name, "🤖")
            feed_line(f"   {ich} · {vx}")
        write_log(log, intro_full)
        summary = CREW_SUMMARY.get(agent.name)
        if summary:
            role_sp, spec_sp = summary
            crew_lines.append((agent.name, role_sp, spec_sp))
    if os.getenv("OCEAN_SIMPLE_FEED") != "1":
        crew_table = Table(title="🤖 The OCEAN Crew (Assembled by OCEAN)")
        crew_table.add_column("Agent", style="cyan", no_wrap=True)
        crew_table.add_column("Role", style="blue")
        crew_table.add_column("Specialty", style="green")
        for a, r, s in crew_lines:
            crew_table.add_row(a, r, s)
        console.print(crew_table)
    else:
        for a, r, s in crew_lines:
            feed(f"🌊 Ocean: Crew — {a}: {r} — {s}")
    feed("🌊 Ocean: Crew assembled ✅ — I’ll route work to them; you don’t manage the roster.")


def _do_plan(log: Path) -> None:
    """OCEAN coordinates the crew to generate project plan and backlog"""
    spec_dict = _load_project_spec()
    if not spec_dict:
        console.print("[yellow]⚠️ No project spec found. Run 'ocean clarify' first.[/yellow]")
        raise typer.Exit(code=1)
    
    spec = ProjectSpec.from_dict(spec_dict)
    
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: Now let me coordinate my crew to create your project plan…")
        feed("🌊 Ocean: Moroni, Q, Edna, and Mario are analyzing your requirements…")
    else:
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Now let me coordinate my crew to create your project plan...")
        console.print("[bold blue]🌊 OCEAN:[/bold blue] Moroni, Q, Edna, and Mario are analyzing your requirements...")
    
    # Generate backlog from agent proposals
    backlog = generate_backlog(spec)
    
    # EXECUTE the backlog using agent capabilities
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: My crew is now EXECUTING your project tasks…")
    else:
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] My crew is now EXECUTING your project tasks...")
    bj, pm, runtime_summary = execute_backlog(backlog, DOCS, spec)
    
    write_log(log, f"[OCEAN] Crew completed planning and execution: {bj}")
    
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: Excellent! My crew has created AND BUILT your project!")
        feed(f"🌊 Ocean: Backlog: {bj}")
        feed(f"🌊 Ocean: Plan summary: {pm}")
        if runtime_summary:
            feed(f"🌊 Ocean: Local runtime: {runtime_summary}")
    else:
        console.print("✅ [bold blue]🌊 OCEAN:[/bold blue] Excellent! My crew has created AND BUILT your project!")
        console.print(f"✅ [bold blue]🌊 OCEAN:[/bold blue] Backlog: {bj}")
        console.print(f"✅ [bold blue]🌊 OCEAN:[/bold blue] Plan summary: {pm}")
        if runtime_summary:
            console.print(f"🌐 [bold blue]🌊 OCEAN:[/bold blue] Local runtime: [green]{runtime_summary}[/green]")
        write_log(log, f"[OCEAN] Runtime: {runtime_summary}")
    
    # Show backlog summary
    if os.getenv("OCEAN_SIMPLE_FEED") != "1":
        backlog_table = Table(title="📋 Project Backlog (EXECUTED by OCEAN's Crew)")
        backlog_table.add_column("Task", style="cyan")
        backlog_table.add_column("Owner", style="blue")
        backlog_table.add_column("Files", style="green")
        for task in backlog:
            files_str = ", ".join(task.files_touched) if task.files_touched else "None"
            backlog_table.add_row(task.title, task.owner, files_str)
        console.print(backlog_table)
    else:
        for task in backlog:
            files_str = ", ".join(task.files_touched) if task.files_touched else "None"
            feed(f"🌊 Ocean: Backlog — [{task.owner}] {task.title} — {files_str}")
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: Your project is now fully planned, built, and ready!")
    else:
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Your project is now fully planned, built, and ready!")
    if runtime_summary:
        console.print(f"🔗 [green]Open: {runtime_summary}[/green]")

    # Auto-provision workspace for web/api projects
    if spec.kind in ("web", "api"):
        _provision_workspace(spec.name)
        # Persist state
        slug = _slugify(spec.name)
        state_path = PROJECTS / slug / "state.json"
        data = {
            "name": spec.name,
            "kind": spec.kind,
            "runtime": runtime_summary,
            "createdAt": datetime.now().isoformat(),
        }
        state_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


@app.command(help="Ask clarifying questions and save docs/project.json")
def clarify():
    """Project clarification with Moroni"""
    log = session_log_path()
    _load_env_file(ROOT / ".env")
    _do_clarify(log)


@app.command(help="Print agent introductions and log them")
def crew():
    """Show the OCEAN crew"""
    log = session_log_path()
    _do_crew(log)


@app.command(help="First-run dev setup: venv, pip install -e ., pytest, then doctor")
def onboard(
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip pytest"),
    skip_venv: bool = typer.Option(False, "--skip-venv", help="Use current interpreter only (no venv/)"),
):
    """Prepare local Python env and verify tests before using Codex/chat."""
    ensure_repo_structure()
    try:
        from . import setup_flow as _setup_flow

        repo = _setup_flow.resolve_ocean_repo_root()
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(2)
    code = _setup_flow.run_dev_ready(repo, console=console, skip_tests=skip_tests, skip_venv=skip_venv)
    if code != 0:
        raise typer.Exit(code)
    _run_doctor_quick(full=False)
    console.print("\n[cyan]Next:[/cyan] [bold]ocean[/bold] or [bold]ocean chat[/bold].")


@app.command(help="Generate/refresh scaffolds for backend, UI, CI, docs")
def init(
    setup: bool = typer.Option(False, "--setup", help="Dev setup: venv, pip install -e ., pytest, then doctor"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
):
    """Generate project scaffolds using AI agents"""
    ensure_repo_structure()
    if setup:
        try:
            from . import setup_flow as _setup_flow

            repo = _setup_flow.resolve_ocean_repo_root()
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(2)
        code = _setup_flow.run_dev_ready(repo, console=console, skip_tests=False, skip_venv=False)
        if code != 0:
            raise typer.Exit(code)
        _run_doctor_quick(full=False)
        console.print("\n[cyan]Next:[/cyan] [bold]ocean[/bold] or [bold]ocean chat[/bold] for the SDLC flow.")
        return

    console.print("[bold blue]🌊 OCEAN:[/bold blue] This command is deprecated!")
    console.print("[bold blue]🌊 OCEAN:[/bold blue] Run 'ocean' to start the full AI-powered experience.")
    console.print("[bold blue]🌊 OCEAN:[/bold blue] My agents will generate and execute everything automatically.")
    
    # If force is specified, run the full chat flow
    if force:
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Starting full AI-powered project generation...")
        chat()
    else:
        console.print("\n💡 Tip: Use 'ocean' (no args) for the full experience, or 'ocean clarify' to start.")


def _provision_workspace(proj_name: str) -> Path:
    """Internal helper to create a workspace folder with runtime helpers and DB."""
    ensure_repo_structure()
    slug = _slugify(proj_name)
    dest = PROJECTS / slug
    dest.mkdir(parents=True, exist_ok=True)

    # Copy artifacts if present
    for src_dir_name in ("backend", "ui", "devops"):
        src = ROOT / src_dir_name
        if src.exists():
            shutil.copytree(src, dest / src_dir_name, dirs_exist_ok=True)

    # Create data directory and simple SQLite DB
    data_dir = dest / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "app.db"
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("create table if not exists kv (k text primary key, v text)")
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Create .env and README in workspace
    (dest / ".env").write_text(
        "PORT=8000\nENV=development\n# Optional: export Codex auth for in-container use\n# CODEX_AUTH_TOKEN=\n",
        encoding="utf-8",
    )
    (dest / "README.md").write_text(
        f"# {proj_name} Workspace\n\nThis workspace was provisioned by OCEAN.\n\n- Backend: ./backend\n- UI: ./ui\n- DevOps: ./devops\n- Data (SQLite): ./data/app.db\n\nUse ./run.sh to start locally.\n",
        encoding="utf-8",
    )

    # Create run.sh helper
    run_sh = dest / "run.sh"
    run_sh.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Create venv if missing
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate

# Install deps for backend if present
if [ -d backend ]; then
  python -m pip install --upgrade pip >/dev/null
  pip install fastapi[all] uvicorn >/dev/null
fi

# Start backend
if [ -d backend ]; then
  (uvicorn backend.app:app --host 127.0.0.1 --port 8000 &)
  BACK_PID=$!
  echo "Backend: http://127.0.0.1:8000/healthz (pid $BACK_PID)"
fi

# Serve UI if present
if [ -d ui ]; then
  python -m http.server 5173 -d ui &
  UI_PID=$!
  echo "UI: http://127.0.0.1:5173 (pid $UI_PID)"
fi

wait
""",
        encoding="utf-8",
    )
    run_sh.chmod(0o755)

    # Proactively create workspace venv and install runtime deps
    venv_path = dest / "venv"
    _create_venv(venv_path)
    pip = venv_path / "bin" / "pip"
    if pip.exists():
        # Quiet installs and write outputs to a workspace log file
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y%m%d-%H%M%S")
        wlogs = dest / "logs"
        try:
            wlogs.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        pip_log = wlogs / f"pip-install-{ts}.log"
        def _pip(cmd: list[str]) -> None:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
                try:
                    with pip_log.open("a", encoding="utf-8") as f:
                        f.write("$ " + " ".join(cmd) + "\n")
                        if res.stdout:
                            f.write(res.stdout)
                        if res.stderr:
                            f.write("\n[stderr]\n" + res.stderr)
                        f.write("\n")
                except Exception:
                    pass
            except Exception:
                pass
        _pip([str(pip), "install", "--upgrade", "pip"])
        _pip([str(pip), "install", "fastapi[all]", "uvicorn"])

    # Docker assets
    (dest / ".dockerignore").write_text(
        ".venv\nvenv\n__pycache__\n*.pyc\nlogs\n*.egg-info\n.env\n",
        encoding="utf-8",
    )
    (dest / "Dockerfile").write_text(
        """# Backend image
FROM python:3.11-slim
WORKDIR /app

# Install runtime deps
RUN python -m pip install --upgrade pip \
    && pip install fastapi[all] uvicorn

# Copy backend only
COPY backend ./backend

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        encoding="utf-8",
    )
    (dest / "docker-compose.yml").write_text(
        """version: "3.9"
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app/backend:ro
    env_file:
      - .env
    environment:
      - ENV=development
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 5s
      timeout: 2s
      retries: 10
  ui:
    image: nginx:alpine
    ports:
      - "5173:80"
    volumes:
      - ./ui:/usr/share/nginx/html:ro
    depends_on:
      - backend
""",
        encoding="utf-8",
    )
    return dest


@app.command(help="Provision an isolated project workspace in projects/<slug>")
def provision(name: Optional[str] = typer.Option(None, "--name", help="Project name (defaults to docs/project.json)")):
    """Create projects/<slug> with backend/ui/devops, venv, and a simple DB."""
    spec = _load_project_spec()
    if not spec and not name:
        console.print("[yellow]⚠️ No project spec found. Provide --name or run 'ocean clarify' first.[/yellow]")
        raise typer.Exit(code=1)
    proj_name = name or spec.get("name", "My Project")
    dest = _provision_workspace(proj_name)
    console.print(f"✅ [green]Workspace provisioned[/green]: {dest}")
    console.print("🔗 Open: http://127.0.0.1:8000/healthz | http://127.0.0.1:5173")


@app.command(name="bench", help="Bench harness: clone/copy repo, trace decisions, evidence logs/bench-*")
def bench(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print plan only; no clone or pipeline"),
    list_repos: bool = typer.Option(False, "--list", "-l", help="List allowlisted repos and exit"),
    i_understand_network: bool = typer.Option(
        False,
        "--i-understand-network",
        help="Consent to git clone from network (or set OCEAN_BENCH_NETWORK=1)",
    ),
    repo_url: Optional[str] = typer.Option(None, "--repo-url", help="Clone this URL instead of allowlist pick"),
    repo_path: Optional[str] = typer.Option(None, "--repo-path", help="Copy this local directory into an isolated bench workspace"),
    run_codegen: bool = typer.Option(True, "--codegen/--no-codegen", help="Call LLM/codegen for a tiny bench artifact"),
    run_pytest: bool = typer.Option(False, "--pytest", help="Run pytest -q in the bench workspace"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Deterministic allowlist pick"),
):
    """Run the external-repo bench; writes JSON + Markdown under logs/."""
    from . import bench_runner as br

    ensure_repo_structure()
    allowlist = ROOT / "docs" / "bench_repos.yaml"
    out_dir = LOGS.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = br.bench_repo_from_cli(
            ocean_root=ROOT.resolve(),
            output_dir=out_dir,
            allowlist_path=allowlist,
            dry_run=dry_run,
            list_only=list_repos,
            allow_network_flag=i_understand_network,
            repo_url=repo_url,
            repo_path=repo_path,
            run_codegen=run_codegen,
            run_pytest=run_pytest,
            seed=seed,
        )
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2)
    if list_repos:
        if isinstance(result, list):
            for s in result:
                console.print(f"- {s.name}  {s.url or s.path}  tags={getattr(s, 'tags', [])}")
        raise typer.Exit(code=0)
    assert isinstance(result, dict)
    if dry_run:
        console.print(json.dumps(result, indent=2))
        raise typer.Exit(code=0)
    bid = result.get("bench_id", "unknown")
    console.print(f"✅ Bench complete. Reports: logs/bench-{bid}.json , logs/bench-{bid}.md")
    raise typer.Exit(code=0)


@app.command(help="Run backend tests via pytest")
def test():
    """Run the test suite"""
    ensure_repo_structure()

    # Create session log for test run
    log = session_log_path()

    console.print("[bold blue]🌊 OCEAN:[/bold blue] Running tests for your generated project...")

    try:
        # Check if backend tests exist
        if not (BACKEND / "tests").exists():
            console.print("[yellow]⚠️ No backend tests found. Run 'ocean init' first to generate scaffolds.[/yellow]")
            write_log(log, "[OCEAN] Test run failed: No backend tests found")
            raise typer.Exit(code=1)

        # Confirm before network operations
        if Confirm.ask("📦 Install/upgrade test dependencies with pip?", default=False):
            console.print("📦 Installing test dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "fastapi[all]", "pytest", "httpx"],
                          capture_output=True, check=True)
        else:
            console.print("[yellow]Skipping dependency installation.[/yellow]")

        # Run tests (both tests/ and backend/tests/)
        console.print("🧪 Running tests...")
        code = subprocess.call([sys.executable, "-m", "pytest", "-v", "tests/", "backend/tests/"])

        if code == 0:
            console.print("✅ [green]All tests passed![/green]")
            write_log(log, "[OCEAN] Test run completed successfully - all tests passed")
        else:
            console.print("❌ [red]Some tests failed.[/red]")
            write_log(log, f"[OCEAN] Test run completed with failures (exit code: {code})")

        raise typer.Exit(code=code)
        
    except FileNotFoundError:
        console.print("[red]❌ pytest not found. Install project dependencies first.[/red]")
        raise typer.Exit(code=1)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to install dependencies: {e}[/red]")
        raise typer.Exit(code=1)




@app.command(help="Show a dry-run deployment plan")
def deploy(dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Preview steps only")):
    """Show deployment plan"""
    ensure_repo_structure()
    if dry_run:
        if os.getenv("OCEAN_SIMPLE_FEED") == "1":
            feed("🌊 Ocean: Deployment Plan (Dry Run)")
            steps = [
                "Build project artifacts",
                "Create Docker image",
                "Push to container registry",
                "Deploy to cloud platform",
                "Configure environment variables",
                "Verify deployment",
            ]
            for i, s in enumerate(steps, 1):
                feed(f"🌊 Ocean: Deploy — Step {i}: {s}")
            feed("💡 This is a preview. Run with --no-dry-run to execute.")
        else:
            console.print("\n[bold blue]🚀 Deployment Plan (Dry Run)[/bold blue]")
            plan_table = Table(title="📋 Deployment Steps")
            plan_table.add_column("Step", style="cyan")
            plan_table.add_column("Description", style="green")
            plan_table.add_row("1", "Build project artifacts")
            plan_table.add_row("2", "Create Docker image")
            plan_table.add_row("3", "Push to container registry")
            plan_table.add_row("4", "Deploy to cloud platform")
            plan_table.add_row("5", "Configure environment variables")
            plan_table.add_row("6", "Verify deployment")
            console.print(plan_table)
            console.print("\n💡 [yellow]This is a preview. Run with --no-dry-run to execute.[/yellow]")
        return
    # Live deploy (local, via Docker Compose in provisioned workspace)
    spec_dict = _load_project_spec()
    if not spec_dict:
        console.print("[yellow]⚠️ No project spec found. Run 'ocean clarify' first.[/yellow]")
        raise typer.Exit(code=1)
    spec = ProjectSpec.from_dict(spec_dict)
    slug = _slugify(spec.name)
    workspace = PROJECTS / slug
    if not workspace.exists():
        console.print(f"[dim]Provisioning workspace at {workspace}…[/dim]")
        _provision_workspace(spec.name)
    # Check Docker/Compose (required). If missing, Mario attempts installation.
    docker = shutil.which("docker")
    if not docker:
        console.print("[yellow]⚠️ Docker not found. Mario will attempt installation…[/yellow]")
        if not _install_docker():
            console.print("[red]❌ Unable to install Docker automatically. Install/start Docker and retry.")
            raise typer.Exit(code=1)
        docker = shutil.which("docker")
        if not docker:
            console.print("[red]❌ Docker still not available after install attempt.")
            raise typer.Exit(code=1)
    try:
        info = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        if info.returncode != 0:
            console.print("[yellow]⚠️ Docker daemon not available. Mario will attempt to start it…")
            if not _start_docker_daemon():
                console.print("[red]❌ Docker daemon did not become healthy. Start Docker Desktop/daemon and retry.")
                raise typer.Exit(code=1)
        comp = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True, timeout=10)
        if comp.returncode != 0:
            console.print("[red]❌ docker compose not available. Install Docker Compose v2.")
            raise typer.Exit(code=1)
    except Exception:
        console.print("[red]❌ Unable to verify Docker/Compose. Ensure Docker is running.")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]🌊 OCEAN:[/bold blue] Deploying locally with Docker Compose in {workspace}…")
    # Bring up services (Compose only)
    try:
        code = subprocess.call([docker, "compose", "up", "-d"], cwd=str(workspace))
        if code != 0:
            console.print(f"[red]❌ docker compose up failed (exit {code}). Ensure Docker is healthy and retry.")
            raise typer.Exit(code=code)
    except KeyboardInterrupt:
        console.print("[yellow]Deployment interrupted by user.[/yellow]")
        raise typer.Exit(code=130)
    console.print("✅ [green]Services are up.[/green]")
    console.print("🔗 Backend: http://127.0.0.1:8000/healthz")
    console.print("🖥️ UI: http://127.0.0.1:5173")
    raise typer.Exit(code=0)


## MCP commands removed




@app.command(help="Chat REPL — talk to Ocean and trigger actions")
def chat_repl():
    """Minimal chat REPL. Type 'help' for commands, 'exit' to quit.

    Commands:
      - prd: <text>        Replace docs/prd.md with text
      - crew               Show each agent’s voicing & skills (from docs/personas.yaml)
      - plan               Generate plan/backlog (no deploy)
      - build              Full chat flow without staging
      - stage              Deploy to local staging (Compose or fallback)
      - deploy             Same as stage
      - status             Show quick status
      - exit               Quit
    """
    ensure_repo_structure()
    os.environ.setdefault("OCEAN_SIMPLE_FEED", "1")
    console.print("[bold blue]🌊 OCEAN:[/bold blue] Chat REPL — type 'help' for options.")
    while True:
        try:
            if os.getenv("OCEAN_SIMPLE_FEED") == "1":
                line = input("ocean> ").strip()
            else:
                line = Prompt.ask("ocean").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not line:
            continue
        if line in {"exit", "quit"}:
            break
        if line == "help":
            console.print(
                "Commands: prd: <text> | crew | plan | build | stage | deploy | status | exit"
            )
            continue
        if line in {"crew", "voices", "skills"}:
            console.print(crew_cards_plain_text(search_start=ROOT))
            continue
        if line.startswith("prd:"):
            text = line.split(":", 1)[1].strip()
            (DOCS/"prd.md").write_text(text + "\n", encoding="utf-8")
            console.print("✅ PRD updated (docs/prd.md)")
            continue
        if line == "plan":
            log = session_log_path()
            # Preserve a PRD the user just set — don't overwrite from repo
            if (DOCS / "prd.md").exists():
                os.environ["OCEAN_REFRESH_PRD"] = "0"
            _do_clarify(log)
            console.print("✅ Plan ready.")
            continue
        if line == "build":
            prd_path = DOCS / "prd.md"
            prd_text = prd_path.read_text(encoding="utf-8").strip() if prd_path.exists() else ""
            if not prd_text:
                console.print("No PRD set. Use: prd: <what to build>")
                continue
            from . import codex_exec as _cx
            feed("🌊 Ocean: Dispatching to agent — building now…")
            result = _cx.generate_files_with_fallback(
                prd_text, context_file=DOCS / "project.json"
            )
            if result and "__cursor_handoff__" in result:
                feed("🌊 Ocean: Cursor handoff written to docs/handoffs/ — open in Cursor Composer.")
            elif result:
                workspace = ROOT / "workspace"
                workspace.mkdir(exist_ok=True)
                for path, content in result.items():
                    out = workspace / path
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(content, encoding="utf-8")
                    feed(f"🌊 Ocean: ✅ wrote workspace/{path}")
                console.print(f"✅ Build complete — {len(result)} file(s) written to workspace/.")
            else:
                console.print("Build returned no files. Run: ocean doctor")
            continue
        if line in {"stage", "deploy"}:
            try:
                deploy(dry_run=False)  # type: ignore[arg-type]
            except SystemExit:
                pass
            continue
        if line == "status":
            console.print({
                "cwd": str(ROOT),
                "docs": str(DOCS),
                "compose": bool(__import__('shutil').which("docker")),
            })
            continue
        console.print("[yellow]Unknown command. Type 'help'.[/yellow]")




@app.command(name="codex-chat", help="Start a Codex-style chat wrapped with Ocean branding (Codex required)")
def codex_chat():
    """Ocean-wrapped Codex chat with an Ocean banner and init/auth handled up front."""
    ensure_repo_structure()
    _load_env_file(ROOT / ".env")
    _ensure_codex_auth()
    # Guard: require TTY unless --no-ui/stream mode is enabled
    if (not sys.stdin.isatty() or not sys.stdout.isatty()) and os.getenv("OCEAN_NO_UI") not in ("1", "true", "True"):
        console.print("[yellow][Ocean][/yellow] Interactive chat requires a real terminal (TTY). Run in Terminal/iTerm, or use --no-ui.")
        console.print("For diagnostics, run: ocean doctor")
        raise typer.Exit(code=2)
    try:
        from .codex_wrap import run as run_wrap
    except Exception as e:
        console.print(f"[red]❌ Failed to load chat wrapper: {e}")
        raise typer.Exit(code=1)
    code = run_wrap([])
    raise typer.Exit(code=code)


@app.command(help="Start orchestration immediately without prompts (internal)")
def autostart():
    """Kick off planning and execution so chatter begins automatically.

    - Builds a spec from docs/project.json or docs/prd.md or repository auto-PRD.
    - Generates a backlog and executes it, emitting structured events.
    """
    ensure_repo_structure()
    _load_env_file(ROOT / ".env")
    apply_backend_env_from_prefs(Path.cwd())
    # Create structured events file for the session
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    events_file = LOGS / f"events-{timestamp}.jsonl"
    os.environ["OCEAN_EVENTS_FILE"] = str(events_file)

    # Load project spec from docs/project.json if present; otherwise synthesize from PRD or repo
    spec_dict = _load_project_spec()
    if not spec_dict:
        prd = _load_prd()
        if not prd:
            prd = _autoprd_from_repo()
            (DOCS / "prd.md").write_text(prd, encoding="utf-8")
        spec_dict = _parse_prd(prd)
        _save_project_spec(spec_dict)
    spec = ProjectSpec.from_dict(spec_dict)

    # Generate and execute backlog, which emits events as it progresses
    backlog = generate_backlog(spec)
    execute_backlog(backlog, DOCS, spec)
    # No exit code significance; this is a fire-and-forget command
    raise typer.Exit(code=0)


@app.command(help="Continuous build-test loop (never exits; emits events for the REPL)")
def loop(
    interval: int = typer.Option(30, "--interval", help="Seconds to wait between cycles (default 30)"),
):
    """Continuously generates a plan and executes it, emitting events each cycle.

    - Re-reads docs/prd.md each cycle to adapt to changes
    - Emits runtime URLs when available, then Tony runs tests
    - Never exits; stop with Ctrl-C
    """
    ensure_repo_structure()
    _load_env_file(ROOT / ".env")
    apply_backend_env_from_prefs(Path.cwd())
    _bk_loop = get_codegen_backend()
    # Hydrate API keys and ensure Codex auth so codegen works in loop mode (Codex backend only)
    _hydrate_tokens()
    if _bk_loop == "openai_api":
        if not os.getenv("OPENAI_API_KEY"):
            feed("🌊 Ocean: ❌ Backend openai_api requires OPENAI_API_KEY.")
            raise typer.Exit(code=1)
    elif _bk_loop == "gemini_api":
        if not (os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()):
            feed("🌊 Ocean: ❌ Backend gemini_api requires GEMINI_API_KEY or GOOGLE_API_KEY.")
            raise typer.Exit(code=1)
    elif _bk_loop == "codex":
        _ensure_codex_auth()
        _warmup_codex()
        # Verify Codex exec works before entering long iteration
        try:
            ok, detail, cat = _codex_e2e_test(timeout=8)
        except Exception:
            ok, detail, cat = False, "unknown error", None
        if not ok:
            cat_s = f" [{cat}]" if cat else ""
            feed(f"🌊 Ocean: ❌ Codex exec unavailable{cat_s} — {detail}. Waiting for auth/key… (retrying). Try 'codex login'.")
            # Retry loop: wait in short intervals until available
            import time as _t
            for _ in range(6):  # ~48s total
                _t.sleep(4)
                try:
                    ok, detail, cat = _codex_e2e_test(timeout=6)
                except Exception:
                    ok, detail, cat = False, "unknown error", None
                if ok:
                    feed("🌊 Ocean: Codex exec OK. Proceeding with iteration.")
                    break
            if not ok:
                feed("🌊 Ocean: ❌ Codex still not ready. Exiting loop to save time.")
                raise typer.Exit(code=2)
    else:
        feed(f"🌊 Ocean: Loop mode with backend={_bk_loop} (skipping Codex warmup/exec probe).")
    # Set up a single events file for the session
    if not os.getenv("OCEAN_EVENTS_FILE"):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        events_file = LOGS / f"events-{timestamp}.jsonl"
        os.environ["OCEAN_EVENTS_FILE"] = str(events_file)

    try:
        # removing unused time import
        cycle = 0
        while True:
            cycle += 1
            # Load or synthesize spec per cycle
            _codex_debug_probe(verbose=os.getenv("OCEAN_VERBOSE", "0") not in ("0", "false", "False"))
            spec_dict = _load_project_spec()
            if not spec_dict:
                prd = _load_prd()
                if not prd:
                    prd = _autoprd_from_repo()
                    (DOCS / "prd.md").write_text(prd, encoding="utf-8")
                spec_dict = _parse_prd(prd)
                _save_project_spec(spec_dict)
            spec = ProjectSpec.from_dict(spec_dict)

            # Generate and execute backlog
            backlog = generate_backlog(spec)
            execute_backlog(backlog, DOCS, spec)

            # After execution, validate requirements if present
            try:
                from . import requirements as _req
                reqs, source = _req.load_requirements(DOCS)
            except Exception:
                reqs, source = None, ""
            if reqs is None:
                # Prompt to create requirements for iterative convergence
                _emit_event("note", agent="Tony", title="No requirements file found (docs/requirements.json or .yml). Create one to drive iteration.")
                # Sleep then continue next cycle
                _sleep(interval)
                continue
            ok, results = _req.validate(reqs)
            report_path = _req.write_report(DOCS, results, source)
            _emit_event("note", agent="Tony", title=f"Requirements report: {report_path}")

            if ok:
                # All requirements satisfied — wait for user input (/continue) or spec/req change
                _emit_event("note", agent="Tony", title="All requirements satisfied. Waiting for /continue or requirements change…")
                _wait_for_continue_or_change([DOCS / "requirements.json", DOCS / "requirements.yml", DOCS / "prd.md"])  # blocks
            else:
                # Not satisfied — continue iterating after a short pause
                _sleep(interval)
    except KeyboardInterrupt:
        pass
    raise typer.Exit(code=0)


@app.command(help="Add a note to the autonomous inbox (human-in-the-loop)")
def ingest(
    message: str = typer.Argument(..., help="Product idea, feedback, or test note"),
    attach: list[Path] = typer.Option(
        [],
        "--attach",
        "-a",
        help="Attach file path (repeatable; stored as absolute paths in the inbox)",
    ),
):
    ensure_repo_structure()
    paths = [p for p in attach if p]
    p = ingest_message(message, paths, cwd=ROOT)
    feed(f"🌊 Ocean: inbox ← {p.name}")


@app.command(help="Show autonomous runtime state (.ocean/) and inbox depth")
def status():
    ensure_repo_structure()
    rprint(format_status_text(cwd=ROOT))


@app.command(name="cycle", help="Run one autonomous cycle (inbox → plan → execute)")
def cycle_once(
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Soft cap: skip execution if estimated tokens exceed this (OCEAN_TOKEN_ESTIMATE_PER_TASK per task)",
    ),
):
    ensure_repo_structure()
    _load_env_file(ROOT / ".env")
    apply_backend_env_from_prefs(ROOT)
    if not os.getenv("OCEAN_EVENTS_FILE"):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        events_file = LOGS / f"events-{timestamp}.jsonl"
        os.environ["OCEAN_EVENTS_FILE"] = str(events_file)
        try:
            events_file.touch(exist_ok=True)
        except Exception:
            pass
    res = run_cycle(root=ROOT, docs_dir=DOCS, max_tokens=max_tokens)
    if not res.ok:
        feed(f"🌊 Ocean: cycle failed — {res.message}")
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


def _emit_event(kind: str, **data) -> None:
    path = os.getenv("OCEAN_EVENTS_FILE")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            payload = {"event": kind, **data}
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass

def _sleep(seconds: int) -> None:
    import time as _t
    try:
        _t.sleep(max(1, int(seconds)))
    except Exception:
        pass

def _wait_for_continue_or_change(paths: list[Path]) -> None:
    """Block until logs/continue is touched or any of the given files change."""
    import time as _t
    cont = LOGS / "continue"
    last_mtimes = {p: (p.stat().st_mtime if p.exists() else 0.0) for p in paths}
    while True:
        # Continue signal
        if cont.exists():
            try:
                cont.unlink()
            except Exception:
                pass
            _emit_event("note", agent="Ocean", title="Continue signal received; resuming iteration…")
            return
        # Requirements/spec change
        changed = False
        for p in paths:
            try:
                mt = p.stat().st_mtime if p.exists() else 0.0
            except Exception:
                mt = 0.0
            if mt != last_mtimes.get(p, 0.0):
                changed = True
                last_mtimes[p] = mt
        if changed:
            _emit_event("note", agent="Ocean", title="Requirements/spec changed; resuming iteration…")
            return
        _t.sleep(1)

def _codex_debug_probe(verbose: bool = False) -> None:
    """Emit a concise Codex status line to the feed, with details on failure.

    Shows: mode (subscription/api_fallback/none), codex path, version snippet,
    token presence, OPENAI_API_KEY presence, and a short auth hint.
    """
    try:
        from . import codex_client as _cc
        st = _cc.check()
    except Exception as e:
        feed(f"🌊 Ocean: ❌ Codex probe failed: {e}")
        return
    import shutil
    import subprocess
    codex_path = shutil.which("codex") or "(not found)"
    version = "(n/a)"
    if shutil.which("codex"):
        try:
            out = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=5)
            version = (out.stdout or out.stderr or "").strip().splitlines()[0][:80]
        except Exception:
            version = "(error)"
    token = "yes" if os.getenv("CODEX_AUTH_TOKEN") else "no"
    api = "yes" if os.getenv("OPENAI_API_KEY") else "no"
    mode = st.mode if getattr(st, "ok", False) else "none"
    # Always show one-liner mode; details when failing or verbose
    feed(f"🌊 Ocean: Codex mode={mode}, codex={codex_path}, version={version}, token={token}, api_key={api}")
    if not getattr(st, "ok", False):
        # Try to add auth hint
        try:
            out = subprocess.run(["codex", "auth"], capture_output=True, text=True, timeout=5)
            line = (out.stdout or out.stderr or "").strip().splitlines()[:2]
            if line:
                feed("🌊 Ocean: codex auth → " + " | ".join(s.strip() for s in line))
        except Exception:
            pass
        feed("🌊 Ocean: Hint: run 'codex auth login' or set OPENAI_API_KEY.")
    elif verbose:
        feed("🌊 Ocean: Codex ready. Using subscription or API fallback.")


@app.command(help="Run Repo-Scout: per-agent codex exec reports and Moroni synthesis")
def scout():
    ensure_repo_structure()
    _load_env_file(ROOT / ".env")
    # Build context bundle for Codex
    spec_dict = _load_project_spec()
    spec = ProjectSpec.from_dict(spec_dict) if spec_dict else ProjectSpec(name=Path.cwd().name, kind="web")
    bundle = ctx.build_context_bundle(spec)

    reports_dir = DOCS / "repo_scout"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Helper to emit feed lines
    def emit(kind: str, **data):
        path = os.getenv("OCEAN_EVENTS_FILE")
        if not path:
            return
        try:
            with open(path, "a", encoding="utf-8") as f:
                payload = {"event": kind, **data}
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass

    tasks = [
        ("Q", "backend", "Audit backend files, propose 2 PRs.", reports_dir / "Q.md"),
        ("Edna", "frontend", "Review UI code, suggest 2 UX improvements.", reports_dir / "Edna.md"),
        ("Mario", "infra", "Audit workflows/Docker, suggest 1 infra improvement.", reports_dir / "Mario.md"),
        ("Tony", "tests", "Analyze tests, stress core loop, report issues.", reports_dir / "Tony.md"),
    ]

    for agent, scope, task, out_path in tasks:
        instruction = (
            f"You are {agent}, responsible for {scope}. Review the repository context and produce a short report with Findings and Suggestions.\n"
            f"Scope: {scope}. Task: {task}\n"
            "Return JSON mapping the path to Markdown content. Use headings: # Findings, # Suggestions, # Proposed PRs."
            " Keep it concise and actionable."
            "\nVoice: " + voice_brief(agent, context=scope, search_start=ROOT)
        )
        files = codex_exec.generate_files(instruction, [str(out_path.relative_to(Path.cwd()))], bundle, agent=agent)
        if files:
            for rel, content in files.items():
                p = Path(rel)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
            emit("task_start", agent=agent, title=f"Repo-scout: {scope}", intent=task)
            emit("task_end", agent=agent, title=f"Repo-scout: {scope}", intent=task)
            emit("note", agent=agent, title=f"Report: {out_path}")

    # Moroni synthesis
    try:
        combined = "\n\n".join([
            (reports_dir / "Q.md").read_text(encoding="utf-8") if (reports_dir / "Q.md").exists() else "",
            (reports_dir / "Edna.md").read_text(encoding="utf-8") if (reports_dir / "Edna.md").exists() else "",
            (reports_dir / "Mario.md").read_text(encoding="utf-8") if (reports_dir / "Mario.md").exists() else "",
            (reports_dir / "Tony.md").read_text(encoding="utf-8") if (reports_dir / "Tony.md").exists() else "",
        ])
        tmp = reports_dir / "_combined_reports.md"
        tmp.write_text(combined, encoding="utf-8")
        synth_path = reports_dir / "Moroni-synthesis.md"
        instruction = (
            "Synthesize the following agent reports into a cohesive architecture & roadmap. "
            "Approve/reject proposals, and assign phased next steps. Keep it concise."
            " Return JSON mapping to 'docs/repo_scout/Moroni-synthesis.md'."
            "\nVoice: " + voice_brief("Moroni", context="planning", search_start=ROOT)
        )
        files = codex_exec.generate_files(instruction, [str(synth_path)], tmp, agent="Moroni")
        if files:
            for rel, content in files.items():
                p = Path(rel)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
            emit("note", agent="Moroni", title=f"Synthesis: {synth_path}")
    except Exception:
        pass
    raise typer.Exit(code=0)


def entrypoint():
    # Bare ``ocean`` (no subcommand): same interactive feed as ``ocean chat``.
    if len(sys.argv) == 1:
        from . import launcher

        sys.argv.extend(launcher.resolve_bare_ocean_argv())
    app()


@app.command(help="Diagnose environment and Codex CLI readiness")
def doctor(
    explain: bool = typer.Option(False, "--explain", help="Describe Doctor vs crew agents"),
):
    if explain:
        console.print(
            "[dim]Ocean Doctor is preflight diagnostics (Codex, tokens, sandbox). "
            "It is not a crew agent. Crew: Moroni, Q, Edna, Mario, Tony — each has its own role in planning and codegen.[/dim]"
        )
    _run_doctor_quick(full=True)


@app.command(name="self-update", help="Update Ocean package and refresh global launcher")
def self_update():
    """Reinstall Ocean (-e) from the home repo and refresh the /usr/local/bin/ocean symlink.

    Works even when invoked from a workspace clone.
    """
    ensure_repo_structure()
    repo_root = Path(__file__).resolve().parent.parent  # Home Ocean repo (contains pyproject.toml)
    feed(f"🌊 Ocean: Updating editable install from {repo_root}…")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(repo_root)], check=True, cwd=str(repo_root))
    except subprocess.CalledProcessError as e:
        feed(f"🌊 Ocean: ❌ pip install failed (exit {e.returncode}).")
        raise typer.Exit(code=e.returncode)
    # Refresh global symlink to point at this repo's ocean-cli
    target = repo_root / "ocean-cli"
    global_bin = Path("/usr/local/bin/ocean")
    try:
        if global_bin.exists() or global_bin.parent.exists():
            if os.access(str(global_bin.parent), os.W_OK):
                if global_bin.exists():
                    try:
                        current = os.readlink(str(global_bin))
                    except Exception:
                        current = ""
                else:
                    current = ""
                if current != str(target):
                    os.system(f"ln -sf '{target}' '{global_bin}'")
                    feed(f"🌊 Ocean: Global launcher updated → {global_bin}")
            else:
                feed("🌊 Ocean: No write access to /usr/local/bin. Run: sudo ln -sf '" + str(target) + "' '" + str(global_bin) + "'")
    except Exception:
        pass
    feed("🌊 Ocean: Self-update complete.")


def _run_doctor_quick(full: bool = False) -> None:
    """Quick environment checks.

    - Verifies codex on PATH
    - Shows codex --version and auth hint
    """
    table = Table(title="🔍 Ocean Doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")

    # PATH check
    codex_path = shutil.which("codex")
    table.add_row("ocean binary", shutil.which("ocean") or "(not on PATH)")
    table.add_row("codex in PATH", codex_path or "not found")

    # Version check
    version = "(n/a)"
    if codex_path:
        try:
            out = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=5)
            version = (out.stdout or out.stderr).strip() or "ok"
        except Exception as e:
            version = f"error: {e}"
    table.add_row("codex --version", version)

    # Auth check (best-effort; some versions lack 'auth status')
    auth = "(unknown)"
    if codex_path:
        try:
            out = subprocess.run(["codex", "auth"], capture_output=True, text=True, timeout=5)
            txt = (out.stdout or out.stderr).strip()
            if "login" in txt.lower():
                auth = "use 'codex login' if needed"
            else:
                auth = txt or "ok"
        except Exception:
            auth = "run 'codex login'"
    table.add_row("codex auth", auth)

    try:
        table.add_row("codegen backend", get_codegen_backend())
    except Exception:
        table.add_row("codegen backend", "(unknown)")

    # Optional end-to-end exec test (fast, token-free if subscription)
    try:
        ok, detail, cat = _codex_e2e_test()
        row = detail if ok else f"error: {detail}"
        if cat and not ok:
            row += f" [{cat}]"
        table.add_row("codex exec (e2e)", row)
    except Exception as e:
        table.add_row("codex exec (e2e)", f"error: {e}")

    console.print(table)


def classify_codex_exec_failure(combined_text: str) -> Optional[str]:
    """Best-effort bucket for Codex CLI stderr/stdout when JSON probe fails."""
    if not (combined_text or "").strip():
        return None
    t = combined_text.lower()
    rules: list[tuple[str, tuple[str, ...]]] = [
        (
            "quota_billing",
            (
                "quota",
                "billing",
                "credit",
                "balance",
                "payment required",
                "insufficient",
                "out of credits",
                "no credits",
                "usage limit",
                "spend limit",
            ),
        ),
        ("rate_limit", ("429", "rate limit", "too many requests")),
        ("auth_permission", ("401", "403", "unauthorized", "forbidden", "invalid token", "token expired", "not authenticated")),
    ]
    for label, needles in rules:
        if any(n in t for n in needles):
            return label
    return "unknown_exec_failure"


def _codex_e2e_test(timeout: int = 8) -> tuple[bool, str, Optional[str]]:
    """Tiny end-to-end check of `codex exec` without heavy cost.

    Sends a trivial instruction asking for `{}` JSON; returns (ok, detail, failure_category).
    failure_category is set only when ok is False.
    """
    import shutil
    import subprocess
    import json as _json
    import os as _os
    codex = shutil.which("codex")
    if not codex:
        return False, "codex not found", None
    prompt = "Return ONLY JSON object {}."
    try:
        # Defaults: search ON; sandbox ON (workspace-write); bypass only if explicitly enabled
        use_search = _os.getenv("OCEAN_CODEX_SEARCH") not in ("0", "false", "False")
        bypass = _os.getenv("OCEAN_CODEX_BYPASS_SANDBOX") in ("1", "true", "True")
        sandbox = _os.getenv("OCEAN_CODEX_SANDBOX")
        approval = _os.getenv("OCEAN_CODEX_APPROVAL")
        profile = _os.getenv("OCEAN_CODEX_PROFILE")
        want_cd = _os.getenv("OCEAN_CODEX_CD", "1") not in ("0", "false", "False")
        # detect git repo
        skip_git = False
        try:
            _g = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
            if _g.returncode != 0:
                skip_git = True
        except Exception:
            skip_git = True
        cmd = [codex]
        if use_search:
            cmd.append("--search")
        if profile:
            cmd += ["--profile", profile]
        if want_cd:
            cmd += ["--cd", str(Path.cwd())]
        if skip_git:
            cmd.append("--skip-git-repo-check")
        cmd.append("exec")
        if bypass:
            cmd.append("--dangerously-bypass-approvals-and-sandbox")
        else:
            sb = sandbox if sandbox in ("read-only", "workspace-write", "danger-full-access") else "workspace-write"
            cmd += ["--sandbox", sb]
            if approval in ("untrusted", "on-failure", "on-request", "never"):
                cmd += ["--ask-for-approval", approval]
        # Prefer faster success detection with --output-last-message
        last_path = LOGS / "codex-test-last.txt"
        cmd += ["--output-last-message", str(last_path)]
        cmd.append(prompt)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = proc.stdout or ""
        err = proc.stderr or ""
        # Try direct JSON, then liberal extraction to tolerate banners/headers
        try:
            obj = _json.loads(out)
        except Exception:
            try:
                from .codex_exec import _extract_json as _x
                obj = _x(out)
            except Exception:
                obj = None
        if not isinstance(obj, dict) and last_path.exists():
            try:
                lm = last_path.read_text(encoding="utf-8")
                obj = _json.loads(lm)
            except Exception:
                try:
                    from .codex_exec import _extract_json as _x2
                    obj = _x2(lm)
                except Exception:
                    obj = None
        if isinstance(obj, dict):
            return True, "ok", None
        # Produce a more actionable failure string for doctor table and early abort
        rc = proc.returncode
        head_err = (err.strip().splitlines()[:8]) if err.strip() else []
        head_out = (out.strip().splitlines()[:8]) if out.strip() else []
        # Mask prompt (last arg)
        _cmd = list(cmd)
        if _cmd:
            _cmd = _cmd[:-1] + ["…PROMPT…"]
        cmd_repr = " ".join(_cmd)
        detail = f"rc={rc}; cmd={cmd_repr}; err={' | '.join(head_err)}; out={' | '.join(head_out)}"
        cat = classify_codex_exec_failure(err + "\n" + out)
        return False, detail, cat
    except subprocess.TimeoutExpired:
        return False, "timeout", "unknown_exec_failure"
    except Exception as e:
        return False, str(e), classify_codex_exec_failure(str(e))


@app.command(help="Quick Codex E2E test (no heavy usage)")
def codex_test():
    """Run a tiny codex exec to validate end-to-end readiness and print a one-line result."""
    ok, detail, cat = _codex_e2e_test()
    if ok:
        feed(f"🌊 Ocean: Codex E2E: {detail}")
        raise typer.Exit(code=0)
    else:
        extra = f" [{cat}]" if cat else ""
        feed(f"🌊 Ocean: ❌ Codex E2E failed: {detail}{extra}")
        raise typer.Exit(code=1)


@house_app.command("scan", help="List old/unused files and directories Ocean can remove")
def cleanup_scan():
    candidates = []
    # Old generated projects
    for p in [ROOT / "ocean_brython-snake", ROOT / "projects" / "ocean---multi-agent-software-engineering-orchestrator"]:
        if p.exists():
            candidates.append(("dir", p))
    # Legacy brave search module
    for p in [ROOT / "ocean" / "brave_search.py"]:
        if p.exists():
            candidates.append(("file", p))
    # CrewAI adapter (if disabled)
    if os.getenv("OCEAN_USE_CREWAI") in (None, "0", "false", "False"):
        p = ROOT / "ocean" / "crewai_adapter.py"
        if p.exists():
            candidates.append(("file", p))
    # scripts/ traces
    p = ROOT / "scripts" / "mcp_trace.py"
    if p.exists():
        candidates.append(("file", p))
    if not candidates:
        feed("🧹 Cleanup: Nothing obvious to remove. Ship shape!")
        return
    feed("🧹 Cleanup candidates:")
    for kind, path in candidates:
        feed(f" - {kind}: {path}")


@house_app.command("apply", help="Remove files/dirs found by cleanup scan (dangerous; no undo)")
def cleanup_apply():
    removed = 0
    errors = 0
    import shutil as _sh
    def _rm(p: Path) -> bool:
        try:
            if p.is_dir():
                _sh.rmtree(p)
            elif p.exists():
                p.unlink()
            return True
        except Exception as e:
            feed(f"🧹 Cleanup: failed to remove {p} — {e}")
            return False
    # Same list as scan
    targets: list[Path] = []
    for p in [ROOT / "ocean_brython-snake",
              ROOT / "projects" / "ocean---multi-agent-software-engineering-orchestrator",
              ROOT / "ocean" / "brave_search.py",
              ROOT / "scripts" / "mcp_trace.py"]:
        if p.exists():
            targets.append(p)
    if os.getenv("OCEAN_USE_CREWAI") in (None, "0", "false", "False"):
        p = ROOT / "ocean" / "crewai_adapter.py"
        if p.exists():
            targets.append(p)
    if not targets:
        feed("🧹 Cleanup: Nothing to remove. The deck is spotless.")
        return
    for p in targets:
        ok = _rm(p)
        if ok:
            removed += 1
    feed(f"🧹 Cleanup: removed {removed} item(s). {('No mishaps.' if errors==0 else f'Errors: {errors}.')} Arrr!")


def _doctor_lite() -> None:
    """Print one-line startup diagnostics with light humor and no tables."""
    global _preflight_intro_sent
    try:
        if not _preflight_intro_sent:
            feed("🤿 Ocean Doctor (preflight): Checks Codex/auth/sandbox — not a crew agent.")
            _preflight_intro_sent = True
        feed(f"🤿 Ocean Doctor (preflight): ocean {__version__} @ {Path.cwd()}")
        if _external_startup_disabled():
            feed("🤿 Ocean Doctor (preflight): external Codex startup disabled for this run")
            return
        # codex path/version
        cpath = shutil.which("codex") or "(not found)"
        try:
            cv = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=5)
            cver = (cv.stdout or cv.stderr or "").strip().splitlines()[:1]
            feed(f"🤿 Ocean Doctor (preflight): codex={cpath} ver={(cver[0] if cver else 'n/a')} (splash!)")
        except Exception:
            feed(f"🤿 Ocean Doctor (preflight): codex={cpath} (bring floaties)")
        # token status
        tok = os.getenv("CODEX_AUTH_TOKEN") or ""
        src = os.getenv("OCEAN_CODEX_TOKEN_SOURCE") or "-"
        tshort = (tok[:6] + "…" + tok[-6:]) if len(tok) >= 16 else ("(set)" if tok else "(none)")
        feed(f"🤿 Ocean Doctor (preflight): token={'yes' if tok else 'no'} src={src} preview={tshort}")
        # sandbox/search/profile snapshot
        search = os.getenv("OCEAN_CODEX_SEARCH", "0")
        bypass = os.getenv("OCEAN_CODEX_BYPASS_SANDBOX", "1")
        sb = os.getenv("OCEAN_CODEX_SANDBOX") or ("bypass" if bypass not in ("0","false","False") else "(default)")
        ap = os.getenv("OCEAN_CODEX_APPROVAL") or "(default)"
        prof = os.getenv("OCEAN_CODEX_PROFILE") or "(none)"
        feed(f"🤿 Ocean Doctor (preflight): search={'on' if search in ('1','true','True') else 'off'} sandbox={sb} approval={ap} profile={prof}")
        # exec probe
        ok, detail, cat = _codex_e2e_test(timeout=8)
        catbit = f" [{cat}]" if (not ok and cat) else ""
        feed(f"🤿 Ocean Doctor (preflight): exec={'ok' if ok else 'nope'}{catbit} — {detail if detail else 'no details'}")
        # CrewAI status
        enabled = os.getenv("OCEAN_USE_CREWAI", "1") not in ("0", "false", "False")
        try:
            import importlib
            importlib.import_module("crewai")
            installed = True
        except Exception:
            installed = False
        feed(f"🤿 Ocean Doctor (preflight): crewai={'enabled' if enabled else 'disabled'}, installed={'yes' if installed else 'no'} — backbone ready? {'aye' if (enabled and installed) else 'nay'}")
    except Exception as e:
        feed(f"🤿 Ocean Doctor (preflight): hiccup — {e}")


@token_app.command("doctor", help="Diagnose Codex token: presence, source, expiry, and CLI auth state")
def token_doctor():
    tab = Table(title="🔑 Codex Token Doctor")
    tab.add_column("Field", style="cyan")
    tab.add_column("Value", style="green")
    tok = os.getenv("CODEX_AUTH_TOKEN") or ""
    src = os.getenv("OCEAN_CODEX_TOKEN_SOURCE") or "(unknown)"
    length = len(tok)
    preview = (tok[:6] + "…" + tok[-6:]) if length >= 16 else ("(set)" if tok else "(none)")
    # Decode exp
    exp_str = "(unknown)"
    expired = "(unknown)"
    try:
        parts = tok.split(".")
        if len(parts) >= 2:
            import base64, json as _json
            pad = '=' * (-len(parts[1]) % 4)
            data = base64.urlsafe_b64decode(parts[1] + pad)
            obj = _json.loads(data.decode("utf-8", errors="ignore"))
            exp = obj.get("exp")
            if isinstance(exp, (int, float)):
                from datetime import datetime as _dt
                dt = _dt.fromtimestamp(exp)
                exp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                expired = "yes" if dt < _dt.now() else "no"
    except Exception:
        pass
    # codex auth snapshot
    codex_path = shutil.which("codex") or "(not found)"
    auth_head = "(n/a)"
    if shutil.which("codex"):
        try:
            out = subprocess.run(["codex", "auth"], capture_output=True, text=True, timeout=8)
            lines = (out.stdout or out.stderr or "").strip().splitlines()[:3]
            auth_head = " | ".join(s.strip() for s in lines) or "(no output)"
        except Exception as e:
            auth_head = f"error: {e}"
    tab.add_row("token present", "yes" if tok else "no")
    tab.add_row("token length", str(length))
    tab.add_row("token preview", preview)
    tab.add_row("token source", src)
    tab.add_row("token exp", exp_str)
    tab.add_row("token expired", expired)
    tab.add_row("codex path", codex_path)
    tab.add_row("codex auth", auth_head)
    console.print(tab)


@app.command(help="Create a release commit and tag (Mario)")
def release(
    tag: str = typer.Option("v1", "--tag", help="Tag name (e.g., v1-web-tictactoe)"),
    push: bool = typer.Option(False, "--push/--no-push", help="Push to origin with --follow-tags after tagging"),
):
    """Mario commits all changes and tags a release locally.

    If --ask is enabled, asks for confirmation and an optional tag name.
    """
    ensure_repo_structure()
    if os.getenv("OCEAN_ALLOW_QUESTIONS", "1") not in ("0", "false", "False"):
        if not Confirm.ask(f"Create release with tag '{tag}'?", default=True):
            console.print("[yellow]Release canceled by user.[/yellow]")
            raise typer.Exit(code=0)
    # Run git commands
    steps = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", f"chore(release): {tag}"],
        ["git", "tag", tag],
    ]
    for cmd in steps:
        code = subprocess.call(cmd)
        if code != 0:
            console.print(f"[red]❌ Command failed:[/red] {' '.join(cmd)}")
            raise typer.Exit(code=code)
    if push:
        if os.getenv("OCEAN_ALLOW_QUESTIONS", "1") not in ("0", "false", "False"):
            if not Confirm.ask("Push to 'origin' with --follow-tags?", default=True):
                console.print("[yellow]Push skipped by user.[/yellow]")
                console.print(f"✅ [green]Release created and tagged:[/green] {tag}")
                raise typer.Exit(code=0)
        code = subprocess.call(["git", "push", "--follow-tags", "origin"])
        if code != 0:
            console.print("[red]❌ git push failed. Ensure 'origin' is configured and you have access.[/red]")
            raise typer.Exit(code=code)
        console.print(f"✅ [green]Release created, tagged, and pushed:[/green] {tag}")
    else:
        console.print(f"✅ [green]Release created and tagged:[/green] {tag}")
        raise typer.Exit(code=0)

def _auto_self_update_and_version() -> None:
    """Best-effort editable reinstall from home repo and print version."""
    try:
        repo_root = Path(__file__).resolve().parent.parent
        if (
            os.getenv("OCEAN_NO_SELF_UPDATE") not in ("1", "true", "True")
            and not _is_test_env()
        ):
            res = subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(repo_root)], capture_output=True)
            if res.returncode == 0:
                feed("🌊 Ocean: self-update OK")
            else:
                feed("🌊 Ocean: self-update skipped (pip install error)")
    except Exception:
        pass
    try:
        from . import __version__ as _v
        feed(f"🌊 Ocean v{_v}: starting up…")
    except Exception:
        pass


if __name__ == "__main__":
    app()
