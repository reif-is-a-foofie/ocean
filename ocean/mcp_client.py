from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Queue, Empty
from typing import Any, Dict, Optional


def _default_cmd() -> list[str]:
    cmd = os.getenv("OCEAN_MCP_CMD") or "codex mcp"
    return shlex.split(cmd)


@dataclass
class MCPError(Exception):
    message: str


class StdioJsonRpcClient:
    """Minimal JSON-RPC client over stdio with Content-Length framing (MCP-compatible)."""

    def __init__(self, cmd: Optional[list[str]] = None, cwd: Optional[Path] = None, log: Optional[Path] = None):
        self.cmd = cmd or _default_cmd()
        self.cwd = str(cwd) if cwd else None
        self.proc: Optional[subprocess.Popen] = None
        self._id = 0
        self._lock = threading.Lock()
        self._in_q: Queue[bytes] = Queue()
        self._log = log

    def start(self, env: Optional[dict[str, str]] = None) -> None:
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env=(os.environ | env) if env else None,
        )

        # Reader thread for stdout
        def _reader():
            assert self.proc and self.proc.stdout
            buf = b""
            while True:
                chunk = self.proc.stdout.read(1)
                if not chunk:
                    break
                buf += chunk
                # Try to parse frames as they arrive
                while True:
                    msg, rest = self._try_parse_frame(buf)
                    if msg is None:
                        break
                    buf = rest
                    self._in_q.put(msg)

        t = threading.Thread(target=_reader, daemon=True)
        t.start()

    def _log_io(self, direction: str, payload: bytes) -> None:
        if not self._log:
            return
        self._log.parent.mkdir(parents=True, exist_ok=True)
        with self._log.open("ab") as f:
            f.write(f"[{direction}] ".encode("utf-8") + payload + b"\n")

    @staticmethod
    def _frame(body: bytes) -> bytes:
        headers = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
        return headers + body

    @staticmethod
    def _try_parse_frame(buf: bytes) -> tuple[Optional[bytes], bytes]:
        try:
            header_end = buf.index(b"\r\n\r\n")
        except ValueError:
            return None, buf
        header = buf[:header_end].decode("utf-8", errors="ignore")
        length = 0
        for line in header.split("\r\n"):
            if line.lower().startswith("content-length:"):
                try:
                    length = int(line.split(":", 1)[1].strip())
                except Exception:
                    pass
        rest = buf[header_end + 4 :]
        if len(rest) < length:
            return None, buf
        body = rest[:length]
        remaining = rest[length:]
        return body, remaining

    def rpc(self, method: str, params: Optional[dict[str, Any]] = None, timeout: float = 10.0) -> Any:
        if not self.proc or not self.proc.stdin:
            raise MCPError("process not started")
        with self._lock:
            self._id += 1
            msg = {
                "jsonrpc": "2.0",
                "id": self._id,
                "method": method,
                "params": params or {},
            }
            body = json.dumps(msg).encode("utf-8")
            framed = self._frame(body)
            self._log_io("out", body)
            self.proc.stdin.write(framed)
            self.proc.stdin.flush()

        # Wait for a matching response (simple sequential client)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                payload = self._in_q.get(timeout=0.1)
            except Empty:
                continue
            self._log_io("in", payload)
            try:
                resp = json.loads(payload.decode("utf-8"))
            except Exception as e:
                raise MCPError(f"invalid JSON response: {e}")
            if resp.get("id") != self._id:
                # Not our response; ignore (single-flight, unlikely)
                continue
            if "error" in resp:
                raise MCPError(str(resp["error"]))
            return resp.get("result")
        raise MCPError(f"timeout waiting for response to {method}")

    # Convenience wrappers
    def initialize(self) -> Any:
        params = {
            "clientInfo": {"name": "ocean", "version": "0.1.0"},
            "protocolVersion": "2024-10-07",
        }
        return self.rpc("initialize", params=params, timeout=15.0)

    def list_tools(self) -> list[dict[str, Any]]:
        res = self.rpc("tools/list", params={})
        return list(res.get("tools", []))

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        return self.rpc("tools/call", params={"name": name, "arguments": arguments}, timeout=30.0)

