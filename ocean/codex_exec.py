from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict
from .feed import feed as _feed
import httpx
import base64
import datetime as _dt


class CodexUnavailable(Exception):
    pass


def _codex_bin() -> Optional[str]:
    return shutil.which("codex")


def available() -> bool:
    if os.getenv("OCEAN_DISABLE_CODEX") in ("1", "true", "True"):
        return False
    return _codex_bin() is not None


_last_mode: str = "unknown"  # subscription | api_fallback | unavailable
_announced: bool = False
_last_error_detail: str = ""


def last_mode() -> str:
    return _last_mode


def last_error() -> str:
    return _last_error_detail


def _ensure_token_env() -> None:
    """Populate CODEX_AUTH_TOKEN in the environment if possible.

    Tries a few codex subcommands to surface a token and caches it in env.
    """
    if os.getenv("CODEX_AUTH_TOKEN"):
        return
    codex = _codex_bin()
    if not codex:
        return
    # Helper: decode JWT exp without verifying signature
    def _jwt_info(tok: str) -> dict:
        info = {"exp": None, "iat": None, "exp_iso": None, "expired": None}
        try:
            parts = tok.split(".")
            if len(parts) >= 2:
                pad = '=' * (-len(parts[1]) % 4)
                payload = base64.urlsafe_b64decode(parts[1] + pad)
                data = json.loads(payload.decode("utf-8", errors="ignore"))
                exp = data.get("exp")
                iat = data.get("iat")
                info["exp"] = exp
                info["iat"] = iat
                if isinstance(exp, (int, float)):
                    dt = _dt.datetime.fromtimestamp(exp)
                    info["exp_iso"] = dt.isoformat(sep=" ")
                    info["expired"] = dt < _dt.datetime.now()
        except Exception:
            pass
        return info

    # First, try ~/.codex/auth.json
    try:
        auth_json = Path.home() / ".codex" / "auth.json"
        if auth_json.exists():
            data = json.loads(auth_json.read_text(encoding="utf-8"))
            tok = (data.get("id_token") or "").strip()
            if tok:
                os.environ["CODEX_AUTH_TOKEN"] = tok
                os.environ["OCEAN_CODEX_AUTH"] = "1"
                os.environ["OCEAN_CODEX_TOKEN_SOURCE"] = str(auth_json)
                info = _jwt_info(tok)
                try:
                    exp_s = info.get("exp_iso") or "unknown"
                    expired = info.get("expired")
                    note = f"exp={exp_s}{' (expired)' if expired else ''}"
                    _feed(f"🌊 Ocean: Found Codex token in {auth_json} (masked, {note}).")
                except Exception:
                    pass
                return
    except Exception:
        pass

    # Next, search common directories for any JWT-like token, capturing source file
    try:
        line = subprocess.check_output(
            "grep -Rno 'ey[A-Za-z0-9_\\-\\.]\\{20,\\}' ~/.codex ~/.config/codex 2>/dev/null | head -n 1",
            shell=True,
            text=True,
        ).strip()
        if line:
            # Expect: /path/to/file:LINE:eyJhbGci...
            parts = line.rsplit(":", 2)
            src_path = parts[0] if len(parts) == 3 else "(grep)"
            tok = parts[-1]
            if tok:
                os.environ["CODEX_AUTH_TOKEN"] = tok
                os.environ["OCEAN_CODEX_AUTH"] = "1"
                os.environ["OCEAN_CODEX_TOKEN_SOURCE"] = src_path
                info = _jwt_info(tok)
                try:
                    exp_s = info.get("exp_iso") or "unknown"
                    expired = info.get("expired")
                    note = f"exp={exp_s}{' (expired)' if expired else ''}"
                    _feed(f"🌊 Ocean: Found Codex token via grep in {src_path} (masked, {note}).")
                except Exception:
                    pass
                return
    except Exception:
        pass
    def _scan_token(txt: str) -> Optional[str]:
        # Common forms: raw JWT-like string, id_token=..., CODEX_AUTH_TOKEN=...
        # 1) id_token=...
        m = re.search(r"id_token=([A-Za-z0-9\-_.]+)", txt)
        if m:
            return m.group(1)
        # 2) CODEX_AUTH_TOKEN=...
        m = re.search(r"CODEX_AUTH_TOKEN=\"?([A-Za-z0-9\-_.]+)\"?", txt)
        if m:
            return m.group(1)
        # 3) any JWT-like token
        m = re.search(r"(ey[A-Za-z0-9_\-\.]{20,})", txt)
        if m:
            return m.group(1)
        return None

    # Avoid interactive flows like `codex auth login` here; only use non-interactive commands.
    for args in (["auth", "print-token"], ["auth", "token"], ["auth", "--show-token"], ["auth", "export"], ["auth"]):
        try:
            tok = subprocess.run([codex, *args], capture_output=True, text=True, timeout=10)
            txt = (tok.stdout or "") + "\n" + (tok.stderr or "")
            cand = _scan_token(txt) or ""
            if cand and len(cand) > 20:
                os.environ["CODEX_AUTH_TOKEN"] = cand
                os.environ["OCEAN_CODEX_AUTH"] = "1"
                os.environ.setdefault("OCEAN_CODEX_TOKEN_SOURCE", f"{codex} {' '.join(args)}")
                try:
                    _feed("🌊 Ocean: Codex auth token acquired (masked).")
                except Exception:
                    pass
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

    # Build minimal, compatible codex exec command with advanced controls.
    # Do NOT pass --model; let Codex decide its default model.
    # Defaults: sandbox ON (workspace-write), search ON; bypass only if explicitly enabled
    use_search = os.getenv("OCEAN_CODEX_SEARCH") not in ("0", "false", "False")
    bypass = os.getenv("OCEAN_CODEX_BYPASS_SANDBOX") in ("1", "true", "True")
    use_json = os.getenv("OCEAN_CODEX_JSON") in ("1", "true", "True")
    stream = os.getenv("OCEAN_CODEX_STREAM") in ("1", "true", "True")
    profile = os.getenv("OCEAN_CODEX_PROFILE")
    sandbox = os.getenv("OCEAN_CODEX_SANDBOX")  # read-only | workspace-write | danger-full-access
    approval = os.getenv("OCEAN_CODEX_APPROVAL")  # untrusted | on-failure | on-request | never
    want_cd = os.getenv("OCEAN_CODEX_CD", "1") not in ("0", "false", "False")
    skip_git = False
    try:
        import subprocess as _sp
        chk = _sp.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
        if chk.returncode != 0:
            skip_git = True
    except Exception:
        skip_git = True
    cmd = [
        _codex_bin() or "codex",
    ]
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
        # Default sandbox to workspace-write if not specified
        sb = sandbox if sandbox in ("read-only", "workspace-write", "danger-full-access") else "workspace-write"
        cmd += ["--sandbox", sb]
        if approval in ("untrusted", "on-failure", "on-request", "never"):
            cmd += ["--ask-for-approval", approval]
    if use_json or stream:
        cmd.append("--json")

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
        # Ensure subscription token is exported to child processes if available
        try:
            _ensure_token_env()
            if os.getenv("CODEX_AUTH_TOKEN"):
                env["CODEX_AUTH_TOKEN"] = os.getenv("CODEX_AUTH_TOKEN", "")
        except Exception:
            pass
        _last_mode = "subscription"
    elif env.get("OPENAI_API_KEY"):
        _last_mode = "api_fallback"
        # Defer to API fallback below (do not attempt CLI in this mode)
    else:
        _last_mode = "unavailable"
        if force:
            raise CodexUnavailable("Codex exec returned no JSON mapping")
        try:
            _feed("🌊 Ocean: ❌ Codex not authenticated and no OPENAI_API_KEY present. Run 'codex login' or export OPENAI_API_KEY.")
        except Exception:
            pass
        return None

    # Announce effective environment once in verbose mode
    global _announced
    try:
        if os.getenv("OCEAN_VERBOSE", "1") not in ("0", "false", "False") and not _announced:
            codex_path = shutil.which("codex") or "(not found)"
            token = "yes" if os.getenv("CODEX_AUTH_TOKEN") else "no"
            api = "yes" if os.getenv("OPENAI_API_KEY") else "no"
            search = "yes" if use_search else "no"
            src = os.getenv("OCEAN_CODEX_TOKEN_SOURCE", "(unknown)") if token == "yes" else "-"
            # Try to decode exp for readability
            exp_note = ""
            try:
                t = os.getenv("CODEX_AUTH_TOKEN") or ""
                parts = t.split(".")
                if len(parts) >= 2:
                    pad = '=' * (-len(parts[1]) % 4)
                    payload = base64.urlsafe_b64decode(parts[1] + pad)
                    data = json.loads(payload.decode("utf-8", errors="ignore"))
                    exp = data.get("exp")
                    if isinstance(exp, (int, float)):
                        dt = _dt.datetime.fromtimestamp(exp)
                        exp_note = f", token_exp={dt.strftime('%Y-%m-%d %H:%M:%S')}"
            except Exception:
                pass
            sb = (sandbox or "workspace-write") if not bypass else "bypass"
            ap = approval or "(default)"
            stream_on = os.getenv("OCEAN_CODEX_STREAM") in ("1", "true", "True")
            _feed(f"🌊 Ocean: Codex env → mode={_last_mode}, codex={codex_path}, token={token} (src={src}{exp_note}), api_key={api}, search={search}, sandbox={sb}, approval={ap}, stream={'on' if stream_on else 'off'}")
            _announced = True
    except Exception:
        pass

    # If in subscription mode, attempt CLI exec first; else skip to API fallback
    if _last_mode == "subscription":
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file: Optional[Path] = None
        if agent:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_file = logs_dir / f"codex-{agent.lower()}-{ts}.log"
        # Prepare last-message file for robust parsing when JSON banners are present
        last_msg_file: Optional[Path] = None
        try:
            custom_last = os.getenv("OCEAN_CODEX_LAST_MSG")
            if custom_last:
                last_msg_file = Path(custom_last)
            else:
                from datetime import datetime as _dt
                last_msg_file = logs_dir / f"codex-last-{(agent or 'Ocean').lower()}-{_dt.now().strftime('%Y%m%d-%H%M%S')}.txt"
            cmd += ["--output-last-message", str(last_msg_file)]
        except Exception:
            last_msg_file = None
        # Add a simple retry with backoff for transient failures
        attempts = 0
        stdout = stderr = ""
        debug = os.getenv("OCEAN_CODEX_DEBUG") in ("1", "true", "True")
        while attempts < 2:
            attempts += 1
            try:
                # codex exec expects the prompt as an optional positional argument.
                # Pass it directly rather than via stdin to avoid interactive hangs.
                if debug:
                    try:
                        cmd_repr = " ".join([*(cmd[:2]), "…PROMPT…", *cmd[2:]]) if len(cmd) >= 2 else "codex exec …PROMPT…"
                        _feed(f"🌊 Ocean: [debug] Running: {cmd_repr} (agent={agent or 'Ocean'})")
                        _feed(f"🌊 Ocean: [debug] Prompt size: {len(full_prompt)} chars")
                    except Exception:
                        pass
                if stream:
                    # Stream JSONL/events to feed while capturing the full output
                    try:
                        import subprocess as _sp, json as _json, time as _time
                        proc = _sp.Popen(
                            [*cmd, full_prompt],
                            stdout=_sp.PIPE,
                            stderr=_sp.PIPE,
                            text=True,
                            env=env,
                            bufsize=1,
                        )
                        stdout_chunks: list[str] = []
                        start = _time.time()
                        while True:
                            if proc.stdout is None:
                                break
                            line = proc.stdout.readline()
                            if not line:
                                if proc.poll() is not None:
                                    break
                                # timeout check
                                if _time.time() - start > int(os.getenv("OCEAN_CODEX_TIMEOUT", str(timeout))):
                                    try:
                                        proc.kill()
                                    except Exception:
                                        pass
                                    raise RuntimeError("codex exec stream timed out")
                                continue
                            stdout_chunks.append(line)
                            # Try to surface useful events succinctly
                            sline = line.strip()
                            if not sline:
                                continue
                            try:
                                evt = _json.loads(sline)
                                if isinstance(evt, dict):
                                    kind = str(evt.get("event") or evt.get("type") or "evt")
                                    # Show short messages and token usage
                                    if kind.lower() in ("message","assistant","tool","event"):
                                        txt = evt.get("content") or evt.get("text") or evt.get("message") or "(event)"
                                        txt = str(txt)
                                        _feed(f"🪵 Codex: {kind}: " + (txt[:160] + ("…" if len(txt) > 160 else "")))
                                    if "tokens" in evt or "tokens_used" in evt:
                                        val = evt.get("tokens_used") or evt.get("tokens")
                                        _feed(f"🪵 Codex: tokens={val}")
                                    continue
                            except Exception:
                                pass
                            # Non-JSON line, print a short head
                            _feed("🪵 Codex: " + (sline[:160] + ("…" if len(sline) > 160 else "")))
                        # Read remaining stderr
                        try:
                            stderr = proc.stderr.read() if proc.stderr else ""
                        except Exception:
                            stderr = ""
                        stdout = "".join(stdout_chunks)
                    except Exception as _se:
                        # Fallback to non-streaming run
                        try:
                            _feed(f"🌊 Ocean: stream mode error; falling back — {_se}")
                        except Exception:
                            pass
                        proc = _sp.run(
                            [*cmd, full_prompt],
                            capture_output=True,
                            text=True,
                            timeout=int(os.getenv("OCEAN_CODEX_TIMEOUT", str(timeout))),
                            env=env,
                        )
                        stdout = (proc.stdout or "")
                        stderr = (proc.stderr or "")
                else:
                    proc = subprocess.run(
                        [*cmd, full_prompt],
                        capture_output=True,
                        text=True,
                        timeout=int(os.getenv("OCEAN_CODEX_TIMEOUT", str(timeout))),
                        env=env,
                    )
                    stdout = (proc.stdout or "")
                    stderr = (proc.stderr or "")
                if stdout.strip():
                    break
                if debug:
                    try:
                        rc = proc.returncode
                        def _head(text: str, n: int = 12) -> str:
                            lines = (text or "").splitlines()
                            return " | ".join(line.strip() for line in lines[:n] if line.strip())
                        _feed(f"🌊 Ocean: [debug] rc={rc}; stderr: {_head(stderr)}; stdout: {_head(stdout)}")
                    except Exception:
                        pass
            except Exception as e:
                if attempts >= 2:
                    if log_file:
                        try:
                            log_file.write_text(f"ERROR: {e}\n", encoding="utf-8")
                        except Exception:
                            pass
                    _feed(f"🌊 Ocean: Codex exec error (agent={agent or 'Ocean'}): {e}")
                    stdout = ""
                    stderr = str(e)
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
        # Fallback: parse last-message file if present and not parsed yet
        if (not isinstance(obj, dict)) and last_msg_file and last_msg_file.exists():
            try:
                lm = last_msg_file.read_text(encoding="utf-8")
                try:
                    obj = json.loads(lm)
                except Exception:
                    obj = _extract_json(lm)
            except Exception:
                pass
        if isinstance(obj, dict):
            # Interpret common shapes below
            pass
        else:
            # Fall through to API fallback if available
            if env.get("OPENAI_API_KEY"):
                _last_mode = "api_fallback"
            else:
                # Optionally retry once with sandbox bypass if not already enabled
                auto_bypass = os.getenv("OCEAN_CODEX_AUTO_BYPASS") not in ("0", "false", "False")
                already_bypass = "--dangerously-bypass-approvals-and-sandbox" in cmd
                retried = False
                if auto_bypass and not already_bypass:
                    try:
                        cmd2 = list(cmd) + ["--dangerously-bypass-approvals-and-sandbox"]
                        _feed("🌊 Ocean: Retrying Codex exec with sandbox bypass due to prior failure…")
                        proc2 = subprocess.run(
                            [*cmd2, full_prompt],
                            capture_output=True,
                            text=True,
                            timeout=int(os.getenv("OCEAN_CODEX_TIMEOUT", str(timeout))),
                            env=env,
                        )
                        out2 = proc2.stdout or ""
                        err2 = proc2.stderr or ""
                        obj2 = None
                        try:
                            obj2 = json.loads(out2)
                        except Exception:
                            obj2 = _extract_json(out2)
                        if isinstance(obj2, dict):
                            try:
                                _feed(f"🌊 Ocean: Codex exec OK (files={len(obj2)})")
                            except Exception:
                                pass
                            return obj2  # type: ignore[return-value]
                        # fallthrough to detailed logs
                        stdout = out2
                        stderr = err2
                        cmd = cmd2
                        retried = True
                    except Exception:
                        pass
                # Emit concise logs to feed for diagnosis
                try:
                    mode = _last_mode
                    rc = locals().get('proc2').returncode if retried and 'proc2' in locals() else (locals().get('proc').returncode if 'proc' in locals() else None)  # type: ignore[name-defined]
                    _cmd = list(cmd)
                    if _cmd:
                        _cmd = _cmd[:-1] + ["…PROMPT…"] if _cmd[-1] else _cmd
                    cmd_repr = " ".join(_cmd) if _cmd else "codex exec …PROMPT…"
                    msg = f"Codex exec failed to produce JSON (agent={agent or 'Ocean'}, mode={mode}, rc={rc})."
                    _last_error_detail = msg + f" cmd={cmd_repr}"
                    _feed("🌊 Ocean: " + msg)
                    _feed(f"🌊 Ocean: Cmd: {cmd_repr}")
                    def _head(text: str, n: int = 12) -> str:
                        lines = (text or "").splitlines()
                        return " | ".join(line.strip() for line in lines[:n] if line.strip())
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
                _last_error_detail = "API fallback returned no JSON mapping"
                return None
        except Exception as e:
            try:
                _feed(f"🌊 Ocean: OpenAI API fallback error: {e}")
            except Exception:
                pass
            _last_error_detail = f"API fallback error: {e}"
            return None
    
    # By here, obj should be parsed from either CLI or API fallback
    if not isinstance(obj, dict):
        _last_error_detail = "No JSON mapping returned"
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
