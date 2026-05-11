"""Regression for Ocean MCP over stdio (Content-Length framed JSON-RPC).

This is the supported integration surface for Cursor and other MCP hosts:
``python -m ocean.mcp_server`` speaks MCP-style requests on stdin/stdout.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ocean.mcp_client import MCPError, StdioJsonRpcClient


@pytest.fixture
def mcp_stdio_cmd() -> list[str]:
    return [sys.executable, "-m", "ocean.mcp_server"]


def test_mcp_stdio_initialize_list_tools_ping(mcp_stdio_cmd: list[str]) -> None:
    client = StdioJsonRpcClient(cmd=mcp_stdio_cmd)
    try:
        client.start()
        initialized = client.initialize(timeout=10)
        assert initialized["serverInfo"]["name"] == "ocean"
        tools = client.list_tools()
        assert any(t["name"] == "ocean_turn" for t in tools)
        assert any(t["name"] == "ocean_health" for t in tools)
        assert any(t["name"] == "ocean_set_codegen_backend" for t in tools)
        assert any(t["name"] == "ocean_version" for t in tools)
        pong = client.rpc("ping", {}, timeout=5)
        assert pong == {}
    finally:
        client.stop()


def test_mcp_stdio_ocean_turn_roundtrip(mcp_stdio_cmd: list[str], tmp_path: Path) -> None:
    client = StdioJsonRpcClient(cmd=mcp_stdio_cmd)
    try:
        client.start()
        client.initialize(timeout=10)

        result = client.call_tool(
            "ocean_turn",
            {
                "project_root": str(tmp_path),
                "user_turn": "Run Ocean as MCP outside the codebase for Cursor.",
                "use_advisor": False,
            },
        )
        assert "content" in result
        assert result["structuredContent"]["selected_task"]
        assert result["structuredContent"]["build_context"]
    finally:
        client.stop()


def test_mcp_stdio_ocean_health_and_version(mcp_stdio_cmd: list[str], tmp_path: Path) -> None:
    client = StdioJsonRpcClient(cmd=mcp_stdio_cmd)
    try:
        client.start()
        client.initialize(timeout=10)
        v = client.call_tool("ocean_version", {})
        assert v["structuredContent"]["ocean_version"]
        h = client.call_tool("ocean_health", {"project_root": str(tmp_path)})
        assert "recovery_hints" in h["structuredContent"]
        assert "probe" in h["structuredContent"]
        vb = h["structuredContent"].get("valid_codegen_backends")
        assert isinstance(vb, list) and "codex" in vb
    finally:
        client.stop()


def test_mcp_stdio_rejects_unknown_method(mcp_stdio_cmd: list[str]) -> None:
    client = StdioJsonRpcClient(cmd=mcp_stdio_cmd)
    try:
        client.start()
        client.initialize(timeout=10)
        with pytest.raises(MCPError):
            client.rpc("tools/noSuchThing", {}, timeout=5)
    finally:
        client.stop()
