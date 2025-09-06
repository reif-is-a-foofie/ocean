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
        # Explicit env flags
        if os.getenv("OCEAN_CODEX_AUTH") in ("1", "true", "True"):
            return True
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
    # Prepare command — advanced controls
    use_search = os.getenv("OCEAN_CODEX_SEARCH") not in ("0", "false", "False")
    bypass = os.getenv("OCEAN_CODEX_BYPASS_SANDBOX") in ("1", "true", "True")
    sandbox = os.getenv("OCEAN_CODEX_SANDBOX")
    approval = os.getenv("OCEAN_CODEX_APPROVAL")
    profile = os.getenv("OCEAN_CODEX_PROFILE")
    want_cd = os.getenv("OCEAN_CODEX_CD", "1") not in ("0", "false", "False")
    skip_git = False
    try:
        chk = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
        if chk.returncode != 0:
            skip_git = True
    except Exception:
        skip_git = True
    cmd = [codex or "codex"]
    if use_search:
        cmd.append("--search")
    if profile:
        cmd += ["--profile", profile]
    if want_cd:
        cmd += ["--cd", str(Path.cwd())]
    if skip_git:
        cmd.append("--skip-git-repo-check")
    cmd.append("exec")
    if bypass:
        cmd.append("--dangerously-bypass-approvals-and-sandbox")
    else:
        sb = sandbox if sandbox in ("read-only", "workspace-write", "danger-full-access") else "workspace-write"
        cmd += ["--sandbox", sb]
        if approval in ("untrusted", "on-failure", "on-request", "never"):
            cmd += ["--ask-for-approval", approval]
    # Supply prompt positionally
    cmd.append(prompt)

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
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
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
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
