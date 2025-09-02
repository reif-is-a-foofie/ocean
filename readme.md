# OCEAN PRD (Codex + Cursor Version)

## Name & Expansion

**OCEAN = OCEAN Creates Ex And Nihilo**

---

## Vision

Ocean is a **CLI/TUI multi-agent orchestrator** that spins up a Codex-powered software engineering team on demand.

* You invoke it simply with `ocean`.
* It asks clarifying questions (via Moroni, the architect/brain) until the project vision is understood.
* Then it spins up the predefined crew:

  * **Moroni** — Architect/Brain. Clarifies vision, orchestrates.
  * **Q** — Backend/tools engineer. Knows APIs, data, services.
  * **Edna** — Designer/UI/UX. Produces mockups, CSS, flows.
  * **Mario** — DevOps. Knows hosting (Railway, Vercel, Render, etc.), CI/CD, deploys final product.

The crew works together in visible chat logs inside the CLI/TUI.

Ocean inherits the **Codex CLI** for natural language, MCP-based execution, and context management. Cursor consumes this PRD + rules to implement the system.

---

## Guiding Principles

1. **One word, one entrypoint** — just `ocean`.
2. **Crew-based orchestration** — no abstract PM software; it’s a “team that codes.”
3. **Agile deliverables** — every milestone produces something the user can actually use/test.
4. **Immutability** — logs, repos, and agent conversations are preserved.
5. **Transparency** — user can see every conversation between agents.

---

## Core Flow

1. User runs `ocean`.
2. Moroni greets user, asks clarifying questions about what’s being built (no hardcoded prompts — natural Codex context).
3. Once vision is clear enough (e.g., “Web app,” “API service,” “CLI”), Moroni spins up the crew.
4. Q, Edna, and Mario each propose and execute tasks.
5. Deliverables are committed locally in a `repo/` folder.
6. Mario deploys — end result is a live, usable instance.

---

## Agent Context

* **Moroni (Architect)**

  * Access: project PRD, user clarifications, repo structure.
  * Role: split project into milestones, assign work to Q, Edna, Mario.
  * Interface: chat-first in Codex CLI.

* **Q (Backend Engineer)**

  * Access: GitHub context, API docs, open-source libraries.
  * Role: build backend services, data models, integrations.
  * Deliverables: code in `backend/`.

* **Edna (Designer)**

  * Access: Figma/HTML/CSS boilerplates, open-source design systems.
  * Role: build UI flows, mockups, frontend styling.
  * Deliverables: `ui/` code, `design.md`.

* **Mario (DevOps)**

  * Access: deployment platforms (Railway, Render, Vercel).
  * Role: provision infra, set up CI/CD, deploy working app.
  * Deliverables: `.github/workflows/`, `Dockerfile`, live URL.

---

## Technical Setup

* **Codex CLI** provides MCP interface for each agent.
* **CrewAI** (or similar orchestration lib) coordinates task assignment, conversation passing, and repo commits.
* **Repo structure** is generated automatically:

  * `/backend`
  * `/ui`
  * `/devops`
  * `/docs`
* **Chat logs** saved into `/logs`.

---

## Milestones (Agile, Deliverables to User Each Step)

### M1 — Bootstrapping Ocean

* Implement `ocean` CLI entrypoint (Typer or Click).
* Print welcome banner:

  ```
  🌊 Welcome to OCEAN  
  (OCEAN = OCEAN Creates Ex And Nihilo)  
  ```
* Enter Codex chat loop (interactive Q\&A with Moroni).
* **Deliverable:** User runs `ocean` and gets interactive conversation.

### M2 — Vision Clarification

* Moroni (via Codex) asks clarifying questions.
* Understands if project is server, app, CLI, etc.
* Stores clarified project spec in `/docs/project.json`.
* **Deliverable:** User exits clarification with a saved project spec.

### M3 — Crew Spin-Up

* Instantiate Moroni, Q, Edna, Mario as Codex MCP agents.
* Each agent introduces itself in chat.
* Agents receive project.json context.
* **Deliverable:** Visible crew chat log confirming readiness.

### M4 — First Sprint

* Moroni assigns first atomic milestone.
* Q codes backend stub.
* Edna generates UI scaffold.
* Mario sets up CI pipeline.
* **Deliverable:** Repo initialized with working Hello World project scaffold.

### M5 — Iteration & Testing

* User can run `ocean test`.
* Crew executes milestone tasks → updates repo.
* Codex applies diffs automatically.
* **Deliverable:** Usable prototype in local repo.

### M6 — Deployment

* Mario provisions hosting (Railway/Render).
* Deploys app.
* **Deliverable:** Live URL printed in terminal.

---

## Definition of Done

* `ocean` runs as a single command.
* Moroni clarifies vision until project spec is saved.
* Crew (Q, Edna, Mario) executes in visible chat log.
* Repo scaffold created and updated iteratively.
* CI/CD and deployment live.
* Final result: a **user-accessible deployed app**.

---

## CursorRules (Expansion)

* Always break tasks into atomic steps.
* Each milestone must ship a usable deliverable (repo code, prototype, deployment).
* Agents must converse visibly in logs.
* Use Codex MCP for coding tasks (Q, Edna, Mario).
* PRD is the single source of truth; if unclear, Moroni must ask user.
* Cursor must enforce repo structure and incremental commits.



