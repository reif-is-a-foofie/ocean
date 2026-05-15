"""Lightweight LLM calls for early-session product hints (OpenAI / Gemini API only)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from .backends import get_codegen_backend, get_gemini_model, get_openai_model


def early_brain_enabled() -> bool:
    return os.getenv("OCEAN_EARLY_BRAIN", "1").strip().lower() not in ("0", "false", "no", "off")


def _gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def _doctrine_context(cwd: Path, max_chars: int = 6000) -> str:
    from .product_loop import read_doctrine_summary

    summaries = read_doctrine_summary(cwd)
    if not summaries:
        return "(No doctrine files found in project root yet.)"
    chunks: list[str] = []
    for name in sorted(summaries):
        body = summaries[name].strip()
        if not body:
            continue
        chunks.append(f"## {name}\n{body}")
    text = "\n\n".join(chunks)
    if len(text) > max_chars:
        return text[: max_chars - 20] + "\n\n…(truncated)"
    return text


def _brain_user_prompt(cwd: Path) -> str:
    ctx = _doctrine_context(cwd)
    return (
        "You are Ocean's early product-intelligence brain. The user just finished onboarding "
        "credentials and model selection in the Ocean CLI.\n\n"
        "Using ONLY the doctrine excerpts below, emit **3 to 5** short bullet lines "
        "(each line starts with '- ') naming the **smallest next valuable moves** or focus risks. "
        "No markdown besides those leading dashes; no JSON; no code fences; max ~80 words total.\n\n"
        f"{ctx}"
    )


def _openai_brain(*, cwd: Path, timeout: float) -> str | None:
    key = _openai_key()
    if not key:
        return None
    api_model = get_openai_model(cwd)
    if api_model.startswith("o4"):
        api_model = "gpt-4o-mini"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    messages = [
        {
            "role": "system",
            "content": "You advise on product sequencing. Follow the user's format constraints exactly.",
        },
        {"role": "user", "content": _brain_user_prompt(cwd)},
    ]
    body: dict[str, Any] = {"model": api_model, "messages": messages, "temperature": 0.3}
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return str((((data.get("choices") or [{}])[0]).get("message") or {}).get("content") or "").strip() or None


def _gemini_brain(*, cwd: Path, timeout: float, api_key: str | None = None) -> str | None:
    key = (api_key or "").strip() or _gemini_key()
    if not key:
        return None
    model = get_gemini_model(cwd).strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    body: dict[str, Any] = {
        "systemInstruction": {
            "parts": [
                {
                    "text": "You advise on product sequencing. Follow the user's format constraints exactly.",
                }
            ]
        },
        "contents": [{"role": "user", "parts": [{"text": _brain_user_prompt(cwd)}]}],
        "generationConfig": {"temperature": 0.3},
    }
    resp = httpx.post(url, headers=headers, json=body, timeout=timeout)
    data = resp.json()
    if resp.status_code >= 400:
        err = data.get("error") if isinstance(data.get("error"), dict) else {}
        msg = (err.get("message") if isinstance(err, dict) else None) or json.dumps(data)[:300]
        raise RuntimeError(f"Gemini API HTTP {resp.status_code}: {msg}")
    cands = data.get("candidates") or []
    text = ""
    if cands and isinstance(cands[0], dict):
        parts = ((cands[0].get("content") or {}).get("parts")) or []
        if isinstance(parts, list):
            for p in parts:
                if isinstance(p, dict) and p.get("text"):
                    text += str(p["text"])
    return text.strip() or None


def fetch_early_loop_brain_text(*, cwd: Path | None = None, timeout: float = 22.0) -> str | None:
    """Return a short plain-text brain snippet, or None if disabled / unavailable / error."""
    if not early_brain_enabled():
        return None
    root = Path(cwd or Path.cwd()).resolve()
    backend = get_codegen_backend(root)
    try:
        if backend == "openai_api" and _openai_key():
            return _openai_brain(cwd=root, timeout=timeout)
        from . import setup_gemini as _sg

        gkey, src = _sg.resolve_gemini_key_for_early_brain()
        if gkey:
            out = _gemini_brain(cwd=root, timeout=timeout, api_key=gkey)
            if out and src == "embedded":
                _sg.record_embedded_gemini_use()
            return out
    except Exception:
        return None
    return None
