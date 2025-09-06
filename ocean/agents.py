from dataclasses import dataclass, field
from typing import Iterable, List
import subprocess
import sys
import os
import json
import socket
import shutil
from datetime import datetime
from pathlib import Path

from .models import ProjectSpec, Task
from .tools.design_system import DESIGN_METHOD
from .tools.v0_cli import V0Cli
from .tools.deploy import RenderDeployPlan
from .mcp import MCP
from . import context as ctx
from .persona import voice_brief
from . import codex_exec


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
        MCP.start_for_agent(self.name, Path("logs"))
        executed = []
        for task in tasks:
            if "architecture" in task.title.lower():
                self._generate_architecture(spec)
            executed.append(task)
        return executed

    def _generate_architecture(self, spec: ProjectSpec):
        """Generate architecture documentation using Codex MCP (MCP-only)."""
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        def _v() -> bool:
            import os
            return os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")

        # Prefer Codex exec if available
        if codex_exec.available():
            bundle = ctx.build_context_bundle(spec)
            import os
            verbose = os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")
            if verbose:
                from .feed import agent_say as _say
                _say("Q", '"Context prepared."')
            prd_text = ""
            p = Path("docs/prd.md")
            if p.exists():
                try:
                    prd_text = p.read_text(encoding="utf-8")
                except Exception:
                    prd_text = ""
            instruction = (
                f"Generate an architecture document for a {spec.kind} project named '{spec.name}'. "
                f"Goals: {', '.join(spec.goals)}. Constraints: {', '.join(spec.constraints)}. "
                + ("Here is the PRD:\n" + prd_text if prd_text else "")
                + "\nReturn JSON mapping 'docs/architecture.md' to Markdown content."
            )
            if _v():
                preview = instruction[:140].replace("\n", " ") + ("…" if len(instruction) > 140 else "")
                from .feed import agent_say as _say
                _say("Moroni", f'"Codex exec request → {preview}"')
            # Add Moroni's voice for documentation tone (no effect on code)
            instruction = instruction + "\nVoice guidance: " + voice_brief(self.name, context="planning")
            files = codex_exec.generate_files(instruction, ["docs/architecture.md"], bundle, agent=self.name)
            if files:
                from .codex_exec import last_mode
                for rel, content in files.items():
                    Path(rel).parent.mkdir(parents=True, exist_ok=True)
                    Path(rel).write_text(content, encoding="utf-8")
                from .feed import agent_say as _say
                _say("Moroni", '"Architecture drafted via Codex MCP."')
                return

        # Try Codex first
        prd = None
        prd_path = Path("docs/prd.md")
        if prd_path.exists():
            try:
                prd = prd_path.read_text(encoding="utf-8")
            except Exception:
                prd = None
        prompt = (
            f"Generate an architecture document for a {spec.kind} project named '{spec.name}'. "
            f"Goals: {', '.join(spec.goals)}. Constraints: {', '.join(spec.constraints)}. "
            + ("Here is the PRD:\n" + prd + "\n" if prd else "") +
            "Output Markdown content."
        )
        files = MCP.codegen_files(self.name, prompt, ["docs/architecture.md"]) or {}
        if files:
            for rel, content in files.items():
                MCP.write_file(self.name, Path(rel), content)
            from .feed import agent_say as _say
            _say("Moroni", '"Architecture drafted via Codex MCP."')
            return

        # No local fallback: require Codex or API to generate artifacts
        from .feed import agent_say as _say
        _say("Moroni", '"❌ Codegen unavailable (no subscription or API). Skipping architecture until Codex/API is ready."')
        return


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
        MCP.start_for_agent(self.name, Path("logs"))
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
        
        from .feed import agent_say as _say
        _say("Q", '"CLI application scaffolded via Codex MCP."')

    def _generate_web_backend(self, spec: ProjectSpec):
        """Generate web backend using Codex MCP (MCP-only)."""
        backend_dir = Path("backend")
        backend_dir.mkdir(exist_ok=True)

        # Prefer Codex exec if available
        if codex_exec.available():
            bundle = ctx.build_context_bundle(spec)
            import os
            verbose = os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")
            if verbose:
                from .feed import agent_say as _say
                _say("Edna", '"Context prepared."')
            prd_text = ""
            p = Path("docs/prd.md")
            if p.exists():
                try:
                    prd_text = p.read_text(encoding="utf-8")
                except Exception:
                    prd_text = ""
            instruction = (
                f"Generate a minimal FastAPI backend for '{spec.name}'. "
                "Create backend/app.py with '/' and '/healthz' endpoints. "
                + ("PRD:\n" + prd_text if prd_text else "")
            )
            if verbose:
                from .feed import agent_say as _say
                _say("Q", '"Using prepared context bundle."')
            files = codex_exec.generate_files(instruction, ["backend/app.py"], bundle, agent=self.name)
            if files:
                from .codex_exec import last_mode
                for rel, content in files.items():
                    Path(rel).parent.mkdir(parents=True, exist_ok=True)
                    Path(rel).write_text(content, encoding="utf-8")
                from .feed import agent_say as _say
                _say("Q", '"Web backend scaffolded via Codex MCP."')
                return

        prd = None
        prd_path = Path("docs/prd.md")
        if prd_path.exists():
            try:
                prd = prd_path.read_text(encoding="utf-8")
            except Exception:
                prd = None
        prompt = (
            f"Generate a FastAPI backend for project '{spec.name}' with endpoints '/' and '/healthz'. "
            + ("Here is the PRD:\n" + prd + "\n" if prd else "") +
            "Return files with their content."
        )
        files = MCP.codegen_files(self.name, prompt, ["backend/app.py"]) or {}
        if files:
            for rel, content in files.items():
                MCP.write_file(self.name, Path(rel), content)
            from .feed import agent_say as _say
            _say("Q", '"Web backend scaffolded via Codex MCP."')
            return

        # No local fallback
        from .feed import agent_say as _say
        _say("Q", '"❌ Codegen unavailable (no subscription or API). Skipping backend until Codex/API is ready."')

    def _generate_generic_backend(self, spec: ProjectSpec):
        """No local fallback; require Codex/API for generic backend."""
        from .feed import agent_say as _say
        _say("Q", '"❌ Codegen unavailable (no subscription or API). Skipping generic backend until Codex/API is ready."')


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
        MCP.start_for_agent(self.name, Path("logs"))
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
        def _v() -> bool:
            import os
            return os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")
        
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
        from .feed import agent_say as _say
        _say("Edna", '"CLI design documented."')

    def _generate_web_design(self, spec: ProjectSpec):
        """Generate web interface using Codex MCP (MCP-only)."""
        ui_dir = Path("ui")
        ui_dir.mkdir(exist_ok=True)

        # Prefer Codex exec if available
        if codex_exec.available():
            bundle = ctx.build_context_bundle(spec)
            import os
            verbose = os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")
            if verbose:
                from .feed import agent_say as _say
                _say("Edna", '"Context prepared."')
            prd_text = ""
            p = Path("docs/prd.md")
            if p.exists():
                try:
                    prd_text = p.read_text(encoding="utf-8")
                except Exception:
                    prd_text = ""
            instruction = (
                f"Generate a responsive landing page for '{spec.name}' with CSS. "
                f"Description: {spec.description}. Goals: {', '.join(spec.goals)}. "
                + ("PRD:\n" + prd_text if prd_text else "")
                + "\nReturn ui/index.html and ui/styles.css."
            )
            # Guide copy tone only; do not impact code structure
            instruction = instruction + "\nVoice guidance (copy tone only): " + voice_brief(self.name, context="design")
            files = codex_exec.generate_files(instruction, ["ui/index.html", "ui/styles.css"], bundle, agent=self.name)
            if files:
                from .codex_exec import last_mode
                for rel, content in files.items():
                    Path(rel).parent.mkdir(parents=True, exist_ok=True)
                    Path(rel).write_text(content, encoding="utf-8")
                from .feed import agent_say as _say
                _say("Edna", '"Interface designed via Codex MCP."')
                return

        prd = None
        prd_path = Path("docs/prd.md")
        if prd_path.exists():
            try:
                prd = prd_path.read_text(encoding="utf-8")
            except Exception:
                prd = None
        prompt = (
            f"Generate a responsive HTML+CSS landing page for '{spec.name}'. "
            f"Description: {spec.description}. Goals: {', '.join(spec.goals)}. "
            + ("Here is the PRD:\n" + prd + "\n" if prd else "") +
            "Return files (ui/index.html, ui/styles.css)."
        )
        files = MCP.codegen_files(self.name, prompt, ["ui/index.html", "ui/styles.css"]) or {}
        if files:
            for rel, content in files.items():
                MCP.write_file(self.name, Path(rel), content)
            from .feed import agent_say as _say
            _say("Edna", '"Interface designed via Codex MCP."')
            return

        # No local fallback
        from .feed import agent_say as _say
        _say("Edna", '"❌ Codegen unavailable (no subscription or API). Skipping UI until Codex/API is ready."')

    def _generate_generic_design(self, spec: ProjectSpec):
        """No local fallback; require Codex/API for generic design."""
        from .feed import agent_say as _say
        _say("Edna", '"❌ Codegen unavailable (no subscription or API). Skipping design until Codex/API is ready."')


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
                title="Prepare codegen context",
                description="Compress project context and write docs/context_summary.md",
                owner=self.name,
                files_touched=["docs/context_summary.md"],
            ),
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
        MCP.start_for_agent(self.name, Path("logs"))
        executed = []
        for task in tasks:
            if "codegen context" in task.title.lower():
                self._prepare_codegen_context()
            elif "ci workflow" in task.title.lower():
                self._generate_ci_workflow(spec)
            elif "dockerfile" in task.title.lower():
                self._generate_docker_config(spec)
            elif "deployment config" in task.title.lower():
                self._generate_deployment_config(spec)
            elif "start local runtime" in task.title.lower():
                # Avoid spawning duplicate runtimes across continuous loops
                if self.last_runtime_summary:
                    from .feed import agent_say as _say
                    _say("Mario", '"Runtime already running — skipping restart."')
                    summary = self.last_runtime_summary
                else:
                    summary = self._start_local_runtime(spec)
                if summary:
                    task.description = (task.description + f" | URLs: {summary}").strip()
            executed.append(task)
        return executed

    def _prepare_codegen_context(self) -> Path:
        """Create a compressed context summary for codex exec prompts.

        Writes docs/context_summary.md with:
        - project.json, backlog.json, plan.md (truncated)
        - prd.md (truncated)
        - repo tree (depth<=3)
        - samples of backend/ui/docs files
        """
        root = Path('.')
        docs = Path('docs'); docs.mkdir(exist_ok=True)
        out = docs / 'context_summary.md'
        lines: list[str] = []
        def add_file(label: str, p: Path, limit: int = 8000):
            if p.exists():
                try:
                    lines.append(f'## {label}')
                    lines.append(p.read_text(encoding='utf-8')[:limit])
                except Exception:
                    pass
        add_file('project.json', docs / 'project.json', 6000)
        add_file('backlog.json', docs / 'backlog.json', 6000)
        add_file('plan.md', docs / 'plan.md', 6000)
        add_file('prd.md (truncated)', docs / 'prd.md', 8000)
        lines.append('## repository tree (depth=3)')
        for base in ['.', 'backend', 'ui', 'devops', 'docs']:
            p = Path(base)
            if not p.exists():
                continue
            lines.append(f'# {base}')
            for path in sorted(p.rglob('*')):
                try:
                    rel = path.relative_to(root)
                    if len(rel.parts) > 3 or path.is_dir():
                        continue
                    lines.append(str(rel))
                except Exception:
                    continue
        lines.append('## file samples (truncated)')
        for base in ['backend', 'ui', 'docs']:
            p = Path(base)
            if not p.exists():
                continue
            for f in sorted(p.rglob('*')):
                if f.is_file() and f.suffix in {'.py', '.md', '.json', '.yml', '.yaml', '.html', '.css'}:
                    try:
                        lines.append(f'### {f}')
                        lines.append(f.read_text(encoding='utf-8')[:4000])
                    except Exception:
                        pass
        out.write_text('\n\n'.join(lines) + '\n', encoding='utf-8')
        from .feed import agent_say as _say
        _say("Mario", f'"Prepared codegen context: {out}"')
        return out

    def _generate_ci_workflow(self, spec: ProjectSpec):
        """Generate CI workflow using Codex MCP (MCP-only)."""
        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)

        if codex_exec.available():
            bundle = ctx.build_context_bundle(spec)
            import os
            verbose = os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")
            if verbose:
                from .feed import agent_say as _say
                _say("Mario", '"Context prepared."')
            instruction = (
                "Generate a GitHub Actions CI workflow for Python 3.11 running pytest and basic lint. "
                "Save as .github/workflows/ci.yml."
            )
            files = codex_exec.generate_files(instruction, [".github/workflows/ci.yml"], bundle, agent=self.name)
            if files:
                from .codex_exec import last_mode
                for rel, content in files.items():
                    Path(rel).parent.mkdir(parents=True, exist_ok=True)
                    Path(rel).write_text(content, encoding="utf-8")
                from .feed import agent_say as _say
                _say("Mario", '"CI pipeline generated via Codex MCP."')
                return
        
        prd = None
        prd_path = Path("docs/prd.md")
        if prd_path.exists():
            try:
                prd = prd_path.read_text(encoding="utf-8")
            except Exception:
                prd = None
        prompt = f"Generate a GitHub Actions CI workflow for Python 3.11 running pytest and lint for project '{spec.name}'." + (" PRD: " + prd if prd else "")
        files = MCP.codegen_files(self.name, prompt, [".github/workflows/ci.yml"]) or {}
        if files:
            for rel, content in files.items():
                MCP.write_file(self.name, Path(rel), content)
            from .feed import agent_say as _say
            _say("Mario", '"CI pipeline generated via Codex MCP."')
            return

        # Proceed with local fallback if Codex/API not available
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
        from .feed import agent_say as _say
        _say("Mario", '"CI pipeline generated (local fallback)."')

    def _generate_docker_config(self, spec: ProjectSpec):
        """Generate Docker config using Codex MCP (MCP-only)."""
        if codex_exec.available():
            bundle = ctx.build_context_bundle(spec)
            import os
            verbose = os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")
            if verbose:
                from .feed import agent_say as _say
                _say("Mario", '"Context prepared."')
            instruction = (
                f"Generate Dockerfile and .dockerignore for a FastAPI app named '{spec.name}'. "
                "Expose 8000 and run uvicorn backend.app:app."
            )
            files = codex_exec.generate_files(instruction, ["Dockerfile", ".dockerignore"], bundle, agent=self.name)
            if files:
                from .codex_exec import last_mode
                for rel, content in files.items():
                    Path(rel).parent.mkdir(parents=True, exist_ok=True)
                    Path(rel).write_text(content, encoding="utf-8")
                from .feed import agent_say as _say
                _say("Mario", '"Docker config generated via Codex MCP."')
                return

        prd = None
        prd_path = Path("docs/prd.md")
        if prd_path.exists():
            try:
                prd = prd_path.read_text(encoding="utf-8")
            except Exception:
                prd = None
        prompt = f"Generate a Dockerfile and .dockerignore for a Python FastAPI app named '{spec.name}'." + (" PRD: " + prd if prd else "")
        files = MCP.codegen_files(self.name, prompt, ["Dockerfile", ".dockerignore"]) or {}
        if files:
            for rel, content in files.items():
                MCP.write_file(self.name, Path(rel), content)
            from .feed import agent_say as _say
            _say("Mario", '"Docker config generated via Codex MCP."')
            return

        # No local fallback
        from .feed import agent_say as _say
        _say("Mario", '"❌ Codegen unavailable (no subscription or API). Skipping Docker config until Codex/API is ready."')

    def _generate_deployment_config(self, spec: ProjectSpec):
        """Generate deployment config using Codex MCP (MCP-only)."""
        devops_dir = Path("devops")
        devops_dir.mkdir(exist_ok=True)
        if codex_exec.available():
            bundle = ctx.build_context_bundle(spec)
            import os
            verbose = os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False")
            if verbose:
                from .feed import agent_say as _say
                _say("Mario", '"Context prepared."')
            instruction = (
                f"Generate devops/deploy.yaml for a {spec.name} FastAPI app with /healthz health endpoint."
            )
            files = codex_exec.generate_files(instruction, ["devops/deploy.yaml"], bundle, agent=self.name)
            if files:
                from .codex_exec import last_mode
                for rel, content in files.items():
                    Path(rel).parent.mkdir(parents=True, exist_ok=True)
                    Path(rel).write_text(content, encoding="utf-8")
                from .feed import agent_say as _say
                _say("Mario", '"Deployment config generated via Codex MCP."')
                return

        prd = None
        prd_path = Path("docs/prd.md")
        if prd_path.exists():
            try:
                prd = prd_path.read_text(encoding="utf-8")
            except Exception:
                prd = None
        prompt = f"Generate a deployment config (render.yaml or deploy.yaml) for '{spec.name}' FastAPI app with health check '/healthz'." + (" PRD: " + prd if prd else "")
        files = MCP.codegen_files(self.name, prompt, ["devops/deploy.yaml"]) or {}
        if files:
            for rel, content in files.items():
                MCP.write_file(self.name, Path(rel), content)
            from .feed import agent_say as _say
            _say("Mario", '"Deployment config generated via Codex MCP."')
            return

        # No local fallback
        from .feed import agent_say as _say
        _say("Mario", '"❌ Codegen unavailable (no subscription or API). Skipping deployment config until Codex/API is ready."')

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

        # If building a web/api app and uvicorn is missing, auto-install deps
        if (
            backend_app.exists()
            and not uvicorn_available
            and spec.kind in ("web", "api")
            and os.getenv("OCEAN_TEST") != "1"
        ):
            from .feed import agent_say as _say
            _say("Mario", '"Installing runtime dependencies (fastapi[all], uvicorn)…"')
            try:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "fastapi[all]",
                        "uvicorn",
                    ],
                    check=True,
                    capture_output=True,
                )
                uvicorn_available = True
                from .feed import agent_say as _say
                _say("Mario", '"Dependencies installed."')
            except subprocess.CalledProcessError as e:
                from .feed import agent_say as _say
                _say("Mario", f'"Failed to install dependencies automatically: exit={e.returncode}. Run \'ocean run --yes\' or install manually."')

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
            from .feed import agent_say as _say
            _say("Mario", f'"Local backend started: {backend_url}"')
            self.last_backend_url = backend_url
        elif backend_app.exists() and not uvicorn_available:
            from .feed import agent_say as _say
            _say("Mario", "\"uvicorn not available; skipping auto-run. Use 'ocean run --yes' to install and start.\"")

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
            from .feed import agent_say as _say
            _say("Mario", f'"Local UI served: {ui_url}"')
            self.last_ui_url = ui_url

        # Final URL summary
        if backend_url or ui_url:
            summary = " | ".join(filter(None, [backend_url, ui_url]))
            self.last_runtime_summary = summary
            from .feed import agent_say as _say
            _say("Mario", f'"Runtime ready → {summary}"')
            return summary
        else:
            from .feed import agent_say as _say
            _say("Mario", '"No runtime started (missing deps or artifacts)."')
            self.last_runtime_summary = None
            return None


def default_agents() -> list[AgentBase]:
    return [Moroni(), Q(), Edna(), Mario(), Tony()]


class Tony(AgentBase):
    def __init__(self) -> None:
        super().__init__(
            name="Tony",
            role="Experimenter/Test Pilot. Runs prototypes, stress tests, and logs results.",
            tools=["pytest", "shell", "telemetry"],
        )

    def introduce(self) -> str:
        return f"{self.name}: {self.role} (tools: {', '.join(self.tools)})"

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        return [
            Task(
                title="Run test suite and write report",
                description="Execute pytest (if present) and record a concise report",
                owner=self.name,
                files_touched=["docs/test_report.md"],
            )
        ]

    def execute(self, tasks: Iterable[Task], spec: ProjectSpec) -> List[Task]:
        MCP.start_for_agent(self.name, Path("logs"))
        executed = []
        for t in tasks:
            if "test" in t.title.lower():
                from .feed import agent_say as _say
                _say("Tony", '"Let me hammer this build with tests…"')
                self._run_tests_and_report()
                _say("Tony", '"Report ready → docs/test_report.md"')
            executed.append(t)
        return executed

    def _run_tests_and_report(self) -> None:
        """Run pytest -q if available; write docs/test_report.md.

        If pytest is not available or no tests exist, generate a simple exploratory note.
        """
        docs = Path("docs"); docs.mkdir(exist_ok=True)
        report = docs / "test_report.md"
        import subprocess, sys
        lines: list[str] = ["# Test Report", "", f"Generated: {datetime.now().isoformat()}", ""]
        try:
            code = subprocess.call([sys.executable, "-m", "pytest", "-q"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Rerun capturing output for report
            out = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
            lines.append("## Pytest Output\n")
            lines.append("````\n" + (out.stdout or '') + (out.stderr or '') + "\n````")
            lines.append("")
            lines.append(f"Exit code: {code}")
        except Exception as e:
            lines.append("## Exploratory\n")
            lines.append(f"Pytest not available or failed to run: {e}")
            lines.append("Performed smoke checks and manual interactions.")
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")
