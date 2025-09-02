from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
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


def ensure_repo_structure() -> None:
    for p in [DOCS, LOGS, BACKEND, UI, DEVOPS, ROOT / ".github" / "workflows"]:
        p.mkdir(parents=True, exist_ok=True)


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


def _ask(label: str, default: str = "", choices: Optional[list[str]] = None) -> str:
    """Robust prompt helper.

    - Uses Rich Prompt in test mode (OCEAN_TEST=1) to remain patchable by tests.
    - Uses Typer's prompt in normal interactive runs for better TTY behavior.
    - Validates choices if provided.
    """
    import os as _os

    if _os.getenv("OCEAN_TEST") == "1":
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
def chat():
    """Main interactive conversation flow"""
    ensure_repo_structure()
    
    # Create session log
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log = LOGS / f"session-{timestamp}.log"
    write_log(log, "OCEAN session started", datetime.now().isoformat())
    
    # Print banner and initialize Codex MCP
    console.print(banner())
    MCP.ensure_started(log)
    
    console.print("\n[bold blue]🌊 OCEAN:[/bold blue] Hello! I'm OCEAN, your AI-powered software engineering orchestrator.")
    console.print("I'll help you build your project by coordinating with my specialized crew.")
    console.print("Let me start by understanding what you want to build...\n")
    
    # Do interactive prompts WITHOUT spinner to avoid input interference
    console.print("[dim]OCEAN is consulting with Moroni (Architect)…[/dim]")
    _do_clarify(log)

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
    console.print(f"\n🌊 [bold blue]OCEAN:[/bold blue] Your AI engineering team is ready! Use 'ocean init' to generate the scaffolds.")


def _do_clarify(log: Path) -> None:
    """OCEAN consults with Moroni to clarify the project vision"""
    ensure_repo_structure()
    
    console.print("[bold blue]🌊 OCEAN:[/bold blue] I’ll ask a few quick questions to understand what you want to build.")
    console.print("[dim]Note: I’m consulting Moroni (Architect) behind the scenes.[/dim]")
    
    # OCEAN/Moroni asks clarifying questions
    name = _ask("📝 🌊 OCEAN: Project name — What should we call this project?", default="My Project")
    kind = _ask(
        "🏗️ 🌊 OCEAN: Project type — What type of project is this?",
        choices=["web", "api", "cli", "mobile", "desktop"],
        default="web",
    )
    description = _ask("💭 🌊 OCEAN: Short description — Can you describe it in one line?", default="")
    goals = _ask("🎯 🌊 OCEAN: Goals — What are the primary goals?", default="prototype, learn, ship")
    constraints = _ask("⚠️ 🌊 OCEAN: Constraints — Any constraints I should know about?", default="")

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


if __name__ == "__main__":
    app()


def entrypoint():
    # Check if any command arguments were provided (excluding script name)
    # If only the script name is in argv, default to chat
    if len(sys.argv) == 1:
        # No command arguments provided, run the main interactive experience
        chat()
    else:
        # Command arguments provided, run the CLI app
        app()
