from __future__ import annotations

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
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from . import __version__
from .agents import default_agents
from .models import ProjectSpec
from .planner import generate_backlog, write_backlog, execute_backlog
from .mcp import MCP
from . import context as ctx
from . import codex_exec
from .persona import voice_brief
from .feed import feed as feed_line, agent_say, you_say


def _is_test_env() -> bool:
    """Detect pytest/test runner environment.

    Returns True if either OCEAN_TEST=1 is set or Pytest is invoking
    the CLI (PYTEST_CURRENT_TEST is present)."""
    return (os.getenv("OCEAN_TEST") == "1") or (os.getenv("PYTEST_CURRENT_TEST") is not None)

console = Console()
app = typer.Typer(add_completion=False, no_args_is_help=False, help="OCEAN CLI orchestrator")

ROOT = Path.cwd()
DOCS = ROOT / "docs"
LOGS = ROOT / "logs"
BACKEND = ROOT / "backend"
UI = ROOT / "ui"
DEVOPS = ROOT / "devops"
PROJECTS = ROOT / "projects"


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


def _start_local_runtime_simple() -> Optional[str]:
    """Start backend with uvicorn and serve UI via http.server in the background.

    Returns a summary URL string or None.
    """
    logs_dir = LOGS; logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backend_app = BACKEND / "app.py"
    backend_url = None
    try:
        import uvicorn  # noqa: F401
        uvicorn_available = True
    except Exception:
        uvicorn_available = shutil.which("uvicorn") is not None
    if backend_app.exists() and uvicorn_available:
        import socket
        def _free(start=8000, limit=20):
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
        port = _free(8000)
        blog = logs_dir / f"runtime-backend-{ts}.log"
        with blog.open("a", encoding="utf-8") as out:
            subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port)], stdout=out, stderr=subprocess.STDOUT)
        backend_url = f"http://127.0.0.1:{port}/healthz"
    ui_dir = UI
    ui_url = None
    if ui_dir.exists():
        ui_port = 5173
        ulog = logs_dir / f"runtime-ui-{ts}.log"
        with ulog.open("a", encoding="utf-8") as out:
            subprocess.Popen([sys.executable, "-m", "http.server", str(ui_port), "-d", str(ui_dir)], stdout=out, stderr=subprocess.STDOUT)
        ui_url = f"http://127.0.0.1:{ui_port}"
        # Write runtime config consumed by UI if backend started
        if backend_url:
            try:
                api_base = backend_url.rsplit('/healthz', 1)[0]
                (ui_dir / "config.js").write_text(f"window.API_BASE=\"{api_base}\";\n", encoding="utf-8")
            except Exception:
                pass
    summary = " | ".join([u for u in [backend_url, ui_url] if u])
    return summary or None


def _ensure_codex_auth() -> None:
    """Ensure Codex CLI is authenticated; always trigger a best-effort login.

    Per user policy: re-auth every time (idempotent), ignore failures.
    """
    codex = shutil.which("codex")
    if not codex:
        return
    try:
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
            import re, json as _json
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            m = re.search(r"id_token=([A-Za-z0-9\-_.]+)", combined)
            if m:
                tok = m.group(1)
                os.environ["CODEX_AUTH_TOKEN"] = tok
                os.environ["OCEAN_CODEX_AUTH"] = "1"
                # Persist a marker file for detection
                home = Path.home() / ".codex"; home.mkdir(parents=True, exist_ok=True)
                auth_file = home / "auth.json"
                try:
                    payload = {"id_token": tok, "updatedAt": datetime.now().isoformat(), "source": "ocean"}
                    auth_file.write_text(_json.dumps(payload, indent=2), encoding="utf-8")
                except Exception:
                    pass
        except Exception:
            pass

        # Probe status post-login
        out = subprocess.run(["codex", "auth"], capture_output=True, text=True, timeout=10)
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

def _warmup_codex(model: str | None = None, timeout: int = 25) -> None:
    """Warm Codex up without executing a model.

    - Runs `codex --version` to verify CLI presence
    - Probes `codex auth` to verify subscription auth
    - Attempts a login once if needed (idempotent)
    - Sets OCEAN_CODEX_AUTH=1 on success
    - Emits one concise feed line only on failure
    """
    try:
        import shutil, subprocess
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
                    feed("🌊 Ocean: Codex subscription active" + (f" ({ver[0]})" if ver else ""))
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
                    feed("🌊 Ocean: Codex subscription active" + (f" ({ver[0]})" if ver else ""))
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
        for item in here.iterdir():
            if item.name in {".git", ".hg", ".svn", "__pycache__", ".pytest_cache", "venv", ".venv", "node_modules", "logs", ".mypy_cache", ".DS_Store"}:
                continue
            target = dest / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True, ignore=_ignore)
            else:
                try:
                    shutil.copy2(item, target)
                except Exception:
                    pass
        # Write marker
        (dest / ".ocean_workspace").write_text(json.dumps({"source": str(here), "createdAt": datetime.now().isoformat()}, indent=2), encoding="utf-8")
        feed(f"🌊 Ocean: Created/updated workspace at {dest} (source: {here})")
    except Exception as e:
        feed(f"[yellow]🌊 Ocean: Workspace synchronization warning: {e}[/yellow]")
    # Switch to workspace and rebind roots
    try:
        os.chdir(dest)
        _switch_root(dest)
    except Exception as e:
        feed(f"[red]🌊 Ocean: Failed to switch to workspace: {e}[/red]")


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
            l = line.strip()
            if not l:
                continue
            if l.startswith("#"):
                name = l.lstrip("# ").strip() or name
                break
            else:
                summary = l
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
    if (ROOT / "pyproject.toml").exists(): tech.append("Python/pyproject")
    if (ROOT / "requirements.txt").exists(): tech.append("requirements.txt")
    if (ROOT / "package.json").exists(): tech.append("Node/package.json")
    if (ROOT / "Dockerfile").exists(): tech.append("Dockerfile")
    if (ROOT / ".github" / "workflows").exists(): tech.append("GitHub Actions")

    # Goals/constraints rough
    if "test" in readme.lower(): goals.append("testing enabled")
    if "docker" in readme.lower(): goals.append("containerized")
    compose = read_text(ROOT/"docker-compose.yml")
    if "services:" in compose: goals.append("compose staging")
    if "fastapi" in app_py.lower(): goals.append("fastapi backend")
    if (ROOT/"ui").exists(): goals.append("static UI")

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
    lines = [l.rstrip() for l in prd_text.splitlines()]
    name = "My Project"
    description = ""
    kind = "web"
    goals: list[str] = []
    constraints: list[str] = []

    # Title
    for i, l in enumerate(lines):
        if not l.strip():
            continue
        if l.startswith("#"):
            name = l.lstrip("# ").strip() or name
            start_idx = i + 1
            break
        else:
            name = l.strip()
            start_idx = i + 1
            break
    else:
        start_idx = 0

    # One-liner
    for l in lines[start_idx:]:
        if l.strip():
            description = l.strip()
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
    for l in lines:
        low = l.lower()
        if low.startswith("## goals") or low.startswith("### goals"):
            current = "goals"; continue
        if low.startswith("## constraints") or low.startswith("### constraints"):
            current = "constraints"; continue
        if low.startswith("## "):
            current = None
        if l.strip().startswith("-") and current:
            item = l.lstrip("- ").strip()
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


def _ask(label: str, default: str = "", choices: Optional[list[str]] = None) -> str:
    """Robust prompt helper.

    - Uses Rich Prompt in test mode (OCEAN_TEST=1) to remain patchable by tests.
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

    # In test mode or non-TTY, use Rich Prompt (works with monkeypatch in tests)
    if _os.getenv("OCEAN_TEST") == "1" or not sys.stdin.isatty():
        return Prompt.ask(label, default=default, choices=choices)

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
        ans = typer.prompt(f"{label}{hint}", default=default)
        if choices and ans not in choices:
            console.print(f"[yellow]Please choose one of: {', '.join(choices)}[/yellow]")
            continue
        return ans


@app.callback(invoke_without_command=True)
def main(
    version: Optional[bool] = typer.Option(None, "--version", help="Show version and exit", is_eager=True),
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Show detailed TUI conversations and agent steps"),
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
    os.environ["OCEAN_ALLOW_QUESTIONS"] = "1" if ask else "0"
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
        # Always refresh PRD from current repository context in feed/workspace mode
        os.environ.setdefault("OCEAN_REFRESH_PRD", "1")
    else:
        os.environ.pop("OCEAN_SIMPLE_FEED", None)

    # Always activate a safe workspace when running outside the Ocean home repo
    try:
        _prepare_workspace_from_cwd()
    except Exception:
        # Non-fatal; proceed in-place if workspace prep fails
        pass


@app.command(help="Run the interactive flow: clarify → crew intros → planning → staging")
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
    # Announce again in case key came from workspace .env
    try:
        key = os.getenv("OPENAI_API_KEY")
        if key and os.getenv("OCEAN_APIKEY_ANNOUNCED") != "1":
            masked = (key[:6] + "…") if len(key) > 6 else "(set)"
            feed(f"🌊 Ocean: OPENAI_API_KEY detected (len={len(key)}, prefix={masked})")
            os.environ["OCEAN_APIKEY_ANNOUNCED"] = "1"
    except Exception:
        pass
    # Announce again in case key came from workspace .env
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
    # Create structured events file for TUI
    events_file = LOGS / f"events-{timestamp}.jsonl"
    os.environ["OCEAN_EVENTS_FILE"] = str(events_file)
    
    # Initialize Codex MCP and greet
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        # Skip block banner; use cheeky feed lines instead
        _ensure_codex_auth()
        _auto_self_update_and_version()
        feed("🌊 Ocean: Ahoy! I'm Ocean — caffeinated and ready to ship.")
        feed(f"🌊 Ocean: Workspace: {Path.cwd()}")
        feed("🌊 Ocean: I’ll skim your repo, assemble the crew, and draft a plan.")
    else:
        # Traditional banner
        console.print(banner())
        _ensure_codex_auth()
    # Ocean Doctor disabled by default per user request
    MCP.ensure_started(log)
    # Ensure project-level venv for convenience
    _ensure_root_venv()
    # Warm up Codex session early so codegen runs without delays
    _warmup_codex()
    # Hard e2e check: bail out early if exec can't run, to avoid long loops
    try:
        ok, detail = _codex_e2e_test(timeout=8)
    except Exception:
        ok, detail = False, "unknown error"
    if not ok:
        feed(f"🌊 Ocean: ❌ Codex exec unavailable — {detail}. Run 'codex auth login' or set OPENAI_API_KEY. Aborting early.")
        raise typer.Exit(code=2)
    # In feed mode we require Codex for codegen phases; errors are surfaced during plan/execute
    status = MCP.status()

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
    
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        pass
    else:
        console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Hello! I'm OCEAN, your AI-powered software engineering orchestrator.")
        console.print("I'll help you build your project by coordinating with my specialized crew.")
        console.print("Let me start by understanding what you want to build...\n")
    
    # Do interactive prompts WITHOUT spinner to avoid input interference
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: Consulting with Moroni (Architect)…")
    else:
        console.print("[dim]OCEAN is consulting with Moroni (Architect)…[/dim]")
    _do_clarify(log)

    # Optional CrewAI orchestration path
    if (not _is_test_env()) and (os.getenv("OCEAN_USE_CREWAI", "1") not in ("0", "false", "False")):
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
        feed("🌊 Ocean: Assembling the crew…")
        _do_crew(log)
        # Proceed with planning and execution, but keep Codex disabled in feed
        feed("🌊 Ocean: Creating your project plan…")
        # Preflight Codex check (dynamic)
        try:
            import os as _os
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
            task2 = progress.add_task("OCEAN is assembling the crew...", total=None)
            _do_crew(log)
            progress.update(task2, completed=True, description="✅ OCEAN assembled the crew")

            if _is_test_env():
                console.print("[dim]Test mode: skipping planning and execution.[/dim]")
                console.print(f"\n🎉 [green]OCEAN has completed your project setup![/green]")
                console.print(f"📝 Session log: [blue]{log}[/blue]")
                return

            task3 = progress.add_task("OCEAN is creating your project plan...", total=None)
            _do_plan(log)
            progress.update(task3, completed=True, description="✅ OCEAN created your plan")
    
    console.print(f"\n🎉 [green]OCEAN has completed your project setup![/green]")
    console.print(f"📝 Session log: [blue]{log}[/blue]")
    console.print(f"📋 Project spec: [blue]docs/project.json[/blue]")
    console.print(f"📋 Backlog: [blue]docs/backlog.json[/blue]")
    console.print(f"📋 Plan: [blue]docs/plan.md[/blue]")
    console.print(f"\n🌊 [bold blue]OCEAN:[/bold blue] Your AI engineering team is ready!")
    console.print(f"💡 Tip: Use 'ocean provision' to create an isolated workspace under 'projects/'.")

    # Auto-stage by default using Docker Compose (fallback to local runtime inside deploy)
    try:
        deploy(dry_run=False)  # type: ignore[arg-type]
    except SystemExit:
        # deploy exits via typer.Exit; ignore here
        pass


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

    spec = {
        "name": name.strip(),
        "kind": kind.strip().lower(),
        "description": description.strip(),
        "goals": [g.strip() for g in goals.split(",") if g.strip()],
        "constraints": [c.strip() for c in constraints.split(",") if c.strip()],
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
        console.print(table)
    feed(f"🌊 Ocean: Moroni saved your project spec to {out}")


def _do_crew(log: Path) -> None:
    """OCEAN assembles and introduces the crew"""
    ensure_repo_structure()
    spec = _load_project_spec()
    if not spec:
        console.print("[yellow]⚠️ No project spec found. Run 'ocean clarify' first.[/yellow]")
        raise typer.Exit(code=1)
    
    write_log(log, "[OCEAN] Assembling crew for project:", json.dumps(spec))
    
    feed(f"🌊 Ocean: Assembling the crew for '{spec['name']}'…")
    feed("🌊 Ocean: Each agent brings unique expertise to your project…")
    
    crew_lines: list[tuple[str, str, str]] = []
    for agent in default_agents():
        intro = agent.introduce()
        feed(f"{intro}")
        write_log(log, intro)
        if "Moroni" in intro:
            crew_lines.append(("Moroni", "Architect & Brain", "Vision, Planning, Coordination"))
        elif "Q" in intro:
            crew_lines.append(("Q", "Backend Engineer", "APIs, Services, Data Models"))
        elif "Edna" in intro:
            crew_lines.append(("Edna", "Designer & UI/UX", "Interfaces, Design Systems"))
        elif "Mario" in intro:
            crew_lines.append(("Mario", "DevOps & Infrastructure", "CI/CD, Deployment, Monitoring"))
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
    feed("🌊 Ocean: Crew assembled ✅")


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
        console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] Now let me coordinate my crew to create your project plan...")
        console.print("[bold blue]🌊 OCEAN:[/bold blue] Moroni, Q, Edna, and Mario are analyzing your requirements...")
    
    # Generate backlog from agent proposals
    backlog = generate_backlog(spec)
    
    # EXECUTE the backlog using agent capabilities
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: My crew is now EXECUTING your project tasks…")
    else:
        console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] My crew is now EXECUTING your project tasks...")
    bj, pm, runtime_summary = execute_backlog(backlog, DOCS, spec)
    
    write_log(log, f"[OCEAN] Crew completed planning and execution: {bj}")
    
    if os.getenv("OCEAN_SIMPLE_FEED") == "1":
        feed("🌊 Ocean: Excellent! My crew has created AND BUILT your project!")
        feed(f"🌊 Ocean: Backlog: {bj}")
        feed(f"🌊 Ocean: Plan summary: {pm}")
        if runtime_summary:
            feed(f"🌊 Ocean: Local runtime: {runtime_summary}")
    else:
        console.print(f"✅ [bold blue]🌊 OCEAN:[/bold blue] Excellent! My crew has created AND BUILT your project!")
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
        console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] Your project is now fully planned, built, and ready!")
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


@app.command(help="Generate/refresh scaffolds for backend, UI, CI, docs")
def init(force: bool = typer.Option(False, "--force", help="Overwrite existing files")):
    """Generate project scaffolds using AI agents"""
    ensure_repo_structure()
    
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


@app.command(help="Start the backend server and optionally serve UI")
def run(host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
        port: int = typer.Option(8000, "--port", help="Port to bind to"),
        serve_ui: bool = typer.Option(False, "--ui", help="Also serve UI files"),
        yes: bool = typer.Option(False, "-y", "--yes", help="Do not prompt; install deps")):
    """Start the backend server"""
    ensure_repo_structure()

    # Create session log for server run
    log = session_log_path()

    if not (BACKEND / "app.py").exists():
        console.print("[yellow]⚠️ No backend app found. Run 'ocean init' first to generate scaffolds.[/yellow]")
        write_log(log, "[OCEAN] Server run failed: No backend app found")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]🌊 OCEAN:[/bold blue] Starting your generated backend server...")
    console.print(f"🌐 Backend: http://{host}:{port}")

    if serve_ui:
        console.print(f"🎨 UI: http://{host}:{port}/ui")

    try:
        # Install dependencies if needed, with confirmation
        do_install = yes or Confirm.ask("📦 Install/upgrade server dependencies with pip?", default=False)
        if do_install:
            console.print("📦 Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "fastapi[all]", "uvicorn"],
                          capture_output=True, check=True)
        else:
            console.print("[yellow]Skipping dependency installation.[/yellow]")

        # Log server start
        write_log(log, f"[OCEAN] Starting server on {host}:{port}")

        # Start the server
        console.print("🚀 Starting uvicorn server...")
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.app:app",
            "--host", host,
            "--port", str(port),
            "--reload"
        ])

    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to install dependencies: {e}[/red]")
        write_log(log, f"[OCEAN] Server run failed: {e}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]Server stopped by user.[/yellow]")
        write_log(log, "[OCEAN] Server stopped by user")
        raise typer.Exit(code=0)


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
      - plan               Generate plan/backlog (no deploy)
      - build              Full chat flow without staging
      - stage              Deploy to local staging (Compose or fallback)
      - deploy             Same as stage
      - status             Show quick status
      - exit               Quit
    """
    ensure_repo_structure()
    console.print("[bold blue]🌊 OCEAN:[/bold blue] Chat REPL — type 'help' for options.")
    while True:
        try:
            line = Prompt.ask("ocean>").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not line:
            continue
        if line in {"exit", "quit"}:
            break
        if line == "help":
            console.print("Commands: prd: <text> | plan | build | stage | deploy | status | exit")
            continue
        if line.startswith("prd:"):
            text = line.split(":", 1)[1].strip()
            (DOCS/"prd.md").write_text(text + "\n", encoding="utf-8")
            console.print("✅ PRD updated (docs/prd.md)")
            continue
        if line == "plan":
            log = session_log_path()
            _do_clarify(log)
            console.print("✅ Plan generated.")
            continue
        if line == "build":
            try:
                chat(prd=None, stage=False, prod=False)  # type: ignore[call-arg]
            except SystemExit:
                pass
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




@app.command(help="TUI disabled — use Ocean chat instead")
def tui():
    """Deprecated: TUI has been removed to keep things simple.

    Use `ocean` to launch the Ocean-branded chat and see team chatter inline.
    """
    console.print("[yellow]TUI is disabled.[/yellow] Use 'ocean' to chat and orchestrate.")
    raise typer.Exit(code=0)


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
    # Hydrate API keys and ensure Codex auth so codegen works in loop mode
    _hydrate_tokens()
    _ensure_codex_auth()
    _warmup_codex()
    # Verify Codex exec works before entering long iteration
    try:
        ok, detail = _codex_e2e_test(timeout=8)
    except Exception:
        ok, detail = False, "unknown error"
    if not ok:
        feed(f"🌊 Ocean: ❌ Codex exec unavailable — {detail}. Waiting for auth/key… (retrying)")
        # Retry loop: wait in short intervals until available
        import time as _t
        for _ in range(6):  # ~48s total
            _t.sleep(4)
            try:
                ok, detail = _codex_e2e_test(timeout=6)
            except Exception:
                ok = False
            if ok:
                feed("🌊 Ocean: Codex exec OK. Proceeding with iteration.")
                break
        if not ok:
            feed("🌊 Ocean: ❌ Codex still not ready. Exiting loop to save time.")
            raise typer.Exit(code=2)
    # Set up a single events file for the session
    if not os.getenv("OCEAN_EVENTS_FILE"):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        events_file = LOGS / f"events-{timestamp}.jsonl"
        os.environ["OCEAN_EVENTS_FILE"] = str(events_file)

    try:
        import time as _time
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
    import shutil, subprocess
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
            "\nVoice: " + voice_brief(agent, context=scope)
        )
        files = codex_exec.generate_files(instruction, [str(out_path.relative_to(Path.cwd()))], bundle, agent=agent)
        if files:
            for rel, content in files.items():
                p = Path(rel); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content, encoding="utf-8")
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
            "\nVoice: " + voice_brief("Moroni", context="planning")
        )
        files = codex_exec.generate_files(instruction, [str(synth_path)], tmp, agent="Moroni")
        if files:
            for rel, content in files.items():
                p = Path(rel); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content, encoding="utf-8")
            emit("note", agent="Moroni", title=f"Synthesis: {synth_path}")
    except Exception:
        pass
    raise typer.Exit(code=0)

if __name__ == "__main__":
    app()


def entrypoint():
    # If no args were provided, default to invoking the `chat` command via Typer
    # so that options get parsed/injected correctly (avoids OptionInfo default).
    if len(sys.argv) == 1:
        # Default to Ocean chat (combined feed)
        sys.argv.append("chat")
    app()


@app.command(help="Diagnose environment and Codex CLI readiness")
def doctor():
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
                auth = "use 'codex auth login' if needed"
            else:
                auth = txt or "ok"
        except Exception:
            auth = "run 'codex auth login'"
    table.add_row("codex auth", auth)

    # Optional end-to-end exec test (fast, token-free if subscription)
    try:
        ok, detail = _codex_e2e_test()
        table.add_row("codex exec (e2e)", detail if ok else f"error: {detail}")
    except Exception as e:
        table.add_row("codex exec (e2e)", f"error: {e}")

    console.print(table)


def _codex_e2e_test(timeout: int = 8) -> tuple[bool, str]:
    """Tiny end-to-end check of `codex exec` without heavy cost.

    Sends a trivial instruction asking for `{}` JSON; returns (ok, detail).
    """
    import shutil, subprocess, json as _json, os as _os
    codex = shutil.which("codex")
    if not codex:
        return False, "codex not found"
    model = _os.getenv("OCEAN_CODEX_MODEL", "o4-mini")
    prompt = "Return ONLY JSON object {}."
    try:
        proc = subprocess.run([codex, "exec", "--model", model], input=prompt.encode("utf-8"), capture_output=True, timeout=timeout)
        out = (proc.stdout or b"").decode("utf-8", errors="ignore")
        err = (proc.stderr or b"").decode("utf-8", errors="ignore")
        try:
            obj = _json.loads(out)
        except Exception:
            obj = None
        if isinstance(obj, dict):
            return True, f"ok (model: {model})"
        head = (err or out or "").strip().splitlines()[:1]
        return False, (head[0] if head else "no output")
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


@app.command(help="Quick Codex E2E test (no heavy usage)")
def codex_test():
    """Run a tiny codex exec to validate end-to-end readiness and print a one-line result."""
    ok, detail = _codex_e2e_test()
    if ok:
        feed(f"🌊 Ocean: Codex E2E: {detail}")
        raise typer.Exit(code=0)
    else:
        feed(f"🌊 Ocean: ❌ Codex E2E failed: {detail}")
        raise typer.Exit(code=1)


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
            if not Confirm.ask(f"Push to 'origin' with --follow-tags?", default=True):
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
        if os.getenv("OCEAN_NO_SELF_UPDATE") not in ("1", "true", "True"):
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
