from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .mcp import MCP


def _require_mcp_only() -> None:
    if os.getenv("OCEAN_MCP_ONLY", "1") not in ("1", "true", "True"):
        raise RuntimeError("CrewAI requires MCP-only mode. Set OCEAN_MCP_ONLY=1.")


def _codegen_files(agent_name: str, prompt: str, suggestions: Optional[List[str]] = None) -> Dict[str, str]:
    _require_mcp_only()
    files = MCP.codegen_files(agent_name, prompt, suggestions or [])
    if files is None:
        raise RuntimeError("Codex MCP did not return files (codegen_files)")
    return files


def _write_file(agent_name: str, path: str, content: str) -> Dict[str, Any]:
    _require_mcp_only()
    from pathlib import Path
    MCP.write_file(agent_name, Path(path), content)
    return {"path": path, "bytes": len(content)}


def _shell_run(agent_name: str, command: str) -> Dict[str, Any]:
    _require_mcp_only()
    res = MCP.shell_run(agent_name, command)
    if res is None:
        raise RuntimeError("Codex MCP did not execute shell command")
    return res


try:
    from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process
    try:
        from crewai_tools import tool as crew_tool
    except Exception:  # crewai-tools not installed
        crew_tool = None
except Exception as e:  # pragma: no cover
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
        # Ensure MCP instance exists for the agent (uses same names as Ocean agents)
        MCP.start_for_agent(p.name, Path("logs"))
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

