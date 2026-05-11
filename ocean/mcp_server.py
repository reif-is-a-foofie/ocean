from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from . import __version__
from .product_loop import (
    bootstrap_doctrine,
    dumps_result,
    format_guidance_for_agent,
    next_action,
    record_feedback,
    turn,
)


PROTOCOL_VERSION = "2024-11-05"


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


TOOLS: dict[str, dict[str, Any]] = {
    "ocean_turn": {
        "description": (
            "Run the Ocean product loop for this agent turn. Optionally records feedback, "
            "then returns the smallest next high-value product task and role instructions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_root": {"type": "string", "description": "Absolute path to the target project root."},
                "user_turn": {"type": "string", "description": "Latest user request or product signal."},
                "feedback": {"type": "string", "description": "Optional Reif feedback to scribe first."},
                "test_results": {"type": "string", "description": "Optional latest test or verification summary."},
                "candidate_tasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional candidate tasks to rank against the doctrine.",
                },
                "use_advisor": {
                    "type": "boolean",
                    "description": "Whether Ocean may call a configured external reasoning CLI advisor.",
                    "default": True,
                },
            },
            "required": ["project_root"],
        },
    },
    "ocean_next_action": {
        "description": "Ask Ocean's Product Manager for the next smallest valuable task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_root": {"type": "string"},
                "user_turn": {"type": "string"},
                "test_results": {"type": "string"},
                "candidate_tasks": {"type": "array", "items": {"type": "string"}},
                "use_advisor": {"type": "boolean", "default": True},
            },
            "required": ["project_root"],
        },
    },
    "ocean_record_feedback": {
        "description": "Capture Reif feedback and update durable project doctrine files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_root": {"type": "string"},
                "feedback": {"type": "string"},
                "source": {"type": "string", "default": "Reif"},
                "test_context": {"type": "string"},
                "update_files": {"type": "boolean", "default": True},
            },
            "required": ["project_root", "feedback"],
        },
    },
    "ocean_bootstrap_doctrine": {
        "description": "Create the Ocean doctrine files in a target repo if they do not exist.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_root": {"type": "string"},
                "vision": {"type": "string"},
                "audience": {"type": "string"},
                "positioning": {"type": "string"},
            },
            "required": ["project_root"],
        },
    },
    "ocean_set_codegen_backend": {
        "description": (
            "Persist codegen backend preference to docs/ocean_prefs.json (for non-TTY hosts e.g. Toad). "
            "Valid values: codex | openai_api | cursor_handoff | dry_plan_only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_root": {"type": "string", "description": "Absolute path to project repo root."},
                "backend": {
                    "type": "string",
                    "description": "One of VALID_BACKENDS; written to codegen_backend.",
                },
            },
            "required": ["backend"],
        },
    },
    "ocean_health": {
        "description": (
            "Structured environment snapshot for auto-heal: codegen backend prefs, Codex/OpenAI probes, "
            "and short recovery_hints agents can act on without scraping stderr."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_root": {
                    "type": "string",
                    "description": "Optional absolute path; defaults to Ocean process cwd for prefs probe.",
                },
            },
        },
    },
    "ocean_version": {
        "description": "Ocean package version and Python runtime for upgrade/compatibility checks.",
        "inputSchema": {"type": "object", "properties": {}},
    },
}


def handle_ocean_turn(args: dict[str, Any]) -> dict[str, Any]:
    return turn(
        args.get("project_root"),
        user_turn=str(args.get("user_turn") or ""),
        feedback=str(args.get("feedback") or ""),
        test_results=str(args.get("test_results") or ""),
        candidate_tasks=list(args.get("candidate_tasks") or []),
        use_advisor=bool(args.get("use_advisor", True)),
    )


def handle_ocean_next_action(args: dict[str, Any]) -> dict[str, Any]:
    guidance = next_action(
        args.get("project_root"),
        user_turn=str(args.get("user_turn") or ""),
        test_results=str(args.get("test_results") or ""),
        candidate_tasks=list(args.get("candidate_tasks") or []),
        use_advisor=bool(args.get("use_advisor", True)),
    )
    result = guidance.to_dict()
    result["mcp_instruction"] = format_guidance_for_agent(guidance)
    return result


def handle_ocean_record_feedback(args: dict[str, Any]) -> dict[str, Any]:
    return record_feedback(
        args.get("project_root"),
        str(args.get("feedback") or ""),
        source=str(args.get("source") or "Reif"),
        test_context=args.get("test_context"),
        update_files=bool(args.get("update_files", True)),
    )


def handle_ocean_bootstrap_doctrine(args: dict[str, Any]) -> dict[str, Any]:
    return bootstrap_doctrine(
        args.get("project_root"),
        vision=args.get("vision"),
        audience=args.get("audience"),
        positioning=args.get("positioning"),
    )


def handle_ocean_health(args: dict[str, Any]) -> dict[str, Any]:
    root_s = args.get("project_root")
    cwd = Path(root_s).resolve() if root_s else Path.cwd()
    from . import backends
    from . import codex_client as cc

    snap = backends.probe_snapshot(cwd)
    backend = backends.get_codegen_backend(cwd)
    codex_st = cc.check()
    hints: list[str] = []
    if backend == "openai_api" and not snap["openai_api_key"]:
        hints.append(
            "Backend is openai_api but OPENAI_API_KEY is unset; export it or set codegen_backend in docs/ocean_prefs.json."
        )
    if backend == "codex" and not snap["codex_cli"]:
        hints.append(
            "Backend is codex but `codex` is not on PATH; install the Codex CLI or switch codegen backend."
        )
    if backend == "codex" and codex_st.ok is False:
        r = (codex_st.reason or "").strip()
        hints.append(
            "Codex check failed"
            + (f": {r}" if r else "")
            + "; run `codex auth login`, set OPENAI_API_KEY for api_fallback, or switch backend."
        )
    if not hints:
        hints.append("No obvious config mismatches; if codegen still fails, run regression (`scripts/regression.sh`) or `ocean codex-test`.")
    return {
        "ocean_version": __version__,
        "project_root": str(cwd),
        "codegen_backend": backend,
        "valid_codegen_backends": sorted(backends.VALID_BACKENDS),
        "prefs": backends.load_prefs(cwd),
        "probe": snap,
        "codex_check_ok": codex_st.ok,
        "codex_mode": codex_st.mode,
        "codex_reason": getattr(codex_st, "reason", "") or "",
        "recovery_hints": hints,
        "mcp_instruction": "Act on recovery_hints first; then retry ocean_turn or bootstrap doctrine as needed.",
    }


def handle_ocean_set_codegen_backend(args: dict[str, Any]) -> dict[str, Any]:
    from . import backends

    raw = str(args.get("backend") or "").strip().lower()
    if raw not in backends.VALID_BACKENDS:
        return {
            "ok": False,
            "error": f"invalid backend: {raw!r}",
            "valid_codegen_backends": sorted(backends.VALID_BACKENDS),
            "mcp_instruction": "Choose a valid backend and call ocean_set_codegen_backend again.",
        }
    root_s = args.get("project_root")
    cwd = Path(root_s).resolve() if root_s else Path.cwd()
    backends.save_prefs({"codegen_backend": raw}, cwd)
    backends.set_codegen_backend_env(raw)
    return {
        "ok": True,
        "project_root": str(cwd),
        "codegen_backend": raw,
        "prefs_file": str(backends.prefs_path(cwd)),
        "mcp_instruction": "For subprocess `ocean chat` without a TTY, export OCEAN_CODEGEN_BACKEND to match.",
    }


def handle_ocean_version(_args: dict[str, Any]) -> dict[str, Any]:
    import sys as _sys

    vi = _sys.version_info
    py_ver = f"{vi.major}.{vi.minor}.{vi.micro}"
    return {
        "ocean_version": __version__,
        "python_version": py_ver,
        "mcp_instruction": f"Ocean {__version__} on Python {py_ver}",
    }


HANDLERS: dict[str, ToolHandler] = {
    "ocean_turn": handle_ocean_turn,
    "ocean_next_action": handle_ocean_next_action,
    "ocean_record_feedback": handle_ocean_record_feedback,
    "ocean_bootstrap_doctrine": handle_ocean_bootstrap_doctrine,
    "ocean_set_codegen_backend": handle_ocean_set_codegen_backend,
    "ocean_health": handle_ocean_health,
    "ocean_version": handle_ocean_version,
}


class MCPServer:
    def __init__(self) -> None:
        self._buffer = b""

    def run(self) -> None:
        while True:
            message = self._read_message()
            if message is None:
                return
            response = self._handle_message(message)
            if response is not None:
                self._write_message(response)

    def _read_message(self) -> dict[str, Any] | None:
        while b"\r\n\r\n" not in self._buffer:
            chunk = sys.stdin.buffer.read(1)
            if not chunk:
                return None
            self._buffer += chunk
        header, rest = self._buffer.split(b"\r\n\r\n", 1)
        length = 0
        for line in header.decode("utf-8", errors="ignore").split("\r\n"):
            if line.lower().startswith("content-length:"):
                length = int(line.split(":", 1)[1].strip())
                break
        if length <= 0:
            raise ValueError("missing Content-Length header")
        while len(rest) < length:
            chunk = sys.stdin.buffer.read(length - len(rest))
            if not chunk:
                return None
            rest += chunk
        body, self._buffer = rest[:length], rest[length:]
        return json.loads(body.decode("utf-8"))

    def _write_message(self, message: dict[str, Any]) -> None:
        body = json.dumps(message, separators=(",", ":")).encode("utf-8")
        sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
        sys.stdout.buffer.write(body)
        sys.stdout.buffer.flush()

    def _handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        msg_id = message.get("id")
        try:
            if method in {"initialize", "server/initialize"}:
                return self._response(msg_id, self._initialize_result())
            if method == "tools/list":
                return self._response(msg_id, {"tools": self._tool_list()})
            if method == "tools/call":
                return self._response(msg_id, self._call_tool(message.get("params") or {}))
            if method in {"initialized", "notifications/initialized"}:
                return None
            if method == "ping":
                return self._response(msg_id, {})
            if msg_id is None:
                return None
            return self._error(msg_id, -32601, f"method not found: {method}")
        except Exception as exc:
            if msg_id is None:
                return None
            return self._error(msg_id, -32000, str(exc))

    def _initialize_result(self) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "ocean", "version": __version__},
        }

    def _tool_list(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
            for name, spec in TOOLS.items()
        ]

    def _call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in HANDLERS:
            raise ValueError(f"unknown tool: {name}")
        result = HANDLERS[name](args)
        text = result.get("mcp_instruction") if isinstance(result, dict) else None
        if not text:
            text = dumps_result(result)
        return {
            "content": [{"type": "text", "text": str(text)}],
            "structuredContent": result,
        }

    @staticmethod
    def _response(msg_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def main() -> None:
    # Resolve cwd early so relative project_root values behave predictably when
    # clients launch Ocean from a target repo.
    Path.cwd()
    MCPServer().run()


if __name__ == "__main__":
    main()
