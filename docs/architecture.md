# 🌊 OCEAN - Multi-Agent Software Engineering Orchestrator - Architecture

## Mission

OCEAN is a web-based orchestration control room for multi-agent software engineering. It keeps product intent, agent responsibilities, backlog execution, runtime status, and verification feedback in one clear operating surface.

The standard is simple: file-first context, a small FastAPI backend, a static browser UI, reliable tests, and a containerized runtime that can be moved without ceremony.

## Goals

- Testing enabled with a repeatable pytest suite and CI checks.
- Containerized so the same application can run locally or in deployment.
- FastAPI backend for health, state, planning, chat, and orchestration endpoints.
- Static UI for the control room experience.
- Minimal dependencies and explicit operational boundaries.

## Constraints

- Prefer the Python standard library and existing project dependencies before adding packages.
- Keep the backend deployable as a single FastAPI application.
- Keep the UI static and build-output friendly.
- Avoid database requirements for the core loop until a later milestone proves the need.
- Preserve durable project state in plain files so decisions remain reviewable.

## System Shape

```text
User / Browser
      |
      v
Static UI: ui/ or ui/dist/
      |
      v
FastAPI Backend: backend/app.py
      |
      v
Ocean Core Modules: ocean/*
      |
      v
Project Files: docs/*, .ocean/*, doctrine markdown, logs/*
```

## Architecture Principles

### File-First State

OCEAN treats the repository as the source of truth. Project context, backlog, plans, doctrine, chat history, and job records are stored in files that can be reviewed, diffed, committed, and recovered.

Primary state locations:

- `docs/project.json` for project identity, goals, constraints, and vision.
- `docs/backlog.json` for planned work.
- `docs/plan.md` for visible execution sequencing.
- `docs/context_summary.md` for compressed codegen context.
- `.ocean/actors.json` for crew definitions.
- `.ocean/jobs.json` for generated jobs.
- `.ocean/chat.jsonl` for chat history.
- Doctrine files such as `VISION.md`, `TASKS.md`, `FEEDBACK.md`, and `DECISIONS.md`.

### Small Control Plane

The FastAPI backend should coordinate the system, not become a general application platform. Its job is to expose bounded operations over project state and orchestration workflows.

Core responsibilities:

- Serve the static UI.
- Report runtime health.
- Read project context and doctrine.
- Manage actors and jobs.
- Accept chat turns and product feedback.
- Produce scoped handoff prompts for coding agents.

### Static Command Surface

The UI is the operator console. It should help the user see the mission, crew, files, chat, and next action without hiding important state behind opaque services.

Expected interface areas:

- Project identity and runtime health.
- Crew and actor coverage.
- Chat-first feedback loop.
- Relevant file inspection.
- Job planning and handoff prompts.
- Test and readiness summaries.

## Runtime Components

### FastAPI Backend

Anchor module: `backend/app.py`

Expected endpoint groups:

- Health: `GET /healthz`
- Root or app shell: `GET /`
- State: project, actors, coverage, doctrine, and runtime summary.
- Chat: record user turns, feedback, and test notes.
- Jobs: generate and list scoped work items.
- Files: read bounded project files safely under the project root.

Backend standards:

- Validate request and response shapes with typed models where useful.
- Resolve paths safely under the intended project root.
- Return clear HTTP errors for missing files, invalid input, or unsafe paths.
- Keep endpoint names aligned with product workflow.
- Cover new behavior with focused pytest tests.

### Static UI

Source location: `ui/`

Build output: `ui/dist/`

The UI may run in two modes:

- Development: Vite or a lightweight static dev server.
- Production: compiled static assets served by FastAPI or a static host.

UI standards:

- Prioritize dense, scan-friendly operational views over marketing layout.
- Keep controls predictable and accessible.
- Use stable dimensions for panels, lists, buttons, and message areas.
- Keep text readable on mobile and desktop.
- Avoid hidden state when project files already provide durable context.

### Ocean Core Modules

Core modules under `ocean/` hold reusable orchestration logic. The backend should call these modules rather than duplicating file parsing, actor handling, planning, or product-loop behavior.

Key domains:

- Actors and personas.
- Planning and task generation.
- Product chat and feedback capture.
- Runtime status and job lifecycle.
- MCP or external-agent integration surfaces.

## Data Flow

### First Load

1. Browser requests the UI.
2. UI requests health and project state.
3. Backend reads project files and actor definitions.
4. UI renders the current mission, crew, files, jobs, and chat context.

### Feedback Turn

1. User submits a chat message, bug note, screenshot context, or product correction.
2. Backend appends durable feedback to `.ocean/chat.jsonl` and relevant doctrine files when requested.
3. Planning logic ranks or generates the next action.
4. UI displays the updated conversation and actionable handoff.

### Job Planning

1. User intent is combined with project context, backlog, doctrine, and recent results.
2. OCEAN creates scoped work items with owner, context, acceptance criteria, verification, and handoff notes.
3. Coding agents receive narrow prompts instead of broad project ambiguity.
4. Test results and user feedback close the loop.

## Deployment Model

The application should support three operating banners:

### Local Development

- Backend: `uvicorn backend.app:app --reload`
- UI: Vite dev server or static server against `ui/`
- Tests: `pytest`

### Container Runtime

- Build with the root `Dockerfile`.
- Serve the FastAPI app on `$PORT` or `8000` by default.
- Include static UI assets when available.
- Expose `/healthz` for readiness checks.

### CI Runtime

- GitHub Actions installs dependencies.
- Runs pytest.
- Optionally checks UI build if frontend tooling is present.
- Fails fast on regressions.

## Testing Strategy

Testing is a first-class readiness gate.

Minimum coverage:

- Health endpoint returns a successful payload.
- Root endpoint or app shell is reachable.
- State and file endpoints handle missing or unsafe paths correctly.
- Planning and chat operations write durable records predictably.
- CLI and MCP entrypoints keep smoke coverage where they exist.

Acceptance criteria for changes:

- New backend behavior has pytest coverage.
- New file-writing behavior is tested against temporary directories.
- Static UI changes preserve basic build or smoke checks.
- CI can run without private credentials.
- `docs/test_report.md` records the latest meaningful verification pass.

## Security and Safety Boundaries

- Do not read or write outside the configured project root through API file operations.
- Do not expose environment secrets in UI state, logs, chat history, or generated prompts.
- Treat shell execution and external-agent handoffs as explicit future capabilities with narrow contracts.
- Keep generated jobs reviewable before execution.
- Prefer append-only histories for feedback and chat records.

## Specialist Delegation

OCEAN assigns work by domain so execution remains disciplined:

- Moroni: architecture, mission framing, sequencing, and acceptance criteria.
- Q: FastAPI backend, contracts, models, and tests.
- Edna: static UI, interaction design, and design-system consistency.
- Mario: CI, Docker, deployment, and local runtime readiness.
- Tony: test execution, stress checks, and concise verification reports.

The architecture should keep these lanes visible. Each job should name its owner, expected files, acceptance criteria, and verification path.

## Risks

| Risk | Mitigation |
| --- | --- |
| File state becomes inconsistent | Centralize read/write helpers and test state transitions. |
| Backend grows too broad | Keep endpoint groups tied to orchestration workflows. |
| UI becomes decorative instead of operational | Prioritize chat, jobs, files, actors, and health as first-screen concerns. |
| Local and container behavior diverge | Use the same FastAPI app and health endpoint in both modes. |
| Agent handoffs become vague | Require objective, context, acceptance criteria, verification, and handoff notes. |

## Readiness Review

Before treating a build as ready, the project should meet these checks:

- `pytest` passes locally and in CI.
- The app starts with the documented command.
- `/healthz` returns a healthy payload.
- The static UI loads and can reach the backend.
- The Docker image builds and serves the app.
- Project context files exist and remain human-readable.
- The next action is visible in backlog, plan, or generated jobs.

## Near-Term Phases

### Phase 1: Stable Shell

- Confirm FastAPI health and root endpoints.
- Serve or link the static UI.
- Keep project and backlog files readable.
- Maintain passing tests.

### Phase 2: Control Room

- Display project context, actors, files, chat, and jobs.
- Add safe state endpoints.
- Capture feedback durably.
- Generate scoped handoff prompts.

### Phase 3: Runtime Discipline

- Harden CI and Docker flows.
- Record test reports.
- Add deployment notes and dry-run checks.
- Make readiness status visible in the UI.

### Phase 4: Agent Coordination

- Improve job lifecycle tracking.
- Add clearer owner handoffs.
- Connect MCP or external agent workflows behind explicit contracts.
- Preserve user approval at key execution boundaries.
