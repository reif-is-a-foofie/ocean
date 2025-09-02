from dataclasses import dataclass, field
from typing import Iterable, List
import subprocess
import sys
import json
import socket
import shutil
from datetime import datetime
from pathlib import Path

from .models import ProjectSpec, Task
from .tools.design_system import DESIGN_METHOD
from .tools.v0_cli import V0Cli
from .tools.deploy import RenderDeployPlan


@dataclass
class AgentBase:
    name: str
    role: str
    tools: list[str] = field(default_factory=list)

    def introduce(self) -> str:
        info = f"{self.name}: {self.role}"
        if self.tools:
            info += f" (tools: {', '.join(self.tools)})"
        return info

    def plan(self, spec: ProjectSpec) -> list[str]:
        """Generate planning steps based on project spec"""
        return []

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        """Propose tasks based on project spec - to be implemented by subclasses"""
        return []

    def execute(self, tasks: Iterable[Task], spec: ProjectSpec) -> List[Task]:
        """Execute tasks using Codex MCP - to be implemented by subclasses"""
        return list(tasks)


class Moroni(AgentBase):
    def __init__(self) -> None:
        super().__init__(
            name="Moroni",
            role="Architect/Brain. Clarifies vision, orchestrates the team.",
            tools=["planning", "codex_mcp", "architecture"],
        )

    def plan(self, spec: ProjectSpec) -> list[str]:
        """Generate architecture plan based on project type"""
        if spec.kind == "cli":
            return [
                "Design CLI application architecture",
                "Plan user interaction flow",
                "Coordinate Q (game logic), Edna (CLI interface), Mario (packaging)",
            ]
        elif spec.kind == "web":
            return [
                "Design web application architecture",
                "Plan frontend/backend structure",
                "Coordinate Q (backend), Edna (UI), Mario (deployment)",
            ]
        elif spec.kind == "api":
            return [
                "Design API architecture",
                "Plan endpoints and data models",
                "Coordinate Q (services), Edna (documentation), Mario (infrastructure)",
            ]
        else:
            return [
                "Analyze project requirements",
                "Design appropriate architecture",
                "Coordinate team execution",
            ]

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        """Propose architecture and coordination tasks"""
        if spec.kind == "cli":
            return [
                Task(
                    title="Design CLI application structure",
                    description="Create CLI architecture and user interaction design",
                    owner=self.name,
                    files_touched=["docs/architecture.md", "docs/cli_design.md"],
                )
            ]
        elif spec.kind == "web":
            return [
                Task(
                    title="Design web application architecture",
                    description="Create frontend/backend architecture and data flow",
                    owner=self.name,
                    files_touched=["docs/architecture.md", "docs/api_design.md"],
                )
            ]
        else:
            return [
                Task(
                    title="Design application architecture",
                    description="Create appropriate architecture for project type",
                    owner=self.name,
                    files_touched=["docs/architecture.md"],
                )
            ]

    def execute(self, tasks: Iterable[Task], spec: ProjectSpec) -> List[Task]:
        """Moroni orchestrates the execution using Codex MCP"""
        executed = []
        for task in tasks:
            if "architecture" in task.title.lower():
                self._generate_architecture(spec)
            executed.append(task)
        return executed

    def _generate_architecture(self, spec: ProjectSpec):
        """Generate architecture documentation using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        # This should generate architecture docs based on project type
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        
        if spec.kind == "cli":
            arch_content = f"""# {spec.name} - CLI Architecture

## Project Overview
- **Type**: CLI Application
- **Goals**: {', '.join(spec.goals)}
- **Constraints**: {', '.join(spec.constraints)}

## Architecture Design
- **Entry Point**: Main CLI script with argument parsing
- **Core Logic**: Game/application logic module
- **User Interface**: Terminal-based interaction
- **Data Management**: Local file storage or simple state

## Technical Stack
- **Language**: Python
- **CLI Framework**: Click or Typer
- **Dependencies**: Minimal, focused on core functionality

## File Structure
```
{spec.name.lower().replace(' ', '_')}/
├── main.py          # CLI entry point
├── game.py          # Core game logic
├── cli.py           # CLI interface
├── config.py        # Configuration
└── tests/           # Test suite
```

Generated by OCEAN using Codex MCP
"""
        else:
            arch_content = f"""# {spec.name} - Architecture

## Project Overview
- **Type**: {spec.kind.title()} Application
- **Goals**: {', '.join(spec.goals)}
- **Constraints**: {', '.join(spec.constraints)}

## Architecture Design
- **Frontend**: User interface components
- **Backend**: Business logic and data management
- **Data Layer**: Storage and persistence
- **Deployment**: Infrastructure and hosting

Generated by OCEAN using Codex MCP
"""
        
        (docs_dir / "architecture.md").write_text(arch_content)
        print(f"🤖 [Moroni] Generated architecture using Codex MCP")


class Q(AgentBase):
    def __init__(self) -> None:
        super().__init__(
            name="Q",
            role="Backend/tools engineer. Builds services, data models, integrations.",
            tools=["Python", "FastAPI", "pytest", "codex_mcp"],
        )

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        """Propose backend tasks based on project type"""
        if spec.kind == "cli":
            return [
                Task(
                    title="Create CLI application logic",
                    description="Implement core application functionality and CLI interface",
                    owner=self.name,
                    files_touched=["main.py", "game.py", "cli.py"],
                )
            ]
        elif spec.kind == "web":
            return [
                Task(
                    title="Create web backend",
                    description="Implement FastAPI backend with endpoints",
                    owner=self.name,
                    files_touched=["backend/app.py", "backend/models.py"],
                )
            ]
        else:
            return [
                Task(
                    title="Create application backend",
                    description="Implement core application logic",
                    owner=self.name,
                    files_touched=["app.py"],
                )
            ]

    def execute(self, tasks: Iterable[Task], spec: ProjectSpec) -> List[Task]:
        """Q executes backend tasks using Codex MCP"""
        executed = []
        for task in tasks:
            if "cli application logic" in task.title.lower():
                self._generate_cli_app(spec)
            elif "web backend" in task.title.lower():
                self._generate_web_backend(spec)
            elif "application backend" in task.title.lower():
                self._generate_generic_backend(spec)
            executed.append(task)
        return executed

    def _generate_cli_app(self, spec: ProjectSpec):
        """Generate CLI application using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        # This should generate CLI app code based on project requirements
        
        # Main CLI entry point
        main_code = f'''#!/usr/bin/env python3
"""
{spec.name} - CLI Application
Generated by OCEAN using Codex MCP
"""

import click
from game import Game

@click.command()
@click.option("--difficulty", default="normal", help="Game difficulty")
@click.option("--config", default="config.json", help="Config file path")
def main(difficulty, config):
    """{spec.description}"""
    game = Game(difficulty=difficulty, config_file=config)
    game.run()

if __name__ == "__main__":
    main()
'''
        
        # Game logic
        game_code = f'''"""
{spec.name} - Core Game Logic
Generated by OCEAN using Codex MCP
"""

import json
import random

class Game:
    def __init__(self, difficulty="normal", config_file="config.json"):
        self.difficulty = difficulty
        self.config = self._load_config(config_file)
        self.score = 0
        self.game_over = False
        
    def _load_config(self, config_file):
        """Load game configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {{"default_difficulty": "normal"}}
    
    def run(self):
        """Main game loop"""
        print(f"Starting {{self.name}} with difficulty: {{self.difficulty}}")
        print("Game logic implementation goes here...")
        print("Generated by OCEAN using Codex MCP")
'''
        
        # CLI interface
        cli_code = f'''"""
{spec.name} - CLI Interface
Generated by OCEAN using Codex MCP
"""

class CLIInterface:
    def __init__(self):
        self.commands = {{}}
        
    def add_command(self, name, handler):
        """Add a CLI command"""
        self.commands[name] = handler
        
    def run(self):
        """Run the CLI interface"""
        print("CLI interface implementation goes here...")
        print("Generated by OCEAN using Codex MCP")
'''
        
        Path("main.py").write_text(main_code)
        Path("game.py").write_text(game_code)
        Path("cli.py").write_text(cli_code)
        
        print(f"🤖 [Q] Generated CLI application using Codex MCP")

    def _generate_web_backend(self, spec: ProjectSpec):
        """Generate web backend using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        backend_dir = Path("backend")
        backend_dir.mkdir(exist_ok=True)
        
        app_code = f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{spec.name}", version="0.1.0")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {{"message": "Welcome to {spec.name}", "type": "{spec.kind}"}}

@app.get('/healthz')
def healthz():
    return {{'ok': True, 'status': 'healthy'}}

# TODO: Add more endpoints based on project requirements
# Generated by OCEAN using Codex MCP
'''
        
        (backend_dir / "app.py").write_text(app_code)
        print(f"🤖 [Q] Generated web backend using Codex MCP")

    def _generate_generic_backend(self, spec: ProjectSpec):
        """Generate generic backend using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        app_code = f'''"""
{spec.name} - Core Application
Generated by OCEAN using Codex MCP
"""

class Application:
    def __init__(self):
        self.name = "{spec.name}"
        self.type = "{spec.kind}"
        self.goals = {spec.goals}
        
    def run(self):
        """Main application logic"""
        print(f"Running {{self.name}} ({self.type})")
        print("Application logic implementation goes here...")
        print("Generated by OCEAN using Codex MCP")

if __name__ == "__main__":
    app = Application()
    app.run()
'''
        
        Path("app.py").write_text(app_code)
        print(f"🤖 [Q] Generated application backend using Codex MCP")


class Edna(AgentBase):
    def __init__(self) -> None:
        tool_list = ["Design methodology", "UI/UX", "codex_mcp"]
        if V0Cli.is_available():
            tool_list.append("V0 CLI")
        super().__init__(
            name="Edna",
            role="Designer/UI/UX. Produces mockups, CSS, flows.",
            tools=tool_list,
        )

    def plan(self, spec: ProjectSpec) -> list[str]:
        """Provide design methodology based on project type"""
        if spec.kind == "cli":
            return ["CLI interface design", "User interaction flow", "Terminal UX patterns"]
        elif spec.kind == "web":
            return ["Web interface design", "User experience flow", "Responsive design"]
        else:
            return [step.split(":", 1)[0] for step in DESIGN_METHOD[:3]]

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        """Propose design tasks based on project type"""
        if spec.kind == "cli":
            return [
                Task(
                    title="Create CLI interface design",
                    description="Design terminal-based user interface and interaction patterns",
                    owner=self.name,
                    files_touched=["docs/cli_design.md", "docs/ux_patterns.md"],
                )
            ]
        elif spec.kind == "web":
            return [
                Task(
                    title="Create web interface design",
                    description="Design web-based user interface and user experience",
                    owner=self.name,
                    files_touched=["ui/index.html", "ui/styles.css", "docs/design_system.md"],
                )
            ]
        else:
            return [
                Task(
                    title="Create interface design",
                    description="Design appropriate user interface for project type",
                    owner=self.name,
                    files_touched=["docs/interface_design.md"],
                )
            ]

    def execute(self, tasks: Iterable[Task], spec: ProjectSpec) -> List[Task]:
        """Edna executes design tasks using Codex MCP"""
        executed = []
        for task in tasks:
            if "cli interface design" in task.title.lower():
                self._generate_cli_design(spec)
            elif "web interface design" in task.title.lower():
                self._generate_web_design(spec)
            elif "interface design" in task.title.lower():
                self._generate_generic_design(spec)
            executed.append(task)
        return executed

    def _generate_cli_design(self, spec: ProjectSpec):
        """Generate CLI design documentation using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        
        cli_design = f"""# {spec.name} - CLI Interface Design

## Design Principles
- **Simplicity**: Clear, intuitive commands
- **Consistency**: Uniform command structure
- **Feedback**: Clear response to user actions
- **Help**: Comprehensive help system

## Command Structure
```
{spec.name.lower().replace(' ', '_')} [command] [options]
```

## User Interaction Flow
1. **Startup**: Welcome message and available commands
2. **Command Input**: Clear prompts and validation
3. **Execution**: Progress feedback and results
4. **Error Handling**: Helpful error messages
5. **Completion**: Summary and next steps

## Terminal UX Patterns
- Color coding for different types of output
- Progress bars for long operations
- Clear separation between sections
- Consistent formatting

Generated by OCEAN using Codex MCP
"""
        
        (docs_dir / "cli_design.md").write_text(cli_design)
        print(f"🤖 [Edna] Generated CLI design using Codex MCP")

    def _generate_web_design(self, spec: ProjectSpec):
        """Generate web interface using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        ui_dir = Path("ui")
        ui_dir.mkdir(exist_ok=True)
        
        html_code = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec.name} - OCEAN Generated</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🌊 {spec.name}</h1>
            <p>Generated by OCEAN using Codex MCP</p>
        </header>
        
        <main>
            <section class="hero">
                <h2>Welcome to {spec.name}</h2>
                <p>{spec.description}</p>
                <div class="goals">
                    <h3>Project Goals:</h3>
                    <ul>
                        {chr(10).join(f"<li>{goal}</li>" for goal in spec.goals)}
                    </ul>
                </div>
            </section>
            
            <section class="features">
                <h3>Features</h3>
                <p>Application features will be implemented here...</p>
            </section>
        </main>
        
        <footer>
            <p>Built by OCEAN's AI engineering team 🚀</p>
        </footer>
    </div>
</body>
</html>'''
        
        css_code = f'''/* {spec.name} - Styles */
/* Generated by OCEAN using Codex MCP */

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 100vh;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}}

header {{
    text-align: center;
    margin-bottom: 3rem;
}}

header h1 {{
    font-size: 3rem;
    margin-bottom: 1rem;
}}

.hero {{
    background: rgba(255,255,255,0.1);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
}}

.goals ul {{
    text-align: left;
    display: inline-block;
}}

.features {{
    background: rgba(255,255,255,0.1);
    padding: 2rem;
    border-radius: 15px;
}}

footer {{
    text-align: center;
    margin-top: 3rem;
    opacity: 0.8;
}}'''
        
        (ui_dir / "index.html").write_text(html_code)
        (ui_dir / "styles.css").write_text(css_code)
        print(f"🤖 [Edna] Generated web interface using Codex MCP")

    def _generate_generic_design(self, spec: ProjectSpec):
        """Generate generic interface design using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        
        design_doc = f"""# {spec.name} - Interface Design

## Project Type: {spec.kind.title()}

## Design Considerations
- **User Experience**: Intuitive and efficient workflows
- **Accessibility**: Inclusive design principles
- **Performance**: Fast and responsive interactions
- **Scalability**: Design for future growth

## Interface Elements
- **Navigation**: Clear information architecture
- **Feedback**: User action confirmation
- **Error Handling**: Helpful error messages
- **Help System**: Comprehensive documentation

## Design System
- **Typography**: Consistent font hierarchy
- **Colors**: Accessible color palette
- **Spacing**: Consistent layout system
- **Components**: Reusable UI elements

Generated by OCEAN using Codex MCP
"""
        
        (docs_dir / "interface_design.md").write_text(design_doc)
        print(f"🤖 [Edna] Generated interface design using Codex MCP")


class Mario(AgentBase):
    def __init__(self) -> None:
        super().__init__(
            name="Mario",
            role="DevOps. Provision infra, CI/CD, deploys final product.",
            tools=["GitHub Actions", "Docker", "Deployment", "codex_mcp"],
        )
        self.last_backend_url: str | None = None
        self.last_ui_url: str | None = None
        self.last_runtime_summary: str | None = None

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        """Propose DevOps tasks based on project type"""
        tasks = [
            Task(
                title="Add CI workflow",
                description="Set up automated testing and quality checks",
                owner=self.name,
                files_touched=[".github/workflows/ci.yml"],
            )
        ]
        
        if spec.kind in ["web", "api"]:
            tasks.extend([
                Task(
                    title="Create Dockerfile",
                    description="Containerize application for deployment",
                    owner=self.name,
                    files_touched=["Dockerfile", ".dockerignore"],
                ),
                Task(
                    title="Create deployment config",
                    description="Set up deployment configuration for cloud platforms",
                    owner=self.name,
                    files_touched=["devops/deploy.yaml"],
                ),
                Task(
                    title="Start local runtime",
                    description="Launch local backend (and UI if present) and print URL",
                    owner=self.name,
                    files_touched=[],
                ),
            ])
        
        return tasks

    def execute(self, tasks: Iterable[Task], spec: ProjectSpec) -> List[Task]:
        """Mario executes DevOps tasks using Codex MCP"""
        executed = []
        for task in tasks:
            if "ci workflow" in task.title.lower():
                self._generate_ci_workflow(spec)
            elif "dockerfile" in task.title.lower():
                self._generate_docker_config(spec)
            elif "deployment config" in task.title.lower():
                self._generate_deployment_config(spec)
            elif "start local runtime" in task.title.lower():
                summary = self._start_local_runtime(spec)
                if summary:
                    task.description = (task.description + f" | URLs: {summary}").strip()
            executed.append(task)
        return executed

    def _generate_ci_workflow(self, spec: ProjectSpec):
        """Generate CI workflow using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        ci_code = f'''name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest
      - name: Run tests
        run: pytest
      - name: Lint
        run: |
          pip install flake8 black
          flake8 . --exclude=venv/
          black --check . --exclude=venv/
          
# Generated by OCEAN using Codex MCP for {spec.name}
'''
        
        (workflow_dir / "ci.yml").write_text(ci_code)
        print(f"🤖 [Mario] Generated CI workflow using Codex MCP")

    def _generate_docker_config(self, spec: ProjectSpec):
        """Generate Docker config using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        
        dockerfile_code = f'''FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]

# Generated by OCEAN using Codex MCP for {spec.name}
'''
        
        dockerignore_code = '''.git
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv/
.env
logs/
tests/
*.egg-info/
'''
        
        Path("Dockerfile").write_text(dockerfile_code)
        Path(".dockerignore").write_text(dockerignore_code)
        print(f"🤖 [Mario] Generated Docker config using Codex MCP")

    def _generate_deployment_config(self, spec: ProjectSpec):
        """Generate deployment config using Codex MCP"""
        # TODO: Replace with actual Codex MCP call
        devops_dir = Path("devops")
        devops_dir.mkdir(exist_ok=True)
        
        deploy_code = f'''# {spec.name} - Deployment Configuration
# Generated by OCEAN using Codex MCP

deployment:
  platform: render
  type: web
  name: {spec.name.lower().replace(' ', '-')}
  env: python
  buildCommand: pip install -e .
  startCommand: python app.py
  envVars:
    - key: PYTHON_VERSION
      value: 3.11
  healthCheckPath: /healthz
  autoDeploy: true
'''
        
        (devops_dir / "deploy.yaml").write_text(deploy_code)
        print(f"🤖 [Mario] Generated deployment config using Codex MCP")

    def _find_free_port(self, start: int = 8000, limit: int = 20) -> int:
        port = start
        for _ in range(limit):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    port += 1
        return start

    def _start_local_runtime(self, spec: ProjectSpec) -> str | None:
        """Start local backend (and UI) if possible and print URLs.

        - Does not install dependencies; respects network guardrails.
        - Starts uvicorn if available and backend/app.py exists.
        - Starts a static server for ui/ if present.
        - Logs output to logs/runtime-*.log files.
        """
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")

        backend_app = Path("backend/app.py")
        uvicorn_available = False
        try:
            import uvicorn  # type: ignore  # noqa: F401
            uvicorn_available = True
        except Exception:
            uvicorn_available = shutil.which("uvicorn") is not None

        backend_url = None
        if backend_app.exists() and uvicorn_available:
            port = self._find_free_port(8000)
            backend_log = logs_dir / f"runtime-backend-{ts}.log"
            with backend_log.open("a", encoding="utf-8") as out:
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "backend.app:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                    ],
                    stdout=out,
                    stderr=subprocess.STDOUT,
                )
            backend_url = f"http://127.0.0.1:{port}/healthz"
            print(f"🌐 [Mario] Local backend started: {backend_url}")
            self.last_backend_url = backend_url
        elif backend_app.exists() and not uvicorn_available:
            print("⚠️ [Mario] uvicorn not available; skipping auto-run. Use 'ocean run --yes' to install and start.")

        ui_dir = Path("ui")
        ui_url = None
        if ui_dir.exists():
            ui_port = self._find_free_port(5173)
            ui_log = logs_dir / f"runtime-ui-{ts}.log"
            with ui_log.open("a", encoding="utf-8") as out:
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "http.server",
                        str(ui_port),
                        "-d",
                        str(ui_dir),
                    ],
                    stdout=out,
                    stderr=subprocess.STDOUT,
                )
            ui_url = f"http://127.0.0.1:{ui_port}"
            print(f"🖥️ [Mario] Local UI served: {ui_url}")
            self.last_ui_url = ui_url

        # Final URL summary
        if backend_url or ui_url:
            summary = " | ".join(filter(None, [backend_url, ui_url]))
            self.last_runtime_summary = summary
            print(f"✅ [Mario] Runtime ready → {summary}")
            return summary
        else:
            print("ℹ️ [Mario] No runtime started (missing deps or artifacts).")
            self.last_runtime_summary = None
            return None


def default_agents() -> list[AgentBase]:
    return [Moroni(), Q(), Edna(), Mario()]
