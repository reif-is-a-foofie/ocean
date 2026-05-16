# 🌊 OCEAN

**Multi-agent software engineering orchestrator for the CLI.**

Ocean sits between you and your coding agents (Codex CLI, Claude CLI, Cursor). It runs clarification, planning, delegation, and handoff so delivery stays orchestrated — not ad hoc chat.

```
reify@Reifs-MacBook-Pro ~ % ocean
🌊 Ocean: Ahoy! I'm Ocean — caffeinated and ready to ship. [09:30:29]
🌊 Ocean: Workspace: /Users/reify/Classified/ocean/ocean_reify [09:30:31]
🌊 Ocean: You drive goals. I run the crew, timing, and token budget.
🌊 Ocean: Codegen backend → cursor_handoff [09:30:39]
🤿 Ocean Doctor (preflight): codex=/usr/local/bin/codex ver=codex-cli 0.129.0 [09:30:50]
```

## Install

```bash
pip install ocean
ocean --help
```

Requires Python 3.11+. Codex CLI (`npm install -g @openai/codex`) or Claude CLI required for code generation.

## How it works

Ocean is an **orchestrator** — it does not write code itself. It:

1. **Clarifies** your intent with Moroni (Architect)
2. **Assembles** a crew — Moroni, Q, Edna, Mario, Tony
3. **Dispatches** tasks to your agent CLI (Codex or Claude)
4. **Verifies** results and surfaces what's next

The agent does the coding. Ocean handles who gets what, when, and in what order.

## Quick start

```bash
# Full interactive flow
ocean

# Quick REPL
ocean chat --quick
```

In the REPL:

```
ocean> prd: build a task tracker CLI with add/list/done commands
✅ PRD updated (docs/prd.md)

ocean> plan
🌊 Ocean: Preparing project context…
✅ Plan ready.

ocean> build
🌊 Ocean: Dispatching to agent — building now…
🌊 Ocean: ✅ wrote task_tracker.py
✅ Build complete — 1 file(s) written.

ocean> crew
🕹️ Moroni
  · Phase 1: gather resources. Phase 2: secure interfaces. 🕹️
  · Skills — Vision synthesis, phased roadmaps, acceptance criteria …

ocean> exit
```

## Commands

| Command | What it does |
|---|---|
| `ocean` | Full interactive chat — clarify → crew → plan → build |
| `ocean chat` | Same as bare `ocean` (explicit subcommand) |
| `ocean chat --quick` | Quick REPL with `prd:` / `plan` / `build` / `crew` / `status` and free-text chat |
| `ocean chat-repl` | Standalone quick REPL with the same command surface |
| `ocean crew` | Show each agent's skills and voicing |
| `ocean clarify` | Capture project intent, save `docs/project.json` |
| `ocean doctor` | Check Codex/Claude auth and environment |
| `ocean onboard` | First-run setup: venv + pip install + pytest |
| `ocean mcp-server` | Run Ocean as a stdio MCP server for Cursor/Codex |

## The crew

Each agent owns a slice of the SDLC and has a voice defined in `docs/personas.yaml`:

| Agent | Role |
|---|---|
| 🕹️ **Moroni** | Architect — vision, planning, crew coordination |
| 🔧 **Q** | Backend — APIs, services, data models, tests |
| 🎨 **Edna** | Design — UI/UX, tokens, accessibility, visual QA |
| 🍄 **Mario** | DevOps — CI/CD, Docker, deployment, monitoring |
| 🧪 **Tony** | Test pilot — stress tests, telemetry, bug triage |

## Codegen backends

Set in `docs/ocean_prefs.json` or via `OCEAN_CODEGEN_BACKEND`:

| Backend | How it works |
|---|---|
| `codex` | Calls `codex exec` directly (default when Codex is authed) |
| `cursor_handoff` | Writes `docs/handoffs/` for Cursor Composer to pick up |
| `openai_api` | Calls OpenAI API directly (requires `OPENAI_API_KEY`) |
| `dry_plan_only` | Generates backlog/plan only, no code execution |

## MCP server

Ocean can run as an MCP server for Cursor or any MCP client:

```bash
ocean mcp-server
```

Exposes `ocean_turn`, `ocean_next_action`, `ocean_record_feedback`, `ocean_bootstrap_doctrine`, `ocean_health`, `ocean_set_codegen_backend`.

## Project layout

```
docs/
  prd.md          — what to build (set via `prd:` in REPL)
  project.json    — clarified spec (name, kind, goals, vision)
  personas.yaml   — agent voices and skills
  plan.md         — generated backlog
  handoffs/       — Cursor handoff files (cursor_handoff mode)
logs/
  events-*.jsonl  — structured session events
ocean/
  cli.py          — all commands
  codex_exec.py   — Codex CLI dispatch
  persona.py      — voice loading from personas.yaml
  planner.py      — backlog generation and execution
  pty_harness.py  — PTY driver for integration tests
```

## Testing

```bash
pytest tests/       # 70 tests, ~25s
ocean doctor        # environment + auth check
```

## License

MIT
