from __future__ import annotations
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional


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
        # MCP removed; never enforce MCP-only behavior
        return False

    @staticmethod
    def ensure_started(log_path: Path | None = None) -> None:
        # No-op; MCP disabled
        return None

    @staticmethod
    def start_for_agent(agent: str, logs_dir: Path) -> MCPInstance:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"mcp-{agent.lower()}.log"
        log_file.write_text("MCP disabled\n", encoding="utf-8")
        inst = MCPInstance(agent=agent, started_at=datetime.now().isoformat(), log_file=log_file, provider="stub")
        MCP._instances[agent] = inst
        return inst

    @staticmethod
    def get_client(agent: str):
        # Removed: always return None
        return None

    @staticmethod
    def status() -> dict:
        return {"enabled": False, "provider": "stub", "env": {}, "instances": {}}

    @staticmethod
    def status_for_agent(agent: str) -> Optional[dict]:
        inst = MCP._instances.get(agent)
        if not inst:
            return None
        return {
            "agent": inst.agent,
            "started_at": inst.started_at,
            "log_file": str(inst.log_file),
            "provider": inst.provider,
            "cmd": getattr(inst, "cmd", None),
        }

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
        return None

    @staticmethod
    def write_file(agent: str, path: Path, content: str) -> bool:
        """Try to write via MCP write tool; fall back to local write on failure."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True

    @staticmethod
    def shell_run(agent: str, command: str) -> Optional[dict]:
        """Call a shell/run tool if exposed by Codex MCP; returns result dict or None.

        In MCP-only mode, if no shell tool is available, raises.
        """
        return None
