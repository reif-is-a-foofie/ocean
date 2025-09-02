from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime


class MCP:
    """Lightweight Codex MCP bootstrapper (stub).

    - Writes a log line indicating MCP startup.
    - In the future, can spawn/connect to a real MCP server.
    """

    @staticmethod
    def ensure_started(log_path: Path | None = None) -> None:
        # Feature gate via env var (defaults to on)
        enabled = os.getenv("OCEAN_MCP_ENABLED", "1") not in ("0", "false", "False")
        status_line = f"[MCP] Codex MCP {'enabled' if enabled else 'disabled'} at " \
                      f"{datetime.now().isoformat()}"

        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(status_line + "\n")

        # For now, just print a confirmation. Hook real startup here later.
        if enabled:
            print("🔌 Codex MCP: initialized (stub)")
        else:
            print("⚠️ Codex MCP: disabled via OCEAN_MCP_ENABLED")

