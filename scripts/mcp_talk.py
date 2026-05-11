#!/usr/bin/env python3
"""Talk to the Ocean MCP stdio server (same wire protocol as Cursor).

Demonstrates the engagement loop agents should use: health → version → turn.

Usage from repo root::

    ./venv/bin/python scripts/mcp_talk.py
    ./venv/bin/python scripts/mcp_talk.py /path/to/target/repo
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    from ocean.mcp_client import StdioJsonRpcClient

    cmd = [sys.executable, "-m", "ocean.mcp_server"]
    c = StdioJsonRpcClient(cmd=cmd, cwd=repo)
    c.start()
    try:
        init = c.initialize(timeout=15)
        print("=== initialize ===")
        print(json.dumps(init, indent=2)[:800])

        ver = c.call_tool("ocean_version", {})
        print("\n=== ocean_version (structured) ===")
        print(json.dumps(ver.get("structuredContent", ver), indent=2))

        health = c.call_tool("ocean_health", {"project_root": str(repo)})
        print("\n=== ocean_health (structured) ===")
        print(json.dumps(health.get("structuredContent", health), indent=2))

        turn = c.call_tool(
            "ocean_turn",
            {
                "project_root": str(repo),
                "user_turn": "Keep Ocean MCP healthy: prefer stdio tools for auto-heal and version checks.",
                "use_advisor": False,
            },
        )
        print("\n=== ocean_turn (text preview) ===")
        blocks = turn.get("content") or []
        for b in blocks[:3]:
            if b.get("type") == "text":
                t = b.get("text", "")
                print((t[:1200] + "…") if len(t) > 1200 else t)
        print("\n=== ocean_turn (selected_task title) ===")
        sc = turn.get("structuredContent") or {}
        st = sc.get("selected_task") or {}
        print(st.get("title") or json.dumps(st)[:400])

        print("\nOK — MCP session engaged.")
        return 0
    finally:
        c.stop()


if __name__ == "__main__":
    raise SystemExit(main())
