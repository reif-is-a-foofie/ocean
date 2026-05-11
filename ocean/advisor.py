from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AdvisorResult:
    source: str
    text: str
    data: dict[str, Any] | None = None


def build_pm_prompt(payload: dict[str, Any]) -> str:
    return (
        "You are Ocean's Product Manager advisor. Ocean is not trying to be a full brain; "
        "it is the durable doctrine and routing layer for an agentic coding tool.\n\n"
        "Cursor, Codex, and Claude are strong coding engines. Your job is to behave like the software "
        "development team and value driver around them: choose the right work, prevent missed lifecycle "
        "steps, and hand the coding engine discrete jobs.\n\n"
        "Governing question:\n"
        "What is the smallest next change that makes this more valuable to the target user?\n\n"
        "Rank proposed work by these factors:\n"
        "- user value\n"
        "- setup friction reduced\n"
        "- trust increased\n"
        "- demo power\n"
        "- technical dependency\n"
        "- risk\n\n"
        "Return ONLY JSON with this shape:\n"
        "{\n"
        '  "recommended_task": {\n'
        '    "title": "smallest next valuable change",\n'
        '    "rationale": "why this beats the alternatives",\n'
        '    "scores": {\n'
        '      "user_value": 1,\n'
        '      "setup_friction_reduced": 1,\n'
        '      "trust_increased": 1,\n'
        '      "demo_power": 1,\n'
        '      "technical_dependency": 1,\n'
        '      "risk": 1\n'
        "    }\n"
        "  },\n"
        '  "feature_set": ["feature or improvement to build next"],\n'
        '  "agent_instructions": ["instruction for the coding agent"],\n'
        '  "doctrine_implications": ["durable rule or learning"],\n'
        '  "questions": ["blocking question, only if truly needed"]\n'
        "}\n\n"
        "Prefer one task. Explain why it is more valuable than plausible alternatives. "
        "If feedback is present, convert it into product implications.\n\n"
        "Context JSON:\n"
        + json.dumps(payload, indent=2, sort_keys=True)
    )


def ask_pm_advisor(payload: dict[str, Any], *, cwd: Path, timeout: int = 60) -> AdvisorResult | None:
    """Ask an external AI process for PM judgment if configured.

    Modes:
    - OCEAN_PM_ADVISOR_CMD: command receives the prompt on stdin and returns text.
    - OCEAN_PM_ADVISOR=codex: run `codex exec` with a read-only sandbox.

    If neither mode is configured, return None so the host MCP client can use
    its own model on the returned advisor prompt.
    """
    prompt = build_pm_prompt(payload)
    custom_cmd = os.getenv("OCEAN_PM_ADVISOR_CMD")
    if custom_cmd:
        return run_text_advisor(custom_cmd, prompt, cwd=cwd, timeout=timeout)
    if (os.getenv("OCEAN_PM_ADVISOR") or "").lower() == "codex":
        return _run_codex_advisor(prompt, cwd=cwd, timeout=timeout)
    return None


def ask_chat_advisor(prompt: str, *, cwd: Path, timeout: int = 90) -> AdvisorResult | None:
    custom_cmd = os.getenv("OCEAN_CHAT_ADVISOR_CMD") or os.getenv("OCEAN_PM_ADVISOR_CMD")
    if custom_cmd:
        return run_text_advisor(custom_cmd, prompt, cwd=cwd, timeout=timeout)
    if (os.getenv("OCEAN_CHAT_ADVISOR") or os.getenv("OCEAN_PM_ADVISOR") or "").lower() == "codex":
        return _run_codex_advisor(prompt, cwd=cwd, timeout=timeout)
    return None


def run_text_advisor(command: str, prompt: str, *, cwd: Path, timeout: int) -> AdvisorResult | None:
    return _run_custom_advisor(command, prompt, cwd=cwd, timeout=timeout)


def _run_custom_advisor(command: str, prompt: str, *, cwd: Path, timeout: int) -> AdvisorResult | None:
    cmd = shlex.split(command)
    if not cmd:
        return None
    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=timeout,
        check=False,
    )
    text = (proc.stdout or proc.stderr or "").strip()
    if not text:
        text = f"advisor command exited {proc.returncode} without output"
    return AdvisorResult(source=command, text=text, data=_extract_json(text))


def _run_codex_advisor(prompt: str, *, cwd: Path, timeout: int) -> AdvisorResult | None:
    codex = shutil.which("codex")
    if not codex:
        return None
    cmd = [
        codex,
        "--cd",
        str(cwd),
        "exec",
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "never",
        prompt,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), timeout=timeout, check=False)
    text = (proc.stdout or proc.stderr or "").strip()
    if not text:
        text = f"codex advisor exited {proc.returncode} without output"
    return AdvisorResult(source="codex", text=text, data=_extract_json(text))


def _extract_json(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None
