from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple
from .feed import feed as _feed


class CodexUnavailable(Exception):
    pass


def _codex_bin() -> Optional[str]:
    return shutil.which("codex")


def available() -> bool:
    if os.getenv("OCEAN_DISABLE_CODEX") in ("1", "true", "True"):
        return False
    return _codex_bin() is not None


_last_mode: str = "unknown"  # subscription | api_fallback | unavailable


def last_mode() -> str:
    return _last_mode


def _ensure_token_env() -> None:
    """Populate CODEX_AUTH_TOKEN in the environment if possible.

    Tries a few codex subcommands to surface a token and caches it in env.
    """
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
    """Best-effort detection of Codex auth.

    Heuristics, in order:
    - Explicit token in env (CODEX_AUTH_TOKEN)
    - "codex auth" output contains "logged in"/"authenticated"
    - Able to obtain a token via one of: print-token, token, --show-token, export
    - Legacy file at ~/.codex/auth.json exists
    """
    try:
        if os.getenv("CODEX_AUTH_TOKEN"):
            return True
        codex = shutil.which("codex")
        if codex:
            out = subprocess.run([codex, "auth"], capture_output=True, text=True, timeout=5)
            txt = (out.stdout or out.stderr or "").lower()
            if any(kw in txt for kw in ("logged in", "authenticated", "already logged")):
                return True
            # Try to surface a token and cache in env
            for args in (["auth", "print-token"], ["auth", "token"], ["auth", "--show-token"], ["auth", "export"]):
                try:
                    tok = subprocess.run([codex, *args], capture_output=True, text=True, timeout=5)
                    cand = (tok.stdout or tok.stderr or "").strip()
                    if cand and len(cand) > 20 and "\n" not in cand:
                        os.environ["CODEX_AUTH_TOKEN"] = cand
                        return True
                except Exception:
                    continue
    except Exception:
        pass
    home = os.path.expanduser("~")
    auth = Path(home) / ".codex" / "auth.json"
    return auth.exists()


def generate_files(
    instruction: str,
    suggested_files: Optional[list[str]] = None,
    context_file: Optional[Path] = None,
    timeout: int = 240,
    agent: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Use `codex exec` to generate files.

    The prompt asks for a strict JSON mapping of path->content. We attempt to
    parse various shapes from stdout and coerce to a mapping.
    """
    force = os.getenv("OCEAN_FORCE_CODEX") in ("1", "true", "True")
    # Best-effort ensure token is present for subprocesses
    try:
        _ensure_token_env()
    except Exception:
        pass
    if not available():
        if force:
            raise CodexUnavailable("Codex CLI not available")
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

    # Build minimal, compatible codex exec command. Avoid unsupported flags.
    cmd = [
        _codex_bin() or "codex",
        "exec",
        "--model",
        os.getenv("OCEAN_CODEX_MODEL", "o4-mini"),
    ]

    # Auth policy: prefer Codex login (subscription). Use OPENAI_API_KEY only as fallback, loudly.
    env = os.environ.copy()
    if agent:
        env["OCEAN_AGENT"] = agent
        # Provide a hint label for Codex if supported (harmless otherwise)
        env.setdefault("CODEX_RUN_LABEL", f"ocean:{agent}")
    global _last_mode
    if _logged_in_via_codex():
        # Ensure API key does not override subscription auth
        env.pop("OPENAI_API_KEY", None)
        _last_mode = "subscription"
    elif env.get("OPENAI_API_KEY"):
        _last_mode = "api_fallback"
        try:
            _feed("🌊 Ocean: ⚠️ Using OpenAI API key FALLBACK for Codex exec. This may bill outside your subscription.")
            _feed("🌊 Ocean: Set OCEAN_DISALLOW_API_FALLBACK=1 to block this fallback.")
        except Exception:
            pass
        if env.get("OCEAN_DISALLOW_API_FALLBACK") in ("1", "true", "True"):
            return None
    else:
        _last_mode = "unavailable"
        if force:
            raise CodexUnavailable("Codex exec returned no JSON mapping")
        return None

    logs_dir = Path("logs"); logs_dir.mkdir(parents=True, exist_ok=True)
    log_file: Optional[Path] = None
    if agent:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = logs_dir / f"codex-{agent.lower()}-{ts}.log"
    # Add a simple retry with backoff for transient failures
    attempts = 0
    stdout = stderr = ""
    while attempts < 2:
        attempts += 1
        try:
            proc = subprocess.run(
                cmd,
                input=full_prompt.encode("utf-8"),
                capture_output=True,
                timeout=timeout,
                env=env,
            )
            stdout = (proc.stdout or b"").decode("utf-8", errors="ignore")
            stderr = (proc.stderr or b"").decode("utf-8", errors="ignore")
            if stdout.strip():
                break
        except Exception as e:
            if attempts >= 2:
                if log_file:
                    try:
                        log_file.write_text(f"ERROR: {e}\n", encoding="utf-8")
                    except Exception:
                        pass
                # Emit to feed as well
                _feed(f"🌊 Ocean: Codex exec error (agent={agent or 'Ocean'}): {e}")
                return None
        # Backoff
        try:
            import time as _t
            _t.sleep(6 * attempts)
        except Exception:
            pass

    # Persist raw outputs to per-agent log for debugging/traceability
    if log_file:
        try:
            log_file.write_text(
                """# Codex Exec Log\n\n## Command\n{cmd}\n\n## Instruction\n{instr}\n\n## STDOUT\n{out}\n\n## STDERR\n{err}\n""".format(
                    cmd=" ".join(cmd), instr=instruction, out=stdout, err=stderr
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    # Try to parse as JSON directly
    obj = None
    try:
        obj = json.loads(stdout)
    except Exception:
        obj = _extract_json(stdout)
    if not isinstance(obj, dict):
        # Emit concise logs to feed for diagnosis
        try:
            mode = _last_mode
            model = os.getenv("OCEAN_CODEX_MODEL", "o4-mini")
            sandbox = os.getenv("OCEAN_CODEX_SANDBOX", "read-only")
            approval = os.getenv("OCEAN_CODEX_APPROVAL", "never")
            _feed(f"🌊 Ocean: Codex exec returned no JSON (agent={agent or 'Ocean'}, mode={mode}, model={model}, sandbox={sandbox}, approval={approval}).")
            def _head(text: str, n: int = 6) -> str:
                lines = (text or "").splitlines()
                return " | ".join(l.strip() for l in lines[:n] if l.strip())
            if stderr.strip():
                _feed(f"🌊 Ocean: Codex stderr: {_head(stderr)}")
            if stdout.strip():
                _feed(f"🌊 Ocean: Codex stdout: {_head(stdout)}")
        except Exception:
            pass
        return None

    # Interpret common shapes
    # 1) direct mapping
    if all(isinstance(k, str) and isinstance(v, str) for k, v in obj.items()):
        try:
            _feed(f"🌊 Ocean: Codex exec OK (files={len(obj)})")
        except Exception:
            pass
        return obj  # type: ignore[return-value]

    # 2) { files: { path: content } }
    files = obj.get("files") if isinstance(obj.get("files"), dict) else None  # type: ignore[assignment]
    if isinstance(files, dict):
        out = {str(k): str(v) for k, v in files.items()}
        if out:
            try:
                _feed(f"🌊 Ocean: Codex exec OK (files={len(out)})")
            except Exception:
                pass
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
            try:
                _feed(f"🌊 Ocean: Codex exec OK (files={len(out)})")
            except Exception:
                pass
            return out

    return None
