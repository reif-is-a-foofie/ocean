from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .actors import coverage_report, load_actors
from .product_loop import next_action


@dataclass
class OceanJob:
    id: str
    actor_id: str
    actor_name: str
    phase: str
    title: str
    objective: str
    context: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    handoff: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "phase": self.phase,
            "title": self.title,
            "objective": self.objective,
            "context": self.context,
            "instructions": self.instructions,
            "acceptance_criteria": self.acceptance_criteria,
            "verification": self.verification,
            "handoff": self.handoff,
            "cursor_prompt": self.cursor_prompt(),
        }

    def cursor_prompt(self) -> str:
        lines = [
            f"Ocean job: {self.title}",
            f"Owner persona: {self.actor_name} ({self.phase})",
            "",
            "Objective:",
            self.objective,
            "",
            "Context:",
            *[f"- {item}" for item in self.context],
            "",
            "Instructions:",
            *[f"- {item}" for item in self.instructions],
            "",
            "Acceptance criteria:",
            *[f"- {item}" for item in self.acceptance_criteria],
            "",
            "Verification:",
            *[f"- {item}" for item in self.verification],
            "",
            "Handoff:",
            self.handoff,
        ]
        return "\n".join(lines).strip()


def plan_jobs(
    project_root: str | Path,
    *,
    user_turn: str = "",
    test_results: str = "",
    candidate_tasks: list[str] | None = None,
    use_advisor: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    guidance = next_action(
        root,
        user_turn=user_turn,
        test_results=test_results,
        candidate_tasks=candidate_tasks or [],
        use_advisor=use_advisor,
    )
    actors = load_actors(root)
    jobs = _jobs_from_guidance(guidance.to_dict(), actors)
    result = {
        "project_root": str(root),
        "selected_task": guidance.to_dict().get("selected_task"),
        "advisor_recommendation": guidance.to_dict().get("advisor_recommendation"),
        "coverage": coverage_report(root),
        "jobs": [job.to_dict() for job in jobs],
        "crew_manifest": crew_manifest([job.to_dict() for job in jobs], actors),
    }
    save_job_plan(root, result)
    return result


def save_job_plan(root: Path, plan: dict[str, Any]) -> Path:
    path = root / ".ocean" / "jobs.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return path


def crew_manifest(jobs: list[dict[str, Any]], actors: list[dict[str, Any]]) -> dict[str, Any]:
    active_actors = [actor for actor in actors if actor.get("active", True)]
    return {
        "crew": [
            {
                "id": actor["id"],
                "name": actor["name"],
                "role": actor["role"],
                "goal": actor["mission"],
                "skills": actor.get("skills", []),
                "tools": actor.get("tools", []),
            }
            for actor in active_actors
        ],
        "process": "sequential_by_phase",
        "jobs": jobs,
    }


def _jobs_from_guidance(guidance: dict[str, Any], actors: list[dict[str, Any]]) -> list[OceanJob]:
    task = _task_from_guidance(guidance)
    active = {actor["id"]: actor for actor in actors if actor.get("active", True)}
    jobs: list[OceanJob] = []

    ordered_actor_ids = [
        "captain",
        "scrooge",
        "edna",
        "q",
        "mario",
    ]
    for actor_id in ordered_actor_ids:
        actor = active.get(actor_id)
        if not actor:
            continue
        factory = JOB_FACTORIES.get(actor_id) or _generic_job
        job = factory(actor, task, guidance)
        if job:
            jobs.append(job)
    return jobs


def _task_from_guidance(guidance: dict[str, Any]) -> dict[str, Any]:
    advisor_task = (guidance.get("advisor_recommendation") or {}).get("recommended_task")
    selected = guidance.get("selected_task")
    task = advisor_task or selected or {}
    title = str(task.get("title") or "Choose and ship the next smallest valuable improvement")
    rationale = str(task.get("rationale") or "Selected by Ocean as the current highest-value move.")
    return {"title": title, "rationale": rationale}


def _job_id(actor: dict[str, Any], title: str) -> str:
    return f"{actor['id']}-{_slug(title)[:42]}"


def _base_job(actor: dict[str, Any], title: str, objective: str) -> OceanJob:
    return OceanJob(
        id=_job_id(actor, title),
        actor_id=actor["id"],
        actor_name=actor["name"],
        phase=actor.get("phase", "implementation"),
        title=title,
        objective=objective,
    )


def _captain_job(actor: dict[str, Any], task: dict[str, Any], guidance: dict[str, Any]) -> OceanJob:
    job = _base_job(actor, "Confirm product value and scope", f"Validate that '{task['title']}' is still the smallest valuable next move.")
    job.context = [task["rationale"], "Use doctrine, feedback, test results, and current build context."]
    job.instructions = [
        "Name the target user and the value this task creates.",
        "Reject any expansion that does not improve near-term user value.",
        "Write the single Cursor job that should run next.",
    ]
    job.acceptance_criteria = ["The selected task has a clear user benefit and is small enough for one coding pass."]
    job.verification = ["Check TASKS.md and ROADMAP.md for conflicting priorities."]
    job.handoff = "Give Q the confirmed objective, file context, and scope limits."
    return job


def _scrooge_job(actor: dict[str, Any], task: dict[str, Any], guidance: dict[str, Any]) -> OceanJob:
    job = _base_job(actor, "Challenge impact and monetization", f"Explain what business or adoption benefit '{task['title']}' creates.")
    job.context = ["Ask: who benefits, who adopts, who might pay, and what capability this proves."]
    job.instructions = [
        "Identify the strongest adoption or revenue path this task supports.",
        "Call out if the task is impressive but economically weak.",
        "Suggest the smallest tweak that improves demo power, distribution, or monetization.",
    ]
    job.acceptance_criteria = ["The job has an explicit impact thesis, not just a feature rationale."]
    job.verification = ["Compare against POSITIONING.md and ROADMAP.md."]
    job.handoff = "Give Captain any monetization or adoption constraint."
    return job


def _design_job(actor: dict[str, Any], task: dict[str, Any], guidance: dict[str, Any]) -> OceanJob:
    job = _base_job(actor, "Design the user-facing flow", f"Shape the UX, copy, and visible states for '{task['title']}'.")
    job.context = ["Use plain assistant language and avoid developer jargon unless asked."]
    job.instructions = [
        "Define the first screen or interaction the user will see.",
        "Specify empty, loading, success, and failure states.",
        "Write concise interface copy for the setup or workflow.",
    ]
    job.acceptance_criteria = ["A target user can understand what is happening and why it matters."]
    job.verification = ["Check screenshots or browser UI before handoff."]
    job.handoff = "Give Q exact UI/copy requirements."
    return job


def _builder_job(actor: dict[str, Any], task: dict[str, Any], guidance: dict[str, Any]) -> OceanJob:
    job = _base_job(actor, task["title"], f"Implement the smallest complete version of '{task['title']}'.")
    job.context = [
        task["rationale"],
        "Follow the repo's existing patterns and avoid unrelated refactors.",
    ]
    job.instructions = [
        "Make the narrowest code/docs changes needed for the accepted objective.",
        "Keep product doctrine and tuned actor responsibilities intact.",
        "Return changed files and any known tradeoffs.",
    ]
    job.acceptance_criteria = [
        "The selected user-facing or workflow benefit exists end to end.",
        "The implementation is usable by Cursor/Codex as a discrete workflow step.",
    ]
    job.verification = ["Run focused tests or smoke checks and record results."]
    job.handoff = "Give Mario exact verification steps and expected outcomes."
    return job


def _ship_job(actor: dict[str, Any], task: dict[str, Any], guidance: dict[str, Any]) -> OceanJob:
    job = _base_job(actor, "Verify function and usefulness", f"Verify '{task['title']}' works and made the product more useful.")
    job.context = ["Passing tests are necessary but not enough; verify user value."]
    job.instructions = [
        "Run the smallest reliable functional test.",
        "Exercise the expected user path manually when UI or setup is involved.",
        "Write evidence: command, result, screenshot note, and remaining risk.",
    ]
    job.acceptance_criteria = ["There is concrete evidence that the workflow works."]
    job.verification = ["Update test notes or docs/test_report.md when appropriate."]
    job.handoff = "Report the result back into Ocean chat."
    return job


def _generic_job(actor: dict[str, Any], task: dict[str, Any], guidance: dict[str, Any]) -> OceanJob:
    job = _base_job(actor, f"{actor['name']} contribution", f"Contribute your specialty to '{task['title']}'.")
    job.context = [actor.get("mission", ""), task["rationale"]]
    job.instructions = ["Stay inside your role and produce concrete handoff notes."]
    job.acceptance_criteria = ["The role has added a useful constraint, artifact, or verification step."]
    job.verification = ["State what you checked."]
    job.handoff = "Hand off to Captain."
    return job


JOB_FACTORIES = {
    "captain": _captain_job,
    "scrooge": _scrooge_job,
    "edna": _design_job,
    "q": _builder_job,
    "builder": _builder_job,
    "mario": _ship_job,
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "job"
