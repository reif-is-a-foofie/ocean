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

from . import __version__
from .agents import default_agents
from .models import ProjectSpec
from .planner import generate_backlog, write_backlog


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


@app.callback()
def main(version: Optional[bool] = typer.Option(None, "--version", help="Show version and exit", is_eager=True)):
    if version:
        rprint(f"ocean {__version__}")
        raise typer.Exit(code=0)


@app.command(help="Run the interactive flow: clarify -> crew intros")
def chat():
    ensure_repo_structure()
    log = session_log_path()
    rprint(Panel.fit(banner(), title="OCEAN"))
    write_log(log, "OCEAN session started", datetime.now().isoformat())
    typer.echo("Starting vision clarification…")
    _do_clarify(log)
    typer.echo("\nSpinning up the crew…")
    _do_crew(log)
    typer.echo("\nDrafting the initial plan and backlog…")
    _do_plan(log)
    typer.echo(f"\nDone. Log: {log}")


def _do_clarify(log: Path) -> None:
    ensure_repo_structure()
    name = typer.prompt("Project name", default="My Project")
    kind = typer.prompt("Project type (web/api/cli)", default="web")
    description = typer.prompt("One-line description", default="")
    goals = typer.prompt("Primary goals (comma-separated)", default="prototype, learn, ship")
    constraints = typer.prompt("Constraints (comma-separated)", default="")

    spec = {
        "name": name.strip(),
        "kind": kind.strip().lower(),
        "description": description.strip(),
        "goals": [g.strip() for g in goals.split(",") if g.strip()],
        "constraints": [c.strip() for c in constraints.split(",") if c.strip()],
        "createdAt": datetime.now().isoformat(),
    }
    out = _save_project_spec(spec)
    write_log(log, "[Moroni] Clarification complete.", json.dumps(spec))
    rprint(f"Saved project spec to [bold]{out}[/bold]")


@app.command(help="Ask clarifying questions and save docs/project.json")
def clarify():
    log = session_log_path()
    _do_clarify(log)


def _do_crew(log: Path) -> None:
    ensure_repo_structure()
    spec = _load_project_spec()
    if not spec:
        rprint("[yellow]No project spec found. Run `ocean clarify` first.[/yellow]")
        raise typer.Exit(code=1)
    write_log(log, "[System] Crew spin-up for project:", json.dumps(spec))
    for agent in default_agents():
        line = agent.introduce()
        rprint(line)
        write_log(log, line)
    rprint(f"Intros logged to {log}")


def _do_plan(log: Path) -> None:
    spec_dict = _load_project_spec()
    if not spec_dict:
        rprint("[yellow]No project spec found. Run `ocean clarify` first.[/yellow]")
        raise typer.Exit(code=1)
    spec = ProjectSpec.from_dict(spec_dict)
    backlog = generate_backlog(spec)
    bj, pm = write_backlog(backlog, DOCS)
    write_log(log, f"[Moroni] Backlog created: {bj}")
    rprint(f"Backlog written to [bold]{bj}[/bold]\nPlan summary: [bold]{pm}[/bold]")


@app.command(help="Print agent introductions and log them")
def crew():
    log = session_log_path()
    _do_crew(log)


@app.command(help="Generate/refresh scaffolds for backend, UI, CI, docs")
def init(force: bool = typer.Option(False, "--force", help="Overwrite existing files")):
    ensure_repo_structure()
    created: list[str] = []

    # Backend FastAPI app
    backend_app = BACKEND / "app.py"
    if force or not backend_app.exists():
        backend_app.write_text(
            (
                "from fastapi import FastAPI\n\n"
                "app = FastAPI()\n\n"
                "@app.get('/healthz')\n"
                "def healthz():\n"
                "    return {'ok': True}\n"
            ),
            encoding="utf-8",
        )
        created.append(str(backend_app))

    # UI placeholder
    ui_index = UI / "index.html"
    if force or not ui_index.exists():
        ui_index.write_text(
            (
                "<!doctype html>\n<html>\n<head><meta charset='utf-8'><title>OCEAN UI</title></head>\n"
                "<body>\n<h1>OCEAN UI Placeholder</h1>\n<p>Edit ui/index.html to begin.</p>\n</body>\n</html>\n"
            ),
            encoding="utf-8",
        )
        created.append(str(ui_index))
    # UI styleguide from design tokens
    ui_styleguide = UI / "styleguide.html"
    if force or not ui_styleguide.exists():
        from .tools.design_system import DESIGN_TOKENS

        css_vars = "\n".join(
            [f"  --{k.replace('.', '-')}: {v};" for k, v in DESIGN_TOKENS.items()]
        )
        ui_styleguide.write_text(
            (
                "<!doctype html>\n<html>\n<head><meta charset='utf-8'><title>Styleguide</title>\n"
                "<style>:root{\n" + css_vars + "\n} body{font-family:system-ui;margin:2rem}</style>\n"
                "</head><body><h1>Design Tokens</h1><ul>\n"
                + "\n".join([f"<li><code>{k}</code> = <span>{v}</span></li>" for k, v in DESIGN_TOKENS.items()])
                + "\n</ul></body></html>\n"
            ),
            encoding="utf-8",
        )
        created.append(str(ui_styleguide))

    # Docs
    first_sprint = DOCS / "first_sprint.md"
    if force or not first_sprint.exists():
        first_sprint.write_text(
            (
                "# First Sprint\n\n"
                "- Run backend: `uvicorn backend.app:app --reload`\n\n"
                "- Open UI: just open `ui/index.html` in a browser or serve via `python -m http.server -d ui 5173`\n"
            ),
            encoding="utf-8",
        )
        created.append(str(first_sprint))

    # CI workflow
    wf = ROOT / ".github" / "workflows" / "ci.yml"
    if force or not wf.exists():
        wf.write_text(
            (
                "name: CI\n"
                "on: [push, pull_request]\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n"
                "      - uses: actions/setup-python@v5\n"
                "        with:\n"
                "          python-version: '3.11'\n"
                "      - name: Install\n"
                "        run: pip install -e .\n"
                "      - name: Test\n"
                "        run: pytest\n"
            ),
            encoding="utf-8",
        )
        created.append(str(wf))

    # Tests
    tests_dir = BACKEND / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_file = tests_dir / "test_healthz.py"
    if force or not test_file.exists():
        test_file.write_text(
            (
                "from fastapi.testclient import TestClient\n"
                "from backend.app import app\n\n"
                "def test_healthz():\n"
                "    client = TestClient(app)\n"
                "    r = client.get('/healthz')\n"
                "    assert r.status_code == 200\n"
                "    assert r.json() == {'ok': True}\n"
            ),
            encoding="utf-8",
        )
        created.append(str(test_file))

    # Docker files
    dockerfile = ROOT / "Dockerfile"
    if force or not dockerfile.exists():
        dockerfile.write_text(
            (
                "FROM python:3.11-slim\n"
                "WORKDIR /app\n"
                "COPY pyproject.toml .\n"
                "RUN pip install --no-cache-dir -e .\n"
                "COPY backend backend\n"
                "EXPOSE 8000\n"
                "CMD [\"uvicorn\", \"backend.app:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"
            ),
            encoding="utf-8",
        )
        created.append(str(dockerfile))

    dockerignore = ROOT / ".dockerignore"
    if force or not dockerignore.exists():
        dockerignore.write_text(".git\n__pycache__/\n*.pyc\nlogs/\n.ui/\nvenv/\n.env\n", encoding="utf-8")
        created.append(str(dockerignore))

    # Devops placeholders
    render = DEVOPS / "render.yaml"
    if force or not render.exists():
        render.write_text(
            (
                "# Placeholder Render spec\n"
                "# TODO: Fill in environment and build steps\n"
                "services:\n  - type: web\n    name: ocean-backend\n    env: python\n    buildCommand: pip install -e .\n    startCommand: uvicorn backend.app:app --host 0.0.0.0 --port 8000\n"
            ),
            encoding="utf-8",
        )
        created.append(str(render))

    rprint("Created/updated:\n- " + "\n- ".join(created) if created else "Nothing to do.")


@app.command(help="Run backend tests via pytest")
def test():  # noqa: A001 - command name
    ensure_repo_structure()
    try:
        code = subprocess.call([sys.executable, "-m", "pytest"])  # inherit stdio
        raise typer.Exit(code=code)
    except FileNotFoundError:
        rprint("[red]pytest not found. Install project dependencies first.[/red]")
        raise typer.Exit(code=1)


@app.command(help="Run the backend API locally (uvicorn)")
def run(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    ensure_repo_structure()
    args = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        args.append("--reload")
    rprint(f"Starting uvicorn at http://{host}:{port}")
    os.execv(sys.executable, args)


@app.command(help="Show a dry-run deployment plan")
def deploy(dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Preview steps only")):
    ensure_repo_structure()
    if dry_run:
        rprint(
            "\n".join(
                [
                    "Deployment dry-run plan:",
                    "- Build Docker image `ocean:latest`",
                    "- Push to registry (configure REGISTRY_URL, REGISTRY_TOKEN)",
                    "- Provision service (Render/Railway) with env vars",
                    "- Set start command: uvicorn backend.app:app",
                    "- Expose port 8000, verify /healthz",
                ]
            )
        )
        return
    rprint("[yellow]No live deploy implementation. Use --dry-run or see docs/deploy.md[/yellow]")


if __name__ == "__main__":
    app()


def entrypoint():
    # Default to conversation flow if no args provided
    if len(sys.argv) == 1:
        chat()
    else:
        app()
