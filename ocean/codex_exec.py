from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple


def _codex_bin() -> Optional[str]:
    return shutil.which("codex")


def available() -> bool:
    return _codex_bin() is not None


_last_mode: str = "unknown"  # subscription | api_fallback | unavailable


def last_mode() -> str:
    return _last_mode


def _extract_json(stdout: str) -> Optional[dict]:
    # Try to find the first balanced JSON object in output
    # Heuristic: find first '{' and last '}' and attempt to parse progressively
    start = stdout.find("{")
    if start == -1:
        return None
    # try multiple trailing positions from end downwards
    for end in range(len(stdout) - 1, start, -1):
        if stdout[end] == '}':
            chunk = stdout[start : end + 1]
            try:
                return json.loads(chunk)
            except Exception:
                continue
    return None


def _logged_in_via_codex() -> bool:
    home = os.path.expanduser("~")
    auth = Path(home) / ".codex" / "auth.json"
    return auth.exists()


def generate_files(
    instruction: str,
    suggested_files: Optional[list[str]] = None,
    context_file: Optional[Path] = None,
    timeout: int = 120,
) -> Optional[Dict[str, str]]:
    """Use `codex exec` to generate files.

    The prompt asks for a strict JSON mapping of path->content. We attempt to
    parse various shapes from stdout and coerce to a mapping.
    """
    if not available():
        return None

    prompt_parts: list[str] = []
    if context_file and context_file.exists():
        try:
            ctx = context_file.read_text(encoding="utf-8")
            prompt_parts.append("Context begins:\n" + ctx + "\nContext ends.")
        except Exception:
            pass

    prompt_parts.append(
        (
            "You are a code generation tool. "
            "Return ONLY JSON. No markdown. No commentary. "
            "Output a JSON object mapping relative file paths to full file contents. "
            "Paths must be strings; contents must be strings."
        )
    )
    if suggested_files:
        prompt_parts.append("Suggested files: " + ", ".join(suggested_files))

    prompt_parts.append("Instruction: " + instruction)
    full_prompt = "\n\n".join(prompt_parts)

    cmd = [
        _codex_bin() or "codex",
        "exec",
        "-m",
        os.getenv("OCEAN_CODEX_MODEL", "o3"),
        "--ask-for-approval",
        os.getenv("OCEAN_CODEX_APPROVAL", "never"),
        "--sandbox",
        os.getenv("OCEAN_CODEX_SANDBOX", "read-only"),
    ]

    # Auth policy: prefer Codex login (subscription). Use OPENAI_API_KEY only as fallback, loudly.
    env = os.environ.copy()
    global _last_mode
    if _logged_in_via_codex():
        # Ensure API key does not override subscription auth
        env.pop("OPENAI_API_KEY", None)
        _last_mode = "subscription"
    elif env.get("OPENAI_API_KEY"):
        _last_mode = "api_fallback"
        print("\n[bold yellow]⚠️ OCEAN: Using OpenAI API key FALLBACK for Codex exec. This may incur usage outside your subscription.[/bold yellow]")
        print("[bold yellow]Set OCEAN_DISALLOW_API_FALLBACK=1 to block this behavior.[/bold yellow]\n")
        if env.get("OCEAN_DISALLOW_API_FALLBACK") in ("1", "true", "True"):
            return None
    else:
        _last_mode = "unavailable"
        return None

    try:
        proc = subprocess.run(
            cmd,
            input=full_prompt.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except Exception:
        return None

    stdout = (proc.stdout or b"").decode("utf-8", errors="ignore")
    stderr = (proc.stderr or b"").decode("utf-8", errors="ignore")

    # Try to parse as JSON directly
    obj = None
    try:
        obj = json.loads(stdout)
    except Exception:
        obj = _extract_json(stdout)
    if not isinstance(obj, dict):
        return None

    # Interpret common shapes
    # 1) direct mapping
    if all(isinstance(k, str) and isinstance(v, str) for k, v in obj.items()):
        return obj  # type: ignore[return-value]

    # 2) { files: { path: content } }
    files = obj.get("files") if isinstance(obj.get("files"), dict) else None  # type: ignore[assignment]
    if isinstance(files, dict):
        out = {str(k): str(v) for k, v in files.items()}
        if out:
            return out

    # 3) { content: [ {type: 'json', data: {path: content}} ] }
    content = obj.get("content")
    if isinstance(content, list):
        out: Dict[str, str] = {}
        for item in content:
            if isinstance(item, dict) and item.get("type") == "json" and isinstance(item.get("data"), dict):
                for k, v in item["data"].items():
                    out[str(k)] = str(v)
        if out:
            return out

    return None
