#!/usr/bin/env python3
"""Smoke-test Ocean MCP stdio server without pytest.

Starts ``python -m ocean.mcp_server``, runs initialize → tools/list → ping, prints OK.

Run from repo root::

    ./venv/bin/python scripts/mcp_stdio_smoke.py

Cursor and other hosts attach the same binary over stdio; this script mirrors that wiring.
"""
from __future__ import annotations

import sys


def main() -> int:
    from ocean.mcp_client import StdioJsonRpcClient

    cmd = [sys.executable, "-m", "ocean.mcp_server"]
    client = StdioJsonRpcClient(cmd=cmd)
    client.start()
    try:
        init = client.initialize(timeout=15)
        name = (init or {}).get("serverInfo", {}).get("name")
        if name != "ocean":
            print(f"FAIL: expected serverInfo.name ocean, got {name!r}", file=sys.stderr)
            return 1
        tools = client.list_tools()
        print(f"OK initialize + tools/list ({len(tools)} tools)")
        client.rpc("ping", {}, timeout=5)
        print("OK ping")
        hv = client.call_tool("ocean_health", {})
        hints = (hv.get("structuredContent") or {}).get("recovery_hints") or []
        print(f"OK ocean_health ({len(hints)} hint(s))")
        return 0
    finally:
        client.stop()


if __name__ == "__main__":
    raise SystemExit(main())
