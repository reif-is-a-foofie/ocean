# Cursor Rules: Tight Code, Zero Drift

## Code Quality & Commit Hygiene
- [ ] Every commit is atomic: one logical change per commit.
- [ ] No sweeping refactors; only surgical, well-scoped edits.
- [ ] All new files, functions, and classes must have docstrings and type hints.
- [ ] No dead code or commented-out blocks left in the codebase.
- [ ] Use open-source libraries where possible; avoid reinventing the wheel.
- [ ] All code must pass linting and formatting (black, isort, flake8).

## Agent Protocols
- [ ] Before any code change, the agent must declare intent in `docs/plan.md` (see structure below).
- [ ] Each task must be logged as `STARTING` (with agent, timestamp, description, acceptance criteria).
- [ ] After completion, log a `COMPLETED` entry with summary and links/diffs.
- [ ] No batching: each action/task is logged and scoped to a single, well-defined change.
- [ ] If interrupted, the next agent resumes from the last `STARTING` entry.
- [ ] All actions are also appended to the session log in `logs/`.

## Plan & Backlog
- [ ] All milestones, tasks, and agent actions are tracked in `docs/plan.md` and `docs/backlog.json`.
- [ ] Each task in `plan.md` has: status, owner, description, acceptance criteria, timestamp.
- [ ] No task is marked `completed` without meeting acceptance criteria.

## Documentation
- [ ] `docs/plan.md` and `docs/cursor_rules.md` are referenced in the README and enforced in code review.
- [ ] All agents and contributors must read and follow these rules before contributing.