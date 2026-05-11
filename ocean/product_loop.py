from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .advisor import AdvisorResult, ask_pm_advisor, build_pm_prompt
from .actors import load_actors


DOCTRINE_FILES = [
    "VISION.md",
    "AUDIENCE.md",
    "PRODUCT_PRINCIPLES.md",
    "UX_RULES.md",
    "POSITIONING.md",
    "ROADMAP.md",
    "TASKS.md",
    "FEEDBACK.md",
    "DECISIONS.md",
]


DEFAULT_DOCTRINE: dict[str, str] = {
    "VISION.md": """# Vision

Ocean is an external product intelligence layer for agentic coding tools.

It helps a coding agent decide what to do next by asking whether the work made the product more useful to the intended user, not only whether the code passed.
""",
    "AUDIENCE.md": """# Audience

Primary users are builders who use tools like Cursor, Codex, or other coding agents and want product direction outside the application codebase.

They need fast setup, trustworthy guidance, and a path to one useful automation quickly.
""",
    "PRODUCT_PRINCIPLES.md": """# Product Principles

- Ask: "What is the smallest next change that makes this more valuable to the target user?"
- Protect user value over feature volume.
- Prefer plain assistant language over developer jargon unless the user asks for technical detail.
- Keep orchestration outside the target codebase whenever possible.
""",
    "UX_RULES.md": """# UX Rules

- Every setup step should explain what is happening and why it matters.
- Prefer visible progress, concrete next steps, and plain language.
""",
    "POSITIONING.md": """# Positioning

Ocean is a companion product manager for coding agents.

It turns feedback, doctrine, tasks, and test results into the next highest-value instruction.
""",
    "ROADMAP.md": """# Roadmap

- External MCP server usable from Cursor and Codex.
- Feedback scribe that turns reactions into durable doctrine.
- Product manager agent that ranks the next smallest valuable change.
- Captain loop that assigns implementation work based on product value.
""",
    "TASKS.md": """# Tasks

- [ ] Configure Cursor or Codex to call Ocean on each work turn.
- [ ] Run one end-to-end product loop: build, test, capture feedback, reprioritize.
""",
    "FEEDBACK.md": """# Feedback

Feedback Scribe entries are appended here.
""",
    "DECISIONS.md": """# Decisions

- Ocean should guide target codebases from the outside instead of becoming the codebase.
""",
}


@dataclass(frozen=True)
class ScoredTask:
    title: str
    source: str
    user_value: int
    setup_friction_reduced: int
    trust_increased: int
    demo_power: int
    technical_dependency: int
    risk: int
    total: int
    rationale: str


@dataclass
class TurnGuidance:
    project_root: Path
    selected_task: ScoredTask | None
    scored_tasks: list[ScoredTask] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    doctrine_summary: dict[str, str] = field(default_factory=dict)
    missing_doctrine: list[str] = field(default_factory=list)
    build_context: dict[str, Any] = field(default_factory=dict)
    advisor_prompt: str = ""
    advisor: AdvisorResult | None = None
    advisor_recommendation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "selected_task": self.selected_task.__dict__ if self.selected_task else None,
            "scored_tasks": [task.__dict__ for task in self.scored_tasks],
            "instructions": self.instructions,
            "doctrine_summary": self.doctrine_summary,
            "missing_doctrine": self.missing_doctrine,
            "build_context": self.build_context,
            "advisor_prompt": self.advisor_prompt,
            "advisor": self.advisor.__dict__ if self.advisor else None,
            "advisor_recommendation": self.advisor_recommendation,
        }


def resolve_project_root(project_root: str | Path | None = None) -> Path:
    root = Path(project_root or ".").expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"project_root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"project_root is not a directory: {root}")
    return root


def bootstrap_doctrine(
    project_root: str | Path | None = None,
    *,
    vision: str | None = None,
    audience: str | None = None,
    positioning: str | None = None,
) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    created: list[str] = []
    preserved: list[str] = []
    overrides = {
        "VISION.md": _with_heading("Vision", vision),
        "AUDIENCE.md": _with_heading("Audience", audience),
        "POSITIONING.md": _with_heading("Positioning", positioning),
    }
    for name in DOCTRINE_FILES:
        path = root / name
        if path.exists():
            preserved.append(name)
            continue
        content = overrides.get(name) or DEFAULT_DOCTRINE[name]
        path.write_text(_ensure_trailing_newline(content), encoding="utf-8")
        created.append(name)
    return {"project_root": str(root), "created": created, "preserved": preserved}


def record_feedback(
    project_root: str | Path | None,
    feedback: str,
    *,
    source: str = "Reif",
    test_context: str | None = None,
    update_files: bool = True,
) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    feedback = feedback.strip()
    if not feedback:
        raise ValueError("feedback is required")
    bootstrap_doctrine(root)
    categories = classify_feedback(feedback)
    timestamp = datetime.now().isoformat(timespec="seconds")

    entry = [
        f"## {timestamp} - {source}",
        "",
        f"Categories: {', '.join(categories) if categories else 'general'}",
    ]
    if test_context:
        entry.extend(["", f"Context: {test_context.strip()}"])
    entry.extend(["", feedback, ""])
    _append_section(root / "FEEDBACK.md", "\n".join(entry))

    updates: dict[str, list[str]] = {}
    if update_files:
        updates = _apply_feedback_doctrine(root, feedback, categories)
    return {
        "project_root": str(root),
        "categories": categories,
        "updated_files": updates,
    }


def next_action(
    project_root: str | Path | None = None,
    *,
    user_turn: str = "",
    test_results: str = "",
    candidate_tasks: list[str] | None = None,
    max_tasks: int = 5,
    use_advisor: bool = True,
) -> TurnGuidance:
    root = resolve_project_root(project_root)
    bootstrap_doctrine(root)
    summaries = read_doctrine_summary(root)
    build_context = collect_build_context(root)
    missing = [name for name in DOCTRINE_FILES if not (root / name).exists()]
    candidates = _collect_candidates(root, user_turn, candidate_tasks or [])
    scored = sorted(
        (_score_task(task, source, user_turn=user_turn, test_results=test_results) for task, source in candidates),
        key=lambda task: task.total,
        reverse=True,
    )
    selected = scored[0] if scored else None
    instructions = _build_instructions(selected, root, summaries, user_turn, test_results)
    advisor_payload = {
        "project_root": str(root),
        "user_turn": user_turn,
        "test_results": test_results,
        "doctrine_summary": summaries,
        "build_context": build_context,
        "local_selected_task": selected.__dict__ if selected else None,
        "local_scored_tasks": [task.__dict__ for task in scored[:max_tasks]],
        "note": "Ocean is model-agnostic. Use this payload with the host AI brain or configured advisor command.",
    }
    advisor_prompt = build_pm_prompt(advisor_payload)
    advisor = ask_pm_advisor(advisor_payload, cwd=root) if use_advisor else None
    advisor_recommendation = normalize_advisor_recommendation(advisor.data if advisor else None)
    if advisor:
        if advisor_recommendation:
            instructions = _merge_advisor_instructions(instructions, advisor_recommendation, advisor.source)
        else:
            instructions.insert(0, f"External PM advisor ({advisor.source}) says: {advisor.text}")
    return TurnGuidance(
        project_root=root,
        selected_task=selected,
        scored_tasks=scored[:max_tasks],
        instructions=instructions,
        doctrine_summary=summaries,
        missing_doctrine=missing,
        build_context=build_context,
        advisor_prompt=advisor_prompt,
        advisor=advisor,
        advisor_recommendation=advisor_recommendation,
    )


def turn(
    project_root: str | Path | None = None,
    *,
    user_turn: str = "",
    feedback: str = "",
    test_results: str = "",
    candidate_tasks: list[str] | None = None,
    use_advisor: bool = True,
) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    feedback_result = None
    if feedback.strip():
        feedback_result = record_feedback(root, feedback, test_context=test_results or None)
    guidance = next_action(
        root,
        user_turn=user_turn,
        test_results=test_results,
        candidate_tasks=candidate_tasks,
        use_advisor=use_advisor,
    )
    result = guidance.to_dict()
    result["feedback_result"] = feedback_result
    result["mcp_instruction"] = format_guidance_for_agent(guidance)
    return result


def format_guidance_for_agent(guidance: TurnGuidance) -> str:
    selected = guidance.selected_task
    lines = [
        "Ocean product guidance",
        "",
        'Governing question: "What is the smallest next change that makes this more valuable to the target user?"',
        "",
    ]
    if selected:
        lines.extend(
            [
                f"Next task: {selected.title}",
                f"Why: {selected.rationale}",
                (
                    "Score: "
                    f"user_value={selected.user_value}, "
                    f"setup_friction_reduced={selected.setup_friction_reduced}, "
                    f"trust_increased={selected.trust_increased}, "
                    f"demo_power={selected.demo_power}, "
                    f"technical_dependency={selected.technical_dependency}, "
                    f"risk={selected.risk}, total={selected.total}"
                ),
                "",
            ]
        )
    lines.extend(guidance.instructions)
    return "\n".join(lines).strip()


def read_doctrine_summary(project_root: str | Path | None = None) -> dict[str, str]:
    root = resolve_project_root(project_root)
    summary: dict[str, str] = {}
    for name in DOCTRINE_FILES:
        path = root / name
        if path.exists():
            summary[name] = _summarize_text(path.read_text(encoding="utf-8", errors="ignore"))
    return summary


def collect_build_context(project_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_project_root(project_root)
    context: dict[str, Any] = {
        "root": str(root),
        "git": _git_context(root),
        "detected_stack": _detect_stack(root),
        "actors": load_actors(root),
        "important_files": _read_important_files(root),
        "file_tree": _file_tree(root),
    }
    return context


def normalize_advisor_recommendation(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    recommended = data.get("recommended_task")
    if not isinstance(recommended, dict):
        title = data.get("title") or data.get("task")
        if isinstance(title, str):
            recommended = {"title": title, "rationale": data.get("rationale", "")}
        else:
            return None
    title = str(recommended.get("title") or "").strip()
    if not title:
        return None
    scores = recommended.get("scores")
    if not isinstance(scores, dict):
        scores = {}
    return {
        "recommended_task": {
            "title": title,
            "rationale": str(recommended.get("rationale") or "").strip(),
            "scores": {
                "user_value": _score_value(scores.get("user_value")),
                "setup_friction_reduced": _score_value(scores.get("setup_friction_reduced")),
                "trust_increased": _score_value(scores.get("trust_increased")),
                "demo_power": _score_value(scores.get("demo_power")),
                "technical_dependency": _score_value(scores.get("technical_dependency")),
                "risk": _score_value(scores.get("risk")),
            },
        },
        "feature_set": _string_list(data.get("feature_set")),
        "agent_instructions": _string_list(data.get("agent_instructions")),
        "doctrine_implications": _string_list(data.get("doctrine_implications")),
        "questions": _string_list(data.get("questions")),
    }


def classify_feedback(feedback: str) -> list[str]:
    text = feedback.lower()
    categories: list[str] = []
    checks = [
        ("language_tone", ["too technical", "jargon", "terminal", "plain", "friendly", "explain"]),
        ("onboarding", ["onboarding", "first run", "setup", "install", "localhost", "connect cursor"]),
        ("setup_friction", ["friction", "confusing", "hard to", "stuck", "five minutes", "5 minutes"]),
        ("trust", ["trust", "confidence", "verify", "proof", "tested", "working"]),
        ("demo_power", ["demo", "show", "wow", "useful automation", "example"]),
        ("reliability", ["broken", "failed", "error", "bug", "crash", "flaky"]),
    ]
    for category, needles in checks:
        if any(needle in text for needle in needles):
            categories.append(category)
    return categories or ["general"]


def _apply_feedback_doctrine(root: Path, feedback: str, categories: list[str]) -> dict[str, list[str]]:
    updates: dict[str, list[str]] = {}

    def add(name: str, line: str) -> None:
        path = root / name
        if _append_unique_bullet(path, line):
            updates.setdefault(name, []).append(line)

    if "language_tone" in categories:
        add("PRODUCT_PRINCIPLES.md", "Use plain assistant language. Avoid developer jargon unless the user asks for it.")
        add("UX_RULES.md", "Every setup step should explain what is happening and why it matters.")
        add("TASKS.md", "Add friendly setup narration to onboarding flow.")
    if "onboarding" in categories or "setup_friction" in categories:
        add("PRODUCT_PRINCIPLES.md", "The first-run path should get a capable user to one useful automation quickly.")
        add("TASKS.md", "Create a five-minute first-run path for connecting Ocean to Cursor and completing one useful automation.")
    if "trust" in categories or "reliability" in categories:
        add("PRODUCT_PRINCIPLES.md", "Earn trust with visible verification, clear failure states, and reproducible test evidence.")
        add("TASKS.md", "Show verification evidence in the next-turn guidance returned to the coding agent.")
    if "demo_power" in categories:
        add("ROADMAP.md", "Prioritize a demo that proves Ocean can guide an external coding agent through one complete improvement loop.")
        add("TASKS.md", "Build a short external-agent demo script: feedback, doctrine update, PM reprioritization, next instruction.")

    decision = f"Captured feedback: {feedback[:180]}"
    add("DECISIONS.md", decision)
    return updates


def _collect_candidates(root: Path, user_turn: str, candidate_tasks: list[str]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for task in candidate_tasks:
        if task.strip():
            items.append((task.strip(), "candidate_tasks"))
    tasks_path = root / "TASKS.md"
    if tasks_path.exists():
        for line in tasks_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.match(r"\s*-\s+\[[ xX]?\]\s+(.*)", line)
            if match:
                items.append((match.group(1).strip(), "TASKS.md"))
    inferred = _infer_task_from_turn(user_turn)
    if inferred:
        items.insert(0, (inferred, "user_turn"))
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for title, source in items:
        key = re.sub(r"\s+", " ", title.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            unique.append((title, source))
    return unique


def _infer_task_from_turn(user_turn: str) -> str | None:
    text = user_turn.strip()
    if not text:
        return None
    lower = text.lower()
    if "mcp" in lower and ("cursor" in lower or "outside" in lower):
        return "Ship an external Ocean MCP server that Cursor can call each turn for product guidance."
    if "feedback" in lower and "product manager" in lower:
        return "Add Feedback Scribe and Product Manager roles to the agentic product loop."
    return text[:180]


def _score_task(title: str, source: str, *, user_turn: str, test_results: str) -> ScoredTask:
    text = " ".join([title, source, user_turn, test_results]).lower()

    def has(*needles: str) -> bool:
        return any(needle in text for needle in needles)

    user_value = 3 + int(has("user", "audience", "valuable", "useful", "cursor", "first-run", "onboarding"))
    setup = 2 + int(has("setup", "install", "configure", "cursor", "mcp", "localhost", "first-run", "five-minute"))
    trust = 2 + int(has("test", "verify", "evidence", "trust", "reproducible", "working"))
    demo = 2 + int(has("demo", "cursor", "mcp", "automation", "first-run"))
    dependency = 2 + int(has("external", "mcp", "server", "protocol")) - int(has("refactor", "provider", "model"))
    risk = 2 + int(has("auth", "payment", "database", "destructive", "migration")) + int(len(title) > 140)

    user_value = _clamp(user_value)
    setup = _clamp(setup)
    trust = _clamp(trust)
    demo = _clamp(demo)
    dependency = _clamp(dependency)
    risk = _clamp(risk)
    total = user_value * 4 + setup * 3 + trust * 3 + demo * 2 + dependency - risk * 2
    rationale = _rationale(title, user_value, setup, trust, demo, dependency, risk)
    return ScoredTask(
        title=title,
        source=source,
        user_value=user_value,
        setup_friction_reduced=setup,
        trust_increased=trust,
        demo_power=demo,
        technical_dependency=dependency,
        risk=risk,
        total=total,
        rationale=rationale,
    )


def _rationale(title: str, user_value: int, setup: int, trust: int, demo: int, dependency: int, risk: int) -> str:
    strengths: list[str] = []
    if user_value >= 4:
        strengths.append("directly improves user value")
    if setup >= 4:
        strengths.append("reduces setup friction")
    if trust >= 4:
        strengths.append("increases trust")
    if demo >= 4:
        strengths.append("improves demo power")
    if dependency >= 4:
        strengths.append("unblocks later work")
    if not strengths:
        strengths.append("is the clearest available next step")
    if risk >= 4:
        strengths.append("but carries enough risk to keep the scope narrow")
    return f"{title} " + " because it " + ", ".join(strengths) + "."


def _build_instructions(
    selected: ScoredTask | None,
    root: Path,
    summaries: dict[str, str],
    user_turn: str,
    test_results: str,
) -> list[str]:
    instructions = [
        "Captain: assign only the selected smallest valuable task unless the user explicitly expands scope.",
        "Builder: make the change in the target project, not inside Ocean, unless the selected task is Ocean itself.",
        "Tester: verify function and answer whether the target user can now do something more useful.",
        "Reviewer: check quality, failure states, and whether the implementation drifts from product doctrine.",
        "Feedback Scribe: after Reif reacts, call ocean_record_feedback so doctrine and tasks stay durable.",
        "Product Manager: rerank tasks after every feedback or test result.",
    ]
    if selected:
        instructions.insert(0, f"Recommended next move: {selected.title}")
    if "AUDIENCE.md" in summaries:
        instructions.append(f"Audience signal: {summaries['AUDIENCE.md']}")
    if test_results.strip():
        instructions.append("Use the provided test results as evidence, but do not treat passing tests as proof of product value.")
    if user_turn.strip():
        instructions.append("Honor the latest user turn as the active product signal.")
    instructions.append(f"Doctrine root: {root}")
    return instructions


def _merge_advisor_instructions(
    local_instructions: list[str],
    recommendation: dict[str, Any],
    advisor_source: str,
) -> list[str]:
    task = recommendation["recommended_task"]
    instructions = [
        f"External PM advisor ({advisor_source}) selected: {task['title']}",
    ]
    if task.get("rationale"):
        instructions.append(f"Advisor rationale: {task['rationale']}")
    for feature in recommendation.get("feature_set", []):
        instructions.append(f"Feature set item: {feature}")
    for item in recommendation.get("agent_instructions", []):
        instructions.append(f"Advisor instruction: {item}")
    for item in local_instructions:
        if item not in instructions:
            instructions.append(item)
    return instructions


def _git_context(root: Path) -> dict[str, Any]:
    if not (root / ".git").exists():
        return {"is_repo": False}
    return {
        "is_repo": True,
        "status": _run_git(root, ["status", "--short"], limit=2400),
        "branch": _run_git(root, ["branch", "--show-current"], limit=200),
        "recent_commits": _run_git(root, ["log", "--oneline", "-5"], limit=1200),
    }


def _run_git(root: Path, args: list[str], *, limit: int) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, timeout=5, check=False)
    except Exception as exc:
        return f"unavailable: {exc}"
    text = (proc.stdout or proc.stderr or "").strip()
    return text[:limit]


def _detect_stack(root: Path) -> list[str]:
    stack: list[str] = []
    checks = {
        "python": ["pyproject.toml", "requirements.txt", "setup.py"],
        "node": ["package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod"],
        "docker": ["Dockerfile", "docker-compose.yml", "compose.yml"],
        "github_actions": [".github/workflows"],
        "netlify": ["netlify.toml"],
        "vite": ["vite.config.js", "vite.config.ts"],
    }
    for name, paths in checks.items():
        if any((root / path).exists() for path in paths):
            stack.append(name)
    return stack


def _read_important_files(root: Path) -> dict[str, str]:
    names = [
        "README.md",
        "readme.md",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "docs/test_report.md",
        "docs/plan.md",
        "docs/backlog.json",
    ]
    result: dict[str, str] = {}
    for name in names:
        path = root / name
        if path.exists() and path.is_file():
            try:
                result[name] = _summarize_text(path.read_text(encoding="utf-8", errors="ignore"), limit=1800)
            except Exception:
                continue
    return result


def _file_tree(root: Path, *, max_files: int = 120) -> list[str]:
    ignored = {".git", "__pycache__", ".pytest_cache", "node_modules", "venv", ".venv", "logs", "dist", "build"}
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in ignored for part in rel.parts):
            continue
        if path.is_file():
            files.append(str(rel))
        if len(files) >= max_files:
            break
    return files


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _score_value(value: Any) -> int:
    try:
        return _clamp(int(value))
    except Exception:
        return 1


def _summarize_text(text: str, limit: int = 360) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _with_heading(title: str, body: str | None) -> str | None:
    if not body:
        return None
    body = body.strip()
    if body.startswith("#"):
        return body
    return f"# {title}\n\n{body}\n"


def _append_section(path: Path, section: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {path.stem.title()}\n"
    path.write_text(_ensure_trailing_newline(existing.rstrip() + "\n\n" + section.strip()), encoding="utf-8")


def _append_unique_bullet(path: Path, text: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {path.stem.replace('_', ' ').title()}\n"
    normalized = _normalize_line(text)
    for line in existing.splitlines():
        if _normalize_line(line.lstrip("- [ ]")) == normalized:
            return False
    prefix = "- [ ] " if path.name == "TASKS.md" else "- "
    path.write_text(_ensure_trailing_newline(existing.rstrip() + "\n" + prefix + text), encoding="utf-8")
    return True


def _normalize_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower().rstrip(".")


def _ensure_trailing_newline(value: str) -> str:
    return value if value.endswith("\n") else value + "\n"


def _clamp(value: int, low: int = 1, high: int = 5) -> int:
    return max(low, min(high, value))


def dumps_result(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True)
