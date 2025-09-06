# Changelog

## 0.2.27 — 2025-09-06

- Humanized typewriter: variable per‑character delay with jitter and punctuation pauses
  - Controls: OCEAN_TYPEWRITER_HUMAN=1 (default), OCEAN_TW_VARIANCE (±0.6), OCEAN_TW_PUNCT_MULT (4.0), OCEAN_TW_COMMA_MULT (2.0), OCEAN_TW_SPACE_MULT (0.3), OCEAN_TW_MAX_DELAY (0.12)
  - Base speed still adjustable via OCEAN_TYPEWRITER_DELAY (default 0.025)

## 0.2.26 — 2025-09-06

- Typewriter default speed set to 0.025s (override with OCEAN_TYPEWRITER_DELAY)

## 0.2.24 — 2025-09-06

- Pipe Codex logs back into the feed (opt-in):
  - OCEAN_CODEX_STREAM=1 → run exec in streaming mode, print JSONL events as concise "🪵 Codex:" lines
  - OCEAN_CODEX_JSON=1 → pass --json; combined with stream for better event fidelity
  - Still writes full logs to logs/codex-*.log and parses final JSON from stdout or --output-last-message

## 0.2.23 — 2025-09-06

- Moroni now initializes CrewAI by default (OCEAN_CREWAI_BY_MORONI=1):
  - Installs/verification: checks that `crewai` is importable, emits status
  - Runs `CrewRunner.run_project(PRD)` to ensure the backbone is working
  - Falls back gracefully if CrewAI unavailable
  - Legacy CLI CrewAI block only runs when OCEAN_CREWAI_BY_MORONI=0

## 0.2.22 — 2025-09-06

- Make CrewAI the orchestration backbone by swapping MCP-only tools for direct Codex codegen:
  - crewai_adapter now calls codex_exec.generate_files and writes files directly
  - Removes OCEAN_MCP_ONLY requirement; no MCP dependency for CrewAI path
  - Doctor now reports crewai enabled/installed status

## 0.2.21 — 2025-09-06

- Defaults adjusted per policy:
  - Search ON by default (disable with OCEAN_CODEX_SEARCH=0)
  - Sandbox ON (workspace-write) by default; bypass only if OCEAN_CODEX_BYPASS_SANDBOX=1
  - E2E probe and client helpers use the same defaults

## 0.2.20 — 2025-09-06

- Remove Brave Search integration from context bundling; Codex --search now handles web access
- Add cleanup commands: `ocean cleanup scan|apply` to remove old projects (ocean_brython-snake, legacy projects), brave_search.py, mcp_trace.py, and optional TUI/CrewAI files
- Keep MCP stubs but continue to no-op; agents unaffected

## 0.2.19 — 2025-09-06

- Advanced Codex flags:
  - OCEAN_CODEX_JSON=1 → pass --json and --output-last-message; parse last message on fallback
  - OCEAN_CODEX_PROFILE passthrough via --profile
  - Auto --skip-git-repo-check when outside a Git repo
  - Optional --cd <cwd> (default on; set OCEAN_CODEX_CD=0 to disable)
- Startup Doctor: one-line humor checks (enabled by default; disable with OCEAN_STARTUP_DOCTOR=0)
- Defaults recap: sandbox bypass ON by default; search OFF unless OCEAN_CODEX_SEARCH=1

## 0.2.18 — 2025-09-06

- Feed-only output by default: monkey-patch console.print to route through feed (disable with OCEAN_FEED_ONLY=0)
- Sanitize feed lines: strip ANSI escapes, collapse whitespace, clamp line width (OCEAN_FEED_MAXCOL)
- Keeps columns aligned and prevents external tool banners from offsetting layout

## 0.2.17 — 2025-09-06

- Default to sandbox bypass for Codex exec (can disable with OCEAN_CODEX_BYPASS_SANDBOX=0)
- Change search default: OFF unless OCEAN_CODEX_SEARCH=1

## 0.2.16 — 2025-09-06

- Add sandbox/approval controls to all Codex exec calls:
  - Env: OCEAN_CODEX_BYPASS_SANDBOX=1 → pass --dangerously-bypass-approvals-and-sandbox
  - Env: OCEAN_CODEX_SANDBOX=read-only|workspace-write|danger-full-access → pass --sandbox
  - Env: OCEAN_CODEX_APPROVAL=untrusted|on-failure|on-request|never → pass --ask-for-approval
- Env summary now reports sandbox/approval settings

## 0.2.15 — 2025-09-06

- Stop claiming "Using Codex subscription" before success; rely on env summary instead
- Store last Codex error detail and surface it via agent messages ("Codegen failed — …")
- Swap generic "Codegen unavailable" lines across agents for detailed failure reasons

## 0.2.14 — 2025-09-06

- Enable typewriter output by default with OCEAN_TYPEWRITER=1 (unless explicitly disabled or in tests)
- Default OCEAN_TYPEWRITER_DELAY to 0.1s (override with env)

## 0.2.13 — 2025-09-06

- Token diagnostics: record token source (auth.json/grep/auth subcommand) and decode expiry for env summary
- New command: `ocean token doctor` prints token presence/length/preview, source, expiry, and `codex auth` head
- Env summary now shows token source and exp when available

## 0.2.12 — 2025-09-06

- Make agent status more informative: replace "Context prepared." with bundle path, size, file count, PRD/search presence, and query count
- Fix incorrect agent label in Q backend context message

## 0.2.11 — 2025-09-06

- Run all Codex execs with `--search` for internet access (default can be disabled via `OCEAN_CODEX_SEARCH=0`)
- Mask prompt in command logs more cleanly

## 0.2.10 — 2025-09-06

- Fix codex exec invocation: remove --model, positional PROMPT
- Make e2e probe tolerant (extract JSON after banners)
- Don’t abort early unless OCEAN_STRICT_CODEX=1; add detailed rc/cmd/err/out
- Add OCEAN_CODEX_DEBUG for richer logs
