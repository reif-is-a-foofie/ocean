from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple
from .feed import feed as _feed
import httpx


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
        # Explicit env hints first
        if os.getenv("OCEAN_CODEX_AUTH") in ("1", "true", "True"):
            return True
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
        try:
            _feed("🌊 Ocean: ❌ Codex CLI not found on PATH. Install 'codex' and retry.")
        except Exception:
            pass
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
        # Defer to API fallback below (do not attempt CLI in this mode)
    else:
        _last_mode = "unavailable"
        if force:
            raise CodexUnavailable("Codex exec returned no JSON mapping")
        try:
            _feed("🌊 Ocean: ❌ Codex not authenticated and no OPENAI_API_KEY present. Run 'codex auth login' or export OPENAI_API_KEY.")
        except Exception:
            pass
        return None

    # If in subscription mode, attempt CLI exec first; else skip to API fallback
    if _last_mode == "subscription":
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
                # Prefer --prompt flag when supported to avoid stdin hangups
                use_prompt_flag = os.getenv("OCEAN_CODEX_USE_STDIN") not in ("1", "true", "True")
                if use_prompt_flag:
                    proc = subprocess.run(
                        [*cmd, "--prompt", full_prompt],
                        capture_output=True,
                        text=True,
                        timeout=int(os.getenv("OCEAN_CODEX_TIMEOUT", str(timeout))),
                        env=env,
                    )
                    stdout = (proc.stdout or "")
                    stderr = (proc.stderr or "")
                    # Fallback to stdin if flag unsupported
                    if proc.returncode != 0 and "unexpected argument '--prompt'" in (stderr or ""):
                        raise RuntimeError("codex --prompt unsupported; fallback to stdin")
                else:
                    proc = subprocess.run(
                        cmd,
                        input=full_prompt,
                        capture_output=True,
                        text=True,
                        timeout=int(os.getenv("OCEAN_CODEX_TIMEOUT", str(timeout))),
                        env=env,
                    )
                    stdout = (proc.stdout or "")
                    stderr = (proc.stderr or "")
                if stdout.strip():
                    break
            except Exception as e:
                if attempts >= 2:
                    if log_file:
                        try:
                            log_file.write_text(f"ERROR: {e}\n", encoding="utf-8")
                        except Exception:
                            pass
                    _feed(f"🌊 Ocean: Codex exec error (agent={agent or 'Ocean'}): {e}")
                    stdout = ""; stderr = str(e)
                    break
            # Backoff
            try:
                import time as _t
                _t.sleep(6 * attempts)
            except Exception:
                pass

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
        if isinstance(obj, dict):
            # Interpret common shapes below
            pass
        else:
            # Fall through to API fallback if available
            if env.get("OPENAI_API_KEY"):
                _last_mode = "api_fallback"
            else:
                # Emit concise logs to feed for diagnosis
                try:
                    mode = _last_mode
                    model = os.getenv("OCEAN_CODEX_MODEL", "o4-mini")
                    _feed(f"🌊 Ocean: Codex exec returned no JSON (agent={agent or 'Ocean'}, mode={mode}, model={model}).")
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

    # If we are in API fallback, call OpenAI API directly using httpx
    if _last_mode == "api_fallback" and env.get("OPENAI_API_KEY"):
        try:
            _feed("🌊 Ocean: Using OpenAI API fallback for codegen.")
        except Exception:
            pass
        api_model = os.getenv("OCEAN_OPENAI_MODEL") or os.getenv("OCEAN_CODEX_MODEL", "gpt-4o-mini")
        # Map common Codex shorthands to OpenAI models
        if api_model.startswith("o4"):
            api_model = "gpt-4o-mini"
        headers = {
            "Authorization": f"Bearer {env['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": "You are a code generation tool. Return ONLY JSON: a mapping of file paths to full file contents."},
            {"role": "user", "content": full_prompt},
        ]
        body = {"model": api_model, "messages": messages, "temperature": 0}
        try:
            resp = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=timeout)
            data = resp.json()
            content = (((data.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
            try:
                obj = json.loads(content)
            except Exception:
                obj = _extract_json(content)
            if not isinstance(obj, dict):
                # Emit a head for debugging
                try:
                    _feed("🌊 Ocean: API fallback returned no JSON mapping.")
                except Exception:
                    pass
                return None
        except Exception as e:
            try:
                _feed(f"🌊 Ocean: OpenAI API fallback error: {e}")
            except Exception:
                pass
            return None
    
    # By here, obj should be parsed from either CLI or API fallback
    if not isinstance(obj, dict):
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
