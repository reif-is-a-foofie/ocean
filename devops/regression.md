# Ocean regression — stdio MCP server

Ocean’s **production integration surface** for tooling (Cursor, scripts, CI) is the **stdio MCP server**:

```bash
python -m ocean.mcp_server
```

It speaks **Content-Length–framed JSON-RPC** on stdin/stdout (same framing as `StdioJsonRpcClient` in `ocean/mcp_client.py`). There is no HTTP port for this server.

## Quick smoke (no pytest)

From repo root (prefer `./venv/bin/python`):

```bash
./venv/bin/python scripts/mcp_stdio_smoke.py
```

## Automated regression

```bash
./scripts/regression.sh
```

That runs **pytest** (including **`tests/test_mcp_stdio.py`**) and CLI `--help` / `--version`.

## Staging over SSH

After `git pull`:

```bash
./scripts/regression.sh
./venv/bin/python scripts/mcp_stdio_smoke.py
```

## Cursor / MCP host config

Point your MCP config at the same command Cursor would spawn, for example:

- Command: path to `python` (or `venv/bin/python`)
- Args: `-m`, `ocean.mcp_server`

See `docs/mcp_cursor.md` if present for copy-paste snippets.

## What not to use for integration regression

- **`ocean codex-chat`** is a terminal UI around the Codex CLI, not the MCP stdio contract.
- PTY-only hacks are not the integration boundary; **stdio MCP is.**
