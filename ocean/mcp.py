from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional
import shutil


@dataclass
class MCPInstance:
    agent: str
    started_at: str
    log_file: Path
    provider: str = "stub"
    client_log: Optional[Path] = None


class MCP:
    """Lightweight Codex MCP orchestration (stub, multi-instance).

    - ensure_started(): initialize global MCP layer.
    - start_for_agent(): start a per-agent MCP instance (stubbed) and log it.
    - status()/status_for_agent(): return dict status for UI/CLI.
    """

    _instances: Dict[str, MCPInstance] = {}

    @staticmethod
    def _mcp_only() -> bool:
        return os.getenv("OCEAN_MCP_ONLY", "1") not in ("0", "false", "False")

    @staticmethod
    def ensure_started(log_path: Path | None = None) -> None:
        enabled = os.getenv("OCEAN_MCP_ENABLED", "1") not in ("0", "false", "False")
        status_line = f"[MCP] Codex MCP {'enabled' if enabled else 'disabled'} at {datetime.now().isoformat()}"
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(status_line + "\n")
        print("🔌 Codex MCP: initialized (stub)" if enabled else "⚠️ Codex MCP: disabled via OCEAN_MCP_ENABLED")

    @staticmethod
    def start_for_agent(agent: str, logs_dir: Path) -> MCPInstance:
        enabled = os.getenv("OCEAN_MCP_ENABLED", "1") not in ("0", "false", "False")
        provider = os.getenv("OCEAN_MCP_PROVIDER") or ("codex-cli" if shutil.which("codex") else "stub")
        logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = logs_dir / f"mcp-{agent.lower()}-{ts}.log"
        line = f"[MCP] start agent={agent} provider={provider} ts={datetime.now().isoformat()} enabled={enabled}"
        log_file.write_text(line + "\n", encoding="utf-8")
        inst = MCPInstance(agent=agent, started_at=datetime.now().isoformat(), log_file=log_file, provider=provider)
        MCP._instances[agent] = inst
        print(f"🔌 [MCP] Started instance for {agent} ({provider})")
        return inst

    @staticmethod
    def get_client(agent: str):
        """Return a started stdio client if provider is codex-cli, else None."""
        from .mcp_client import StdioJsonRpcClient

        inst = MCP._instances.get(agent)
        if not inst:
            return None
        if inst.provider != "codex-cli":
            return None
        if inst.client_log is None:
            inst.client_log = inst.log_file.parent / (inst.log_file.stem + "-rpc.log")

        # Candidates: env override or common variants
        cmd_env = os.getenv("OCEAN_MCP_CMD")
        candidates: list[list[str]]
        if cmd_env:
            candidates = [shlex.split(c.strip()) for c in cmd_env.split("||") if c.strip()]
        else:
            candidates = [
                ["codex", "mcp"],
                ["codex", "mcp", "--stdio"],
            ]

        last_err = None
        for cmd in candidates:
            client = StdioJsonRpcClient(cmd=cmd, cwd=None, log=inst.client_log)
            try:
                client.start()
                client.initialize()
                # Persist chosen cmd for status visibility
                inst.cmd = " ".join(cmd)
                return client
            except Exception as e:  # pragma: no cover - depends on external binary
                last_err = e
                with inst.log_file.open("a", encoding="utf-8") as f:
                    f.write(f"[MCP] client init failed with cmd={' '.join(cmd)}: {e}\n")
                continue
        # All candidates failed
        with inst.log_file.open("a", encoding="utf-8") as f:
            f.write(f"[MCP] all client init attempts failed: {last_err}\n")
        return None

    @staticmethod
    def status() -> dict:
        enabled = os.getenv("OCEAN_MCP_ENABLED", "1") not in ("0", "false", "False")
        provider = os.getenv("OCEAN_MCP_PROVIDER") or ("codex-cli" if shutil.which("codex") else "stub")
        return {
            "enabled": enabled,
            "env": {
                "OCEAN_MCP_ENABLED": os.getenv("OCEAN_MCP_ENABLED", "1"),
                "OCEAN_MCP_PROVIDER": os.getenv("OCEAN_MCP_PROVIDER", provider),
            },
            "provider": provider,
            "instances": {k: {"agent": v.agent, "started_at": v.started_at, "log_file": str(v.log_file)} for k, v in MCP._instances.items()},
        }

    @staticmethod
    def status_for_agent(agent: str) -> Optional[dict]:
        inst = MCP._instances.get(agent)
        if not inst:
            return None
        return {"agent": inst.agent, "started_at": inst.started_at, "log_file": str(inst.log_file), "provider": inst.provider}

    # Convenience helpers (best-effort; rely on tool discovery and fall back safely)
    @staticmethod
    def _select_tool(tools: list[dict], keywords: list[str]) -> Optional[str]:
        def score(t: dict) -> int:
            name = (t.get("name") or "").lower()
            desc = (t.get("description") or "").lower()
            s = 0
            for kw in keywords:
                if kw in name:
                    s += 2
                if kw in desc:
                    s += 1
            return s
        ranked = sorted(tools, key=score, reverse=True)
        if not ranked:
            return None
        if score(ranked[0]) <= 0:
            return None
        return ranked[0].get("name")

    @staticmethod
    def codegen_files(agent: str, prompt: str, suggestions: Optional[list[str]] = None) -> Optional[dict[str, str]]:
        """Ask Codex MCP to generate files for a prompt.

        Returns a mapping path->content if available; otherwise None.
        """
        client = MCP.get_client(agent)
        if not client:
            if MCP._mcp_only():
                raise MCPError("MCP-only mode: Codex MCP client unavailable. Ensure 'brew install codex' and 'codex auth login'.")
            return None
        try:
            tools = client.list_tools()
            # Allow explicit override
            override = os.getenv("OCEAN_MCP_TOOL_CODEGEN")
            tool_name = override or MCP._select_tool(tools, ["code", "generate", "doc", "scaffold", "file"])
            if not tool_name:
                # Log available tools for debugging
                with open(client._log or (Path("logs")/"mcp-debug.log"), "ab") as f:  # type: ignore[attr-defined]
                    f.write(f"[debug] no codegen tool; tools={tools}\n".encode("utf-8"))
                if MCP._mcp_only():
                    raise MCPError("MCP-only mode: No suitable codegen tool discovered.")
                return None
            args = {"prompt": prompt}
            if suggestions:
                args["suggested_files"] = suggestions
            res = client.call_tool(tool_name, args)
            # Attempt to interpret common shapes
            if isinstance(res, dict):
                if "files" in res and isinstance(res["files"], dict):
                    return {str(k): str(v) for k, v in res["files"].items()}
                if "path" in res and "content" in res:
                    return {str(res["path"]): str(res["content"]) }
            if isinstance(res, list):
                out: dict[str, str] = {}
                for item in res:
                    if isinstance(item, dict) and "path" in item and "content" in item:
                        out[str(item["path"])] = str(item["content"])
                return out or None
        except Exception as e:
            # Respect MCP-only mode: if set, do not fallback silently
            if MCP._mcp_only():
                raise
            return None
        return None

    @staticmethod
    def write_file(agent: str, path: Path, content: str) -> bool:
        """Try to write via MCP write tool; fall back to local write on failure."""
        client = MCP.get_client(agent)
        if client:
            try:
                tools = client.list_tools()
                tool_name = MCP._select_tool(tools, ["write", "file", "save"])
                if tool_name:
                    client.call_tool(tool_name, {"path": str(path), "content": content})
                    return True
            except Exception:
                pass
        # Fallback: local write (only if not MCP-only)
        if MCP._mcp_only():
            raise MCPError("MCP-only mode: write_file fallback disabled.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return True

    @staticmethod
    def shell_run(agent: str, command: str) -> Optional[dict]:
        """Call a shell/run tool if exposed by Codex MCP; returns result dict or None.

        In MCP-only mode, if no shell tool is available, raises.
        """
        client = MCP.get_client(agent)
        if not client:
            if MCP._mcp_only():
                raise MCPError("MCP-only mode: shell client unavailable")
            return None
        try:
            tools = client.list_tools()
            override = os.getenv("OCEAN_MCP_TOOL_SHELL")
            tool_name = override or MCP._select_tool(tools, ["shell", "run", "exec", "command"])
            if not tool_name:
                if MCP._mcp_only():
                    raise MCPError("MCP-only mode: No shell tool discovered")
                return None
            res = client.call_tool(tool_name, {"command": command})
            if isinstance(res, dict):
                return res
            return {"result": res}
        except Exception as e:
            if MCP._mcp_only():
                raise
            return None
