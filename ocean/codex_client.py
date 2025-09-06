from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict


class CodexResult:
    def __init__(self, ok: bool, mode: str, reason: str = "") -> None:
        self.ok = ok
        self.mode = mode  # subscription | api_fallback | none
        self.reason = reason


def _codex_bin() -> Optional[str]:
    return shutil.which("codex")


def _logged_in() -> bool:
    try:
        # Env token takes precedence
        if os.getenv("CODEX_AUTH_TOKEN"):
            return True
        codex = _codex_bin()
        if codex:
            out = subprocess.run([codex, "auth"], capture_output=True, text=True, timeout=5)
            txt = (out.stdout or out.stderr or "").lower()
            if any(k in txt for k in ("logged in", "authenticated", "already logged")):
                return True
    except Exception:
        pass
    # Fallback marker file
    return (Path.home() / ".codex" / "auth.json").exists()


def ensure_token_env() -> None:
    if os.getenv("CODEX_AUTH_TOKEN"):
        return
    codex = _codex_bin()
    if not codex:
        return
    for args in (["auth", "print-token"], ["auth", "token"], ["auth", "--show-token"], ["auth", "export"]):
        try:
            tok = subprocess.run([codex, *args], capture_output=True, text=True, timeout=5)
            cand = (tok.stdout or tok.stderr or "").strip()
            if cand and len(cand) > 20 and "\n" not in cand:
                os.environ["CODEX_AUTH_TOKEN"] = cand
                break
        except Exception:
            continue


def check() -> CodexResult:
    codex = _codex_bin()
    if not codex:
        if os.getenv("OPENAI_API_KEY"):
            return CodexResult(True, "api_fallback")
        return CodexResult(False, "none", reason="codex not installed")
    # Codex installed; determine auth state
    if _logged_in():
        return CodexResult(True, "subscription")
    if os.getenv("OPENAI_API_KEY"):
        return CodexResult(True, "api_fallback")
    return CodexResult(False, "none", reason="codex not authenticated and no OPENAI_API_KEY")


def exec_json(
    instruction: str,
    suggested_files: Optional[list[str]] = None,
    context_file: Optional[Path] = None,
    timeout: int = 240,
    retries: int = 2,
    model_env: str = "OCEAN_CODEX_MODEL",
    agent: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Run codex exec and return a mapping path->content, with retries.

    Respects subscription vs API fallback dynamically.
    """
    status = check()
    if not status.ok:
        return None

    codex = _codex_bin()
    # Build prompt
    parts: list[str] = []
    if context_file and Path(context_file).exists():
        try:
            ctx = Path(context_file).read_text(encoding="utf-8")
            parts.append("Context begins:\n" + ctx + "\nContext ends.")
        except Exception:
            pass
    parts.append(
        "You are a code generation tool. Return ONLY JSON. No markdown. "
        "Output a JSON object mapping relative file paths to full file contents. "
        "Paths must be strings; contents must be strings."
    )
    if suggested_files:
        parts.append("Suggested files: " + ", ".join(suggested_files))
    parts.append("Instruction: " + instruction)
    prompt = "\n\n".join(parts)

    # Ensure token in env for subprocess
    try:
        ensure_token_env()
    except Exception:
        pass
    env = os.environ.copy()
    if agent:
        env.setdefault("CODEX_RUN_LABEL", f"ocean:{agent}")
    model = env.get(model_env, "o4-mini")

    # Prepare command
    # Minimal compatible command; avoid unsupported flags
    cmd = [
        codex or "codex",
        "exec",
        "--model",
        model,
    ]

    logs_dir = Path("logs"); logs_dir.mkdir(parents=True, exist_ok=True)
    log_file: Optional[Path] = None
    if agent:
        ts = time.strftime("%Y%m%d-%H%M%S")
        log_file = logs_dir / f"codex-{agent.lower()}-{ts}.log"

    backoff = 8
    attempt = 0
    while attempt <= retries:
        attempt += 1
        try:
            proc = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                capture_output=True,
                timeout=timeout,
                env=env,
            )
            stdout = (proc.stdout or b"").decode("utf-8", errors="ignore")
            stderr = (proc.stderr or b"").decode("utf-8", errors="ignore")
            if log_file:
                try:
                    log_file.write_text(
                        f"# Command\n{' '.join(cmd)}\n\n# Instruction\n{instruction}\n\n# STDOUT\n{stdout}\n\n# STDERR\n{stderr}\n",
                        encoding="utf-8",
                    )
                except Exception:
                    pass
            # Try parsing JSON mapping
            try:
                obj = json.loads(stdout)
            except Exception:
                obj = _extract_json(stdout)
            if isinstance(obj, dict):
                # direct mapping path->content
                if all(isinstance(k, str) and isinstance(v, str) for k, v in obj.items()):
                    return obj
                # files key variant
                files = obj.get("files") if isinstance(obj.get("files"), dict) else None  # type: ignore[assignment]
                if isinstance(files, dict):
                    return {str(k): str(v) for k, v in files.items()}
                # content array variant
                content = obj.get("content")
                if isinstance(content, list):
                    out: Dict[str, str] = {}
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "json" and isinstance(item.get("data"), dict):
                            for k, v in item["data"].items():
                                out[str(k)] = str(v)
                    if out:
                        return out
        except subprocess.TimeoutExpired:
            pass
        # Retry with backoff
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)
    return None


def _extract_json(stdout: str) -> Optional[dict]:
    start = stdout.find("{")
    if start == -1:
        return None
    for end in range(len(stdout) - 1, start, -1):
        if stdout[end] == '}':
            chunk = stdout[start : end + 1]
            try:
                return json.loads(chunk)
            except Exception:
                continue
    return None
