# Product Requirements Document (PRD) — Ocean

Project Name: Ocean
Tagline: OCEAN = OCEAN Creates Everything And (N)othing

A CLI-first, multi-agent system that turns a plain‑text PRD into a working piece of software using Codex MCP instances per agent. You interact conversationally; Ocean splits tasks across agents and coordinates delivery.

## Overview

- CLI: `ocean` launches a TUI chat and activity view.
- PRD input: Reads `README.md` or a provided file; asks clarifying questions.
- Agents (each runs its own Codex MCP instance):
  - 🌊 Moroni — Architect (vision, plan, decomposition)
  - 🪓 Q — Backend/Tools (APIs, integrations, tests)
  - 👓 Edna — Designer (UI/UX, HTML/CSS/components)
  - 🍄 Mario — DevOps (CI/CD, Docker, deploy)
- Six Primitives workflow: publish → accept → action → submit → confirm → seal.
- Milestones produce user‑visible deliverables (docs, code, running runtime).

## Goals

- Chat-driven builder: `ocean` manages an agent crew to ship software.
- Strong orchestration: dependency-aware, parallel execution where safe.
- Human-in-the-loop: intervene, clarify, approve.
- Workspaces: `projects/<slug>` with venv, DB, Docker, compose.

## Non-Goals

- Not a general PM tool; not Jira/Linear replacement.
- Not for non-software chores.

## Interaction Model

- Launch: `ocean` (no args) → TUI shows left Activity tree and right Chat.
- User can paste PRD or point to a file; Ocean asks follow-ups.
- Agents converse in the same TUI; user may interject at any time.

## Six Primitives

- publish: propose task(s)
- accept: assign steward + start 7‑day SLA
- action: agent performs work via Codex MCP
- submit: deliver files/manifest
- confirm: approve/iterate
- seal: lock and archive

## Deliverables by Milestone

- M1: Ocean skeleton (TUI, PRD ingestion)
- M2: Predefined agents (CrewAI or local orchestrator) with MCP instances
- M3: Task lifecycle (Six Primitives) with logs
- M4: Collaboration layer (live agent chat with mentions)
- M5: Deployment & Execution (workspace scaffold; local runtime)
- M6: Codex MCP integration end-to-end (real tool calls)

## MCP Integration

- Each agent has a dedicated MCP instance; Ocean coordinates.
- Tools: codegen, write, run, read, diff; confirm before destructive actions.
- Config via env: OCEAN_MCP_PROVIDER, OCEAN_MCP_ENDPOINT, OCEAN_MCP_API_KEY.

## Workspace

- `projects/<slug>` contains backend/, ui/, devops/, data/app.db, .env, run.sh, Dockerfile, docker-compose.yml.
- `docker compose up --build` runs backend + static UI locally.

Generated and maintained by OCEAN. This PRD is a living document.
