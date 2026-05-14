"""Per-persona nomination logic.

Each persona inspects the current project state and returns a Nomination:
- task_title / task_description: what they want built
- bid: how many coins they're willing to spend (bounded by their wallet)
- rationale: why they're bidding this amount

Bid strategy:
  bid = urgency [0,1] * wallet.balance * MAX_BID_FRACTION
  minimum bid = 1.0 (so a persona with coins always participates)

A persona that saves for multiple sessions can place a large bid and
dominate the session budget, guaranteeing their task goes first.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .economy import Nomination, Wallet

_MIN_BID = 1.0
_MAX_BID_FRACTION = 0.75   # never bid more than 75% of balance in one shot


@dataclass
class ProjectState:
    has_prd: bool
    prd_snippet: str
    has_project_json: bool
    workspace_files: list[str]
    has_tests: bool
    has_html: bool
    has_ci: bool
    last_task_title: str


def load_project_state(cwd: Path) -> ProjectState:
    workspace = cwd / "workspace"
    ws_files: list[str] = []
    if workspace.exists():
        ws_files = [f.name for f in workspace.rglob("*") if f.is_file()]

    prd_path = cwd / "docs" / "prd.md"
    has_prd = prd_path.exists() and prd_path.stat().st_size > 10
    prd_snippet = ""
    if has_prd:
        try:
            prd_snippet = prd_path.read_text(encoding="utf-8")[:300]
        except Exception:
            pass

    has_project_json = (cwd / "docs" / "project.json").exists()
    has_tests = any("test" in f.lower() for f in ws_files)
    has_html = any(f.endswith(".html") for f in ws_files)
    has_ci = (cwd / ".github" / "workflows").exists() and any(
        (cwd / ".github" / "workflows").glob("*.yml")
    )

    last_task = ""
    economy_path = cwd / "docs" / "economy.json"
    if economy_path.exists():
        try:
            import json
            data = json.loads(economy_path.read_text())
            last_task = data.get("last_task", "")
        except Exception:
            pass

    return ProjectState(
        has_prd=has_prd,
        prd_snippet=prd_snippet,
        has_project_json=has_project_json,
        workspace_files=ws_files,
        has_tests=has_tests,
        has_html=has_html,
        has_ci=has_ci,
        last_task_title=last_task,
    )


def _bid(urgency: float, wallet: Wallet) -> float:
    raw = urgency * wallet.balance * _MAX_BID_FRACTION
    return round(max(_MIN_BID, min(raw, wallet.balance * _MAX_BID_FRACTION)), 2)


# ── per-persona nomination functions ─────────────────────────────────────────

def _mario(state: ProjectState, wallet: Wallet) -> Nomination:
    has_output = bool(state.workspace_files)
    if has_output and not state.has_ci:
        urgency, title, desc = (
            0.85,
            "Wire CI/CD and deployment config",
            f"Workspace has built files but no CI pipeline. "
            f"Add GitHub Actions workflow and a deploy stub. "
            f"Files: {', '.join(state.workspace_files[:5])}",
        )
        rationale = "Built but not shipped — pipes need fixing!"
    elif has_output:
        urgency, title, desc = (
            0.55,
            "Harden the deployment and add health checks",
            "Review deploy config, wire rollback, add a /health endpoint if applicable.",
        )
        rationale = "Keep the pipeline clean, let's-a go!"
    else:
        urgency, title, desc = (
            0.15,
            "Scaffold Makefile and project structure",
            "No output yet. Create a minimal Makefile, .env.example, and README stub.",
        )
        rationale = "Lay the pipes before the water flows."
    return Nomination("Mario", title, desc, _bid(urgency, wallet), rationale)


def _q(state: ProjectState, wallet: Wallet) -> Nomination:
    has_output = bool(state.workspace_files)
    if has_output and not state.has_tests:
        urgency, title, desc = (
            0.9,
            "Write tests for workspace output",
            f"Files built with no test coverage. Write pytest tests for: "
            f"{', '.join(state.workspace_files[:5])}. Cover happy path and edge cases.",
        )
        rationale = "Red → Green → Refactor. Guardrails first."
    elif not state.has_prd:
        urgency, title, desc = (
            0.6,
            "Define API contracts and data models",
            "No PRD. Draft core API contracts, data models, and acceptance criteria.",
        )
        rationale = "Pay attention — specs before code."
    else:
        urgency, title, desc = (
            0.3,
            "Audit and strengthen existing tests",
            "Review test coverage, add missing assertions, tighten contracts.",
        )
        rationale = "There are only about six people who can set up guardrails like this."
    return Nomination("Q", title, desc, _bid(urgency, wallet), rationale)


def _tony(state: ProjectState, wallet: Wallet) -> Nomination:
    has_output = bool(state.workspace_files)
    if has_output:
        urgency, title, desc = (
            0.75,
            "Stress-test and hunt edge cases",
            f"Run exploratory tests against: {', '.join(state.workspace_files[:5])}. "
            f"Find failure modes and boundary conditions. Write repro steps for any bugs.",
        )
        rationale = "Sometimes you gotta run before you can walk."
    elif state.has_tests:
        urgency, title, desc = (
            0.5,
            "Triage and fix flaky tests",
            "Run the test suite, identify flaky or slow tests, fix them.",
        )
        rationale = "I built this in a cave — it better hold up."
    else:
        urgency, title, desc = (
            0.2,
            "Add logging and error telemetry",
            "Add structured logging and error capture so failures surface clearly.",
        )
        rationale = "Can't fix what you can't see."
    return Nomination("Tony", title, desc, _bid(urgency, wallet), rationale)


def _moroni(state: ProjectState, wallet: Wallet) -> Nomination:
    if not state.has_prd and not state.has_project_json:
        urgency, title, desc = (
            0.95,
            "Define vision, PRD, and phased roadmap",
            "No product definition exists. Define: project name, kind, goals, constraints, "
            "vision, and a 3-phase roadmap with acceptance criteria per phase.",
        )
        rationale = "In memory of our mission — plan before we march."
    elif not state.has_project_json:
        urgency, title, desc = (
            0.7,
            "Finalize project spec from PRD",
            f"PRD exists but project.json is missing. Synthesize it. PRD: {state.prd_snippet[:200]}",
        )
        rationale = "Acceptance criteria, standards, banners — Phase 1."
    elif len(state.workspace_files) > 3:
        urgency, title, desc = (
            0.4,
            "Review progress and re-prioritize roadmap",
            f"{len(state.workspace_files)} files built. Assess what's done vs planned, "
            f"update phase status, flag next milestone.",
        )
        rationale = "He did prepare the minds of the people to be faithful."
    else:
        urgency, title, desc = (
            0.2,
            "Clarify next phase acceptance criteria",
            "Define clear done-criteria for the current phase.",
        )
        rationale = "A man of perfect understanding prepares the path."
    return Nomination("Moroni", title, desc, _bid(urgency, wallet), rationale)


def _edna(state: ProjectState, wallet: Wallet) -> Nomination:
    if state.has_html:
        html_files = [f for f in state.workspace_files if f.endswith(".html")]
        urgency, title, desc = (
            0.85,
            "Accessibility audit and UI polish",
            f"HTML files in workspace: {html_files}. Audit contrast, focus order, "
            f"semantic structure, and responsive breakpoints. Fix WCAG AA failures.",
        )
        rationale = "No capes — and no inaccessible interfaces, darling."
    elif state.has_prd and (
        "UI" in state.prd_snippet or "interface" in state.prd_snippet.lower()
    ):
        urgency, title, desc = (
            0.7,
            "Design UI component structure",
            "PRD mentions a UI. Design component hierarchy, spacing scale, "
            "type rhythm, and token system. Deliver HTML/CSS scaffold.",
        )
        rationale = "I never look back, darling — the interface comes first."
    elif state.workspace_files:
        urgency, title, desc = (
            0.3,
            "Visual consistency pass and design tokens",
            "Review workspace files for visual consistency. Apply design tokens, fix spacing.",
        )
        rationale = "Perfection is my standard."
    else:
        urgency, title, desc = (
            0.15,
            "Draft UX flow and wireframe",
            "No UI exists yet. Draft the core user flow and a minimal wireframe in HTML.",
        )
        rationale = "Luck favors the prepared."
    return Nomination("Edna", title, desc, _bid(urgency, wallet), rationale)


_NOMINATORS = {
    "Mario": _mario,
    "Q": _q,
    "Tony": _tony,
    "Moroni": _moroni,
    "Edna": _edna,
}


class PersonaScheduler:
    def nominate_all(
        self, state: ProjectState, wallets: dict[str, Wallet]
    ) -> list[Nomination]:
        nominations: list[Nomination] = []
        for persona, fn in _NOMINATORS.items():
            wallet = wallets.get(persona)
            if wallet is None or wallet.balance < _MIN_BID:
                continue
            try:
                nominations.append(fn(state, wallet))
            except Exception:
                pass
        return nominations
