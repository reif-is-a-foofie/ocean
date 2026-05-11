# Ocean MCP for Cursor

Ocean can run outside a target codebase as a stdio MCP server. Cursor or another coding agent can call it each turn for product guidance, feedback capture, and task ranking.

The local Web UI is chat-first. Keep orchestration simple: one chat, a five-person crew, and filesystem context. Users can mention files with `@path` and update doctrine through chat:

```text
update VISION.md: Ocean stays simple: chat is the interface, files are context, and Cursor gets one job at a time.
append to TASKS.md: Verify first-run Cursor setup.
```

The default crew is capped at five actors: Captain, Edna, Q, Mario, and Scrooge.

Ocean does not ship an LLM. It keeps durable product context and asks the available brain to reason over it.

## Install

From the Ocean repo:

```bash
pip install -e .
```

This exposes:

```bash
ocean-mcp
ocean mcp-server
python -m ocean.mcp_server
```

## Cursor Configuration

Add Ocean to Cursor's MCP config:

```json
{
  "mcpServers": {
    "ocean": {
      "command": "ocean-mcp",
      "args": []
    }
  }
}
```

If the console cannot find `ocean-mcp`, use the explicit Python module form:

```json
{
  "mcpServers": {
    "ocean": {
      "command": "python",
      "args": ["-m", "ocean.mcp_server"]
    }
  }
}
```

## Turn Workflow

At the start of a coding turn, call `ocean_turn` with:

```json
{
  "project_root": "/absolute/path/to/target/repo",
  "user_turn": "Latest user request",
  "test_results": "Optional test summary",
  "candidate_tasks": ["Optional task A", "Optional task B"],
  "use_advisor": true
}
```

If no external advisor is configured, the response still includes `advisor_prompt`. Cursor's own model can read that prompt and produce the product-manager judgment. That is the default model-agnostic path.

## Optional Reasoning CLI

To let Ocean ask a reasoning engine directly, configure one of these environment variables before launching the MCP server:

```bash
export OCEAN_PM_ADVISOR_CMD='your-reasoning-cli --stdin'
```

Ocean sends the Product Manager prompt on stdin and reads stdout as advice.

For Codex:

```bash
export OCEAN_PM_ADVISOR=codex
```

Ocean then calls `codex exec` in a read-only sandbox and folds the answer into `ocean_turn`. This keeps Ocean open-source and model-agnostic while still using whatever brain the user already has installed.

After Reif reacts to a build or test, call the same tool with `feedback`, or call `ocean_record_feedback` directly:

```json
{
  "project_root": "/absolute/path/to/target/repo",
  "feedback": "This feels too technical. Explain it like a smart assistant, not a terminal.",
  "test_context": "Onboarding flow tested locally."
}
```

Ocean will maintain these files in the target repo:

- `VISION.md`
- `AUDIENCE.md`
- `PRODUCT_PRINCIPLES.md`
- `UX_RULES.md`
- `POSITIONING.md`
- `ROADMAP.md`
- `TASKS.md`
- `FEEDBACK.md`
- `DECISIONS.md`

## Available Tools

- `ocean_turn`: record optional feedback and return the next highest-value instruction.
- `ocean_next_action`: rank tasks and return the smallest valuable next move.
- `ocean_record_feedback`: append feedback and update doctrine.
- `ocean_bootstrap_doctrine`: create missing doctrine files without overwriting existing files.

## Orchestration Jobs

Chat and `/api/jobs/plan` turn product intent into discrete Cursor-ready jobs. Each job includes:

- owner persona
- lifecycle phase
- objective
- context
- instructions
- acceptance criteria
- verification
- handoff notes
- a copyable Cursor prompt

This is the core division of labor: Cursor, Claude, and Codex write code well; Ocean drives the software-development team process around them without becoming a second full coding UI.

## How Ocean Knows What To Build

Ocean does not guess from doctrine alone. For each turn it pulls a bounded build context from the target repo:

- current git branch, status, and recent commits
- detected stack from manifests and config files
- important files such as `README.md`, `pyproject.toml`, `package.json`, `docs/test_report.md`, `docs/plan.md`, and `docs/backlog.json`
- a bounded file tree
- product doctrine and recent feedback
- latest user turn and test results supplied by the coding agent

Ocean then sends that context to the available reasoning brain. The preferred advisor response is strict JSON:

```json
{
  "recommended_task": {
    "title": "smallest next valuable change",
    "rationale": "why this beats the alternatives",
    "scores": {
      "user_value": 5,
      "setup_friction_reduced": 4,
      "trust_increased": 4,
      "demo_power": 3,
      "technical_dependency": 3,
      "risk": 2
    }
  },
  "feature_set": ["specific feature to build"],
  "agent_instructions": ["instruction for the coding agent"],
  "doctrine_implications": ["durable lesson"],
  "questions": []
}
```

Ocean parses that JSON and returns it as `advisor_recommendation` plus normalized agent instructions. If the advisor returns plain text, Ocean still returns the raw advice.

The governing question is:

> What is the smallest next change that makes this more valuable to the target user?
