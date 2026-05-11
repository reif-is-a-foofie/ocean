# Toad fork: first-run integration with Ocean

Ocean ships no TUI here; host apps (e.g. a **fork of [Toad](https://github.com/batrachianai/toad)**) should orchestrate **`ocean chat`** from the user’s repo root—optionally behind a pseudo-TTY—or drive prefs via MCP.

## Session events (`logs/events-*.jsonl`)

Each `ocean chat` invocation sets **`OCEAN_EVENTS_FILE`** to a new **`logs/events-YYYYMMDD-HHMMSS.jsonl`**. Tail it for onboarding UI lines.

Envelope for setup steps:

- **`event`** — always **`"setup"`** for onboarding payloads.
- **`phase`** — **`"setup"`**.
- **`kind`** — **`phase_start` \| `phase_end` \| `question` \| `answer` \| `info`**.
- **`id`** — e.g. `welcome`, `backend_choice`, `credentials`, `crew_intro`, `project_clarify`, `codegen_backend`, `openai_api_key`.

**Secrets are never emitted.** `openai_api_key` phases only include booleans like `saved` / `prefix_masked`.

Example:

```json
{"event":"setup","ts":"…","phase":"setup","kind":"question","id":"codegen_backend","message":"Where should Ocean send codegen?","choices":["codex","cursor_handoff","dry_plan_only","openai_api"]}
```

## MCP (non-TTY hosts)

If `ocean chat` stdin is **not** a TTY:

- **`OCEAN_SKIP_BACKEND_PROMPT=1`** or **`OCEAN_CODEGEN_BACKEND=…`** avoids defaulting blindly to Codex.
- Prefer **`ocean_set_codegen_backend`** `{ "project_root": "…", "backend": "codex" }`.
- **`ocean_health`** returns **`valid_codegen_backends`** and **`recovery_hints`** for status UI.

Keep **AGPL** compliance when combining Toad and Ocean binaries.
