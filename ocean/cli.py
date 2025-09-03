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


def _create_venv(path: Path) -> None:
    """Create a Python venv at path if missing and install basic deps.

    - Installs editable package in root venv
    - Installs FastAPI/uvicorn in workspace venvs for web/api kind
    """
    if not path.exists():
        subprocess.run([sys.executable, "-m", "venv", str(path)], check=False)


def _ensure_root_venv() -> None:
    v = ROOT / "venv"
    if not v.exists():
        console.print("[dim]Creating project venv under ./venv…[/dim]")
        _create_venv(v)
        pip = v / "bin" / "pip"
        if pip.exists():
            subprocess.run([str(pip), "install", "-e", "."], check=False)


def session_log_path() -> Path:
    ensure_repo_structure()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return LOGS / f"session-{ts}.log"


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

    if _os.getenv("OCEAN_TEST") == "1" or not sys.stdin.isatty():
        return Prompt.ask(label, default=default, choices=choices)

    # Build label with choices hint if provided
    hint = f" [choices: {', '.join(choices)}]" if choices else ""
    while True:
        ans = typer.prompt(f"{label}{hint}", default=default)
        if choices and ans not in choices:
            console.print(f"[yellow]Please choose one of: {', '.join(choices)}[/yellow]")
            continue
        return ans


@app.callback()
def main(version: Optional[bool] = typer.Option(None, "--version", help="Show version and exit", is_eager=True)):
    if version:
        rprint(f"ocean {__version__}")
        raise typer.Exit(code=0)


@app.command(help="Run the interactive flow: clarify → crew intros → planning")
def chat(prd: Optional[str] = typer.Option(None, "--prd", help="Path to PRD file or '-' to read from stdin")):
    """Main interactive conversation flow"""
    ensure_repo_structure()
    
    # Create session log
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = LOGS / f"session-{timestamp}.log"
    write_log(log, "OCEAN session started", datetime.now().isoformat())
    
    # Print banner and initialize Codex MCP
    console.print(banner())
    # Run doctor at startup unless disabled
    if os.getenv("OCEAN_NO_DOCTOR") not in ("1", "true", "True"):
        _run_doctor_quick()
    MCP.ensure_started(log)
    # Ensure project-level venv for convenience
    _ensure_root_venv()
    status = MCP.status()
    if (status.get("provider") != "codex-cli") and (os.getenv("OCEAN_MCP_ONLY", "1") not in ("0", "false", "False")):
        console.print("[red]❌ MCP-only mode requires Codex CLI. Install via 'brew install codex' and run 'codex auth login'.[/red]")
        raise typer.Exit(code=1)

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
    
    console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Hello! I'm OCEAN, your AI-powered software engineering orchestrator.")
    console.print("I'll help you build your project by coordinating with my specialized crew.")
    console.print("Let me start by understanding what you want to build...\n")
    
    # Do interactive prompts WITHOUT spinner to avoid input interference
    console.print("[dim]OCEAN is consulting with Moroni (Architect)…[/dim]")
    _do_clarify(log)

    # Optional CrewAI orchestration path
    if os.getenv("OCEAN_USE_CREWAI", "1") not in ("0", "false", "False"):
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

    # Non-interactive phases can use a spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Crew Spin-up
        task2 = progress.add_task("OCEAN is assembling the crew...", total=None)
        _do_crew(log)
        progress.update(task2, completed=True, description="✅ OCEAN assembled the crew")

        # Planning
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


def _do_clarify(log: Path) -> None:
    """OCEAN consults with Moroni to clarify the project vision"""
    ensure_repo_structure()
    
    console.print("[bold blue]🌊 OCEAN:[/bold blue] Please provide your PRD (paste or reference). This is the only required input.")
    prd = _load_prd()
    if not prd:
        console.print("[dim]Paste your PRD content. Press Ctrl-D when done.[/dim]")
        try:
            prd = sys.stdin.read()
        except KeyboardInterrupt:
            prd = ""
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
    
    console.print(f"✅ [bold blue]🌊 OCEAN:[/bold blue] Perfect! Moroni has clarified your vision.")
    
    # Show summary
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
    console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] Moroni has saved your project spec to {out}")


def _do_crew(log: Path) -> None:
    """OCEAN assembles and introduces the crew"""
    ensure_repo_structure()
    spec = _load_project_spec()
    if not spec:
        console.print("[yellow]⚠️ No project spec found. Run 'ocean clarify' first.[/yellow]")
        raise typer.Exit(code=1)
    
    write_log(log, "[OCEAN] Assembling crew for project:", json.dumps(spec))
    
    console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] Excellent! Now let me assemble my specialized crew for: {spec['name']}")
    console.print("[bold blue]🌊 OCEAN:[/bold blue] Each agent brings unique expertise to your project...\n")
    
    crew_table = Table(title="🤖 The OCEAN Crew (Assembled by OCEAN)")
    crew_table.add_column("Agent", style="cyan", no_wrap=True)
    crew_table.add_column("Role", style="blue")
    crew_table.add_column("Specialty", style="green")
    
    for agent in default_agents():
        intro = agent.introduce()
        console.print(f"🤖 {intro}")
        write_log(log, intro)
        
        # Parse agent info for table
        if "Moroni" in intro:
            crew_table.add_row("Moroni", "Architect & Brain", "Vision, Planning, Coordination")
        elif "Q" in intro:
            crew_table.add_row("Q", "Backend Engineer", "APIs, Services, Data Models")
        elif "Edna" in intro:
            crew_table.add_row("Edna", "Designer & UI/UX", "Interfaces, Design Systems")
        elif "Mario" in intro:
            crew_table.add_row("Mario", "DevOps & Infrastructure", "CI/CD, Deployment, Monitoring")
    
    console.print(crew_table)
    console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] Perfect! My crew is assembled and ready to work on your project.")
    # Explicit test-friendly line
    console.print("[green]Crew assembled[/green]")


def _do_plan(log: Path) -> None:
    """OCEAN coordinates the crew to generate project plan and backlog"""
    spec_dict = _load_project_spec()
    if not spec_dict:
        console.print("[yellow]⚠️ No project spec found. Run 'ocean clarify' first.[/yellow]")
        raise typer.Exit(code=1)
    
    spec = ProjectSpec.from_dict(spec_dict)
    
    console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] Now let me coordinate my crew to create your project plan...")
    console.print("[bold blue]🌊 OCEAN:[/bold blue] Moroni, Q, Edna, and Mario are analyzing your requirements...")
    
    # Generate backlog from agent proposals
    backlog = generate_backlog(spec)
    
    # EXECUTE the backlog using agent capabilities
    console.print(f"\n[bold blue]🌊 OCEAN:[/bold blue] My crew is now EXECUTING your project tasks...")
    bj, pm, runtime_summary = execute_backlog(backlog, DOCS, spec)
    
    write_log(log, f"[OCEAN] Crew completed planning and execution: {bj}")
    
    console.print(f"✅ [bold blue]🌊 OCEAN:[/bold blue] Excellent! My crew has created AND BUILT your project!")
    console.print(f"✅ [bold blue]🌊 OCEAN:[/bold blue] Backlog: {bj}")
    console.print(f"✅ [bold blue]🌊 OCEAN:[/bold blue] Plan summary: {pm}")
    if runtime_summary:
        console.print(f"🌐 [bold blue]🌊 OCEAN:[/bold blue] Local runtime: [green]{runtime_summary}[/green]")
        write_log(log, f"[OCEAN] Runtime: {runtime_summary}")
    
    # Show backlog summary
    backlog_table = Table(title="📋 Project Backlog (EXECUTED by OCEAN's Crew)")
    backlog_table.add_column("Task", style="cyan")
    backlog_table.add_column("Owner", style="blue")
    backlog_table.add_column("Files", style="green")
    
    for task in backlog:
        files_str = ", ".join(task.files_touched) if task.files_touched else "None"
        backlog_table.add_row(task.title, task.owner, files_str)
    
    console.print(backlog_table)
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
        subprocess.run([str(pip), "install", "--upgrade", "pip"], check=False)
        subprocess.run([str(pip), "install", "fastapi[all]", "uvicorn"], check=False)

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
    
    console.print("[yellow]⚠️ Live deployment not implemented. Use --dry-run or see docs/deploy.md[/yellow]")


@app.command(help="Show Codex MCP status")
def mcp():
    """Display MCP status and configuration."""
    s = MCP.status()
    table = Table(title="🔌 MCP Status")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("enabled", str(s["enabled"]))
    table.add_row("provider", s["provider"]) 
    for k, v in s.get("env", {}).items():
        table.add_row(k, v)
    console.print(table)

@app.command(help="Attempt MCP smoke test against 'codex mcp' and list tools")
def mcp_smoke():
    from .mcp import MCP
    from .mcp_client import StdioJsonRpcClient
    logs = LOGS
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / "mcp-smoke-rpc.log"
    client = StdioJsonRpcClient(log=log)
    try:
        client.start()
        client.initialize()
        tools = client.list_tools()
        table = Table(title="MCP Tools")
        table.add_column("name", style="cyan")
        table.add_column("desc", style="green")
        for t in tools:
            table.add_row(str(t.get("name")), (t.get("description") or "")[:80])
        console.print(table)
        console.print("✅ MCP smoke test OK")
    except Exception as e:
        console.print(f"❌ MCP smoke test failed: {e}")


if __name__ == "__main__":
    app()


def entrypoint():
    # If no args were provided, default to invoking the `chat` command via Typer
    # so that options get parsed/injected correctly (avoids OptionInfo default).
    if len(sys.argv) == 1:
        sys.argv.append("chat")
    app()


@app.command(help="Diagnose Codex MCP environment and readiness")
def doctor():
    _run_doctor_quick(full=True)


def _run_doctor_quick(full: bool = False) -> None:
    """Quick environment checks for Codex MCP.

    - Verifies codex on PATH
    - Shows codex --version
    - Attempts MCP smoke (initialize + list tools) with short timeout if full=True
    """
    table = Table(title="🔍 Ocean Doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")

    # PATH check
    codex_path = shutil.which("codex")
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

    # Auth check (best-effort)
    auth = "(unknown)"
    if codex_path:
        try:
            out = subprocess.run(["codex", "auth", "status"], capture_output=True, text=True, timeout=5)
            auth = (out.stdout or out.stderr).strip() or "ok"
        except Exception:
            auth = "run 'codex auth login'"
    table.add_row("codex auth", auth)

    # MCP smoke (short attempt)
    if full and codex_path:
        try:
            from .mcp_client import StdioJsonRpcClient
            log = LOGS / "mcp-smoke-rpc.log"
            client = StdioJsonRpcClient(log=log)
            client.start()
            client.initialize(timeout=8.0)
            tools = client.list_tools()
            table.add_row("MCP initialize", "ok")
            table.add_row("MCP tools", str(len(tools)))
        except Exception as e:
            table.add_row("MCP initialize", f"fail: {e}")
            table.add_row("MCP tools", "-")

    console.print(table)
