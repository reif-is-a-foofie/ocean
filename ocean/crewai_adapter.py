from __future__ import annotations

import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from . import codex_exec
from . import context as ctx


def _build_context_bundle() -> Path:
    # Best-effort local context bundle; online search handled by Codex --search
    try:
        return ctx.build_context_bundle(None)
    except Exception:
        return Path("docs/context_summary.md") if (Path("docs/context_summary.md").exists()) else Path(".")


def _codegen_files(agent_name: str, prompt: str, suggestions: Optional[List[str]] = None) -> Dict[str, str]:
    bundle = _build_context_bundle()
    files = codex_exec.generate_files(prompt, suggestions or [], bundle, agent=agent_name)
    if not files:
        raise RuntimeError("Codex did not return files (generate_files)")
    return files  # type: ignore[return-value]


def _write_file(agent_name: str, path: str, content: str) -> Dict[str, Any]:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"path": path, "bytes": len(content)}


def _shell_run(agent_name: str, command: str) -> Dict[str, Any]:
    # Minimal passthrough; prefer to avoid shell in agent tools unless explicitly desired
    import subprocess
    proc = subprocess.run(command, shell=True, capture_output=True, text=True)
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


try:
    from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process
    try:
        from crewai_tools import tool as crew_tool
    except Exception:  # crewai-tools not installed
        crew_tool = None
except Exception:  # pragma: no cover
    CrewAgent = None  # type: ignore
    CrewTask = None  # type: ignore
    Crew = None  # type: ignore
    Process = None  # type: ignore
    crew_tool = None  # type: ignore


def _make_tools():
    if crew_tool is not None:
        @crew_tool("codegen_files")
        def codegen_files_tool(prompt: str, agent: str, suggestions_json: str = "[]") -> str:
            files = _codegen_files(agent, prompt, json.loads(suggestions_json))
            return json.dumps(files)

        @crew_tool("write_file")
        def write_file_tool(path: str, content: str, agent: str) -> str:
            result = _write_file(agent, path, content)
            return json.dumps(result)

        @crew_tool("shell_run")
        def shell_run_tool(command: str, agent: str) -> str:
            result = _shell_run(agent, command)
            return json.dumps(result)

        return [codegen_files_tool, write_file_tool, shell_run_tool]

    # Otherwise return raw callables; many CrewAI builds accept these as tools
    return [
        lambda prompt, agent, suggestions_json="[]": json.dumps(
            _codegen_files(agent, prompt, json.loads(suggestions_json))
        ),
        lambda path, content, agent: json.dumps(_write_file(agent, path, content)),
        lambda command, agent: json.dumps(_shell_run(agent, command)),
    ]


@dataclass
class Persona:
    name: str
    role: str
    goal: str
    backstory: str


class CrewRunner:
    def __init__(self, emit: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        if CrewAgent is None:
            raise RuntimeError(
                "CrewAI not installed. Install crewai and crewai-tools or unset OCEAN_USE_CREWAI."
            )
        self.emit = emit or (lambda *_args, **_kw: None)
        self.tools = _make_tools()

    def _agent(self, p: Persona) -> Any:
        return CrewAgent(
            name=p.name,
            role=p.role,
            goal=p.goal,
            backstory=p.backstory,
            tools=self.tools,
            allow_delegation=True,
            verbose=True,
        )

    def build_team(self) -> Dict[str, Any]:
        return {
            "Moroni": self._agent(
                Persona(
                    name="Moroni",
                    role="Architect & Decomposer",
                    goal="Interpret PRD, emit atomic activities, and author architecture/docs",
                    backstory="Unflappable architect; writes acceptance criteria like scripture.",
                )
            ),
            "Q": self._agent(
                Persona(
                    name="Q",
                    role="Backend & Tools",
                    goal="Implement backend APIs, models, tests, and dev tooling",
                    backstory="Pragmatic engineer; ships clean, testable code.",
                )
            ),
            "Edna": self._agent(
                Persona(
                    name="Edna",
                    role="Designer & Frontend",
                    goal="Deliver responsive UI and design system",
                    backstory="Pixel-perfect designer with strong UX instincts.",
                )
            ),
            "Mario": self._agent(
                Persona(
                    name="Mario",
                    role="DevOps & Delivery",
                    goal="Dockerize, compose services, setup CI and deploy",
                    backstory="DevOps ace; values reliability and simplicity.",
                )
            ),
        }

    def run_project(self, prd_text: str) -> Any:
        team = self.build_team()

        # Base tasks; Moroni can later emit more via state.json
        tasks = [
            CrewTask(
                description="Clarify PRD; produce docs/architecture.md and docs/api.md with acceptance criteria.",
                expected_output="Files written and a JSON task list for backlog",
                agent=team["Moroni"],
            ),
            CrewTask(
                description="Scaffold backend service with health check and tests.",
                expected_output="backend/app.py, tests; passing CI",
                agent=team["Q"],
            ),
            CrewTask(
                description="Scaffold UI shell and base layout.",
                expected_output="ui/index.html, ui/styles.css",
                agent=team["Edna"],
            ),
            CrewTask(
                description="Provision Dockerfile and docker-compose for backend+ui; add healthchecks.",
                expected_output="Dockerfile, docker-compose.yml",
                agent=team["Mario"],
            ),
        ]

        # For now, sequential; can move to hierarchical later
        crew = Crew(agents=list(team.values()), tasks=tasks, process=Process.sequential)
        result = crew.kickoff(inputs={"prd": prd_text})
        return result
