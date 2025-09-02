from dataclasses import dataclass, field
from typing import Iterable, List

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

    # High-level hooks to speed Cursor implementation
    def plan(self, spec: ProjectSpec) -> list[str]:  # short bullet plan
        return []

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        return []

    def execute(self, tasks: Iterable[Task]) -> List[Task]:
        # Default: no-op execution; Cursor can implement details per agent
        return list(tasks)


class Moroni(AgentBase):
    def __init__(self) -> None:
        super().__init__(
            name="Moroni",
            role="Architect/Brain. Clarifies vision, orchestrates the team.",
            tools=["planning"],
        )

    def plan(self, spec: ProjectSpec) -> list[str]:
        return [
            "Clarify requirements and constraints",
            "Generate initial repo scaffolds",
            "Coordinate Q (backend), Edna (UI), Mario (DevOps)",
        ]


class Q(AgentBase):
    def __init__(self) -> None:
        super().__init__(
            name="Q",
            role="Backend/tools engineer. Builds services, data models, integrations.",
            tools=["FastAPI", "pytest"],
        )

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        return [
            Task(
                title="Create health endpoint",
                description="Implement /healthz in FastAPI and a smoke test",
                owner=self.name,
                files_touched=["backend/app.py", "backend/tests/test_healthz.py"],
            )
        ]


class Edna(AgentBase):
    def __init__(self) -> None:
        tool_list = ["Design methodology", "HTML/CSS"]
        if V0Cli.is_available():
            tool_list.append("V0 CLI")
        super().__init__(
            name="Edna",
            role="Designer/UI/UX. Produces mockups, CSS, flows.",
            tools=tool_list,
        )

    def plan(self, spec: ProjectSpec) -> list[str]:
        # Provide a compact design methodology outline to guide Cursor
        return [step.split(":", 1)[0] for step in DESIGN_METHOD[:5]]

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        return [
            Task(
                title="Create minimal UI placeholder",
                description="Generate ui/index.html with skeleton styles",
                owner=self.name,
                files_touched=["ui/index.html"],
            )
        ]


class Mario(AgentBase):
    def __init__(self) -> None:
        super().__init__(
            name="Mario",
            role="DevOps. Provision infra, CI/CD, deploys final product.",
            tools=["GitHub Actions", "Docker", "Render (plan)"],
        )

    def propose_tasks(self, spec: ProjectSpec) -> list[Task]:
        return [
            Task(
                title="Add CI workflow",
                description="Run pytest on push via GitHub Actions",
                owner=self.name,
                files_touched=[".github/workflows/ci.yml"],
            ),
            Task(
                title="Create Dockerfile",
                description="Containerize backend with uvicorn",
                owner=self.name,
                files_touched=["Dockerfile", ".dockerignore"],
            ),
            Task(
                title="Render deploy plan",
                description="Add devops/render.yaml and a dry-run plan",
                owner=self.name,
                files_touched=["devops/render.yaml"],
            ),
        ]

    def execute(self, tasks: Iterable[Task]) -> List[Task]:
        # Provide a dry-run deploy plan reference to speed Cursor
        _ = RenderDeployPlan()
        return super().execute(tasks)


def default_agents() -> list[AgentBase]:
    return [Moroni(), Q(), Edna(), Mario()]
