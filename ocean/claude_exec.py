"""Dispatch codegen tasks to the Claude CLI (claude -p)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict

from .feed import feed as _feed


class ClaudeUnavailable(Exception):
    pass


def _claude_bin() -> Optional[str]:
    return shutil.which("claude")


def available() -> bool:
    if os.getenv("OCEAN_DISABLE_CLAUDE") in ("1", "true", "True"):
        return False
    return _claude_bin() is not None


def _extract_json(text: str) -> Optional[Dict[str, str]]:
    """Extract a JSON file-map from claude's text output."""
    # Try raw parse first
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict):
            # Handle claude --output-format json wrapper: {"result": "...", ...}
            if "result" in obj and isinstance(obj["result"], str):
                inner = obj["result"].strip()
                # Strip markdown code fence if present
                inner = re.sub(r"^```[a-z]*\n?", "", inner)
                inner = re.sub(r"\n?```$", "", inner.strip())
                try:
                    obj2 = json.loads(inner)
                    if isinstance(obj2, dict) and all(isinstance(v, str) for v in obj2.values()):
                        return obj2
                except Exception:
                    pass
            # Direct file map
            if all(isinstance(v, str) for v in obj.values()):
                return obj
    except Exception:
        pass

    # Try to find a JSON block in the output
    for m in re.finditer(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text):
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict) and all(isinstance(v, str) for v in obj.values()):
                return obj
        except Exception:
            continue

    # Last resort: find any { } block
    for m in re.finditer(r"(\{[\s\S]*\})", text):
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict) and all(isinstance(v, str) for v in obj.values()):
                return obj
        except Exception:
            continue

    return None


def generate_files(
    instruction: str,
    context_file: Optional[Path] = None,
    suggested_files: Optional[list[str]] = None,
    timeout: int = 240,
    agent: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Use `claude -p` to generate files.

    Asks Claude to return a JSON mapping of relative path -> file content.
    """
    if not available():
        _feed("🌊 Ocean: Claude CLI not found on PATH.")
        return None

    parts: list[str] = []
    if context_file and Path(context_file).exists():
        try:
            parts.append("Context:\n" + Path(context_file).read_text(encoding="utf-8"))
        except Exception:
            pass

    parts.append(
        "You are a code generation tool. "
        "Return ONLY a JSON object mapping relative file paths to their full contents. "
        "No markdown, no commentary, no code fences — just the JSON object."
    )
    if suggested_files:
        parts.append("Suggested files: " + ", ".join(suggested_files))
    parts.append("Instruction: " + instruction)
    prompt = "\n\n".join(parts)

    cmd = [_claude_bin() or "claude", "-p", prompt,
           "--output-format", "json",
           "--dangerously-skip-permissions"]

    if agent:
        _feed(f"🌊 Ocean: [{agent}] dispatching to Claude CLI…")
    else:
        _feed("🌊 Ocean: Dispatching to Claude CLI…")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path.cwd()),
        )
    except subprocess.TimeoutExpired:
        _feed("🌊 Ocean: Claude CLI timed out.")
        return None
    except Exception as e:
        _feed(f"🌊 Ocean: Claude CLI error — {e}")
        return None

    if result.returncode != 0:
        err = (result.stderr or "").strip()[:200]
        _feed(f"🌊 Ocean: Claude CLI exited {result.returncode} — {err}")
        return None

    _record_tokens(result.stdout)

    files = _extract_json(result.stdout)
    if not files:
        _feed("🌊 Ocean: Claude returned no parseable file map.")
        return None

    return files


# Blended Sonnet input+output rate: ~$9 / 1M tokens
_COST_PER_TOKEN = 9.0 / 1_000_000


def _record_tokens(raw_output: str) -> None:
    """Parse cost_usd from claude JSON response and record token estimate."""
    try:
        data = json.loads(raw_output.strip())
        cost = float(data.get("cost_usd") or data.get("total_cost_usd") or 0.0)
        if cost > 0:
            tokens = max(1, int(cost / _COST_PER_TOKEN))
            from pathlib import Path
            from . import token_budget
            token_budget.note_usage(tokens, cwd=Path.cwd())
            _feed(f"🌊 Ocean: ~{tokens:,} tokens (${cost:.4f})")
            return
    except Exception:
        pass
    # Fallback: estimate from output length
    try:
        from pathlib import Path
        from . import token_budget
        tokens = max(1, len(raw_output) // 4)
        token_budget.note_usage(tokens, cwd=Path.cwd())
    except Exception:
        pass
