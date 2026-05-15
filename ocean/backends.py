"""Codegen backend discovery, prefs, and Cursor handoff helpers."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

PREFS_RELATIVE = Path("docs") / "ocean_prefs.json"

VALID_BACKENDS = frozenset(
    {"codex", "claude", "openai_api", "gemini_api", "cursor_handoff", "dry_plan_only"}
)

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-flash-latest"

GEMINI_MODEL_MENU: tuple[tuple[str, str], ...] = (
    ("1", "gemini-flash-latest"),
    ("2", "gemini-2.0-flash"),
    ("3", "gemini-1.5-pro-latest"),
    ("4", "gemini-1.5-flash-latest"),
)

OPENAI_MODEL_MENU: tuple[tuple[str, str], ...] = (
    ("1", "gpt-4o-mini"),
    ("2", "gpt-4o"),
    ("3", "gpt-4.1-mini"),
    ("4", "o4-mini"),
)

# Ordered fallback chain — first available and healthy agent wins
AGENT_FALLBACK_ORDER = ("codex", "claude", "cursor_handoff")
HANDOFFS_DIRNAME = "handoffs"


def prefs_path(cwd: Path | None = None) -> Path:
    root = cwd or Path.cwd()
    return root / PREFS_RELATIVE


def load_prefs(cwd: Path | None = None) -> dict[str, Any]:
    p = prefs_path(cwd)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_prefs(data: dict[str, Any], cwd: Path | None = None) -> Path:
    p = prefs_path(cwd)
    p.parent.mkdir(parents=True, exist_ok=True)
    merged = load_prefs(cwd)
    merged.update(data)
    p.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return p


def get_codegen_backend(cwd: Path | None = None) -> str:
    env = (os.getenv("OCEAN_CODEGEN_BACKEND") or "").strip().lower()
    if env in VALID_BACKENDS:
        return env
    disk = (load_prefs(cwd).get("codegen_backend") or "").strip().lower()
    if disk in VALID_BACKENDS:
        return disk
    return "codex"


def set_codegen_backend_env(backend: str) -> None:
    """Expose resolved backend to subprocesses and codex_exec."""
    if backend in VALID_BACKENDS:
        os.environ["OCEAN_CODEGEN_BACKEND"] = backend
    if backend == "openai_api":
        os.environ["OCEAN_PREFER_OPENAI_API"] = "1"
    else:
        os.environ.pop("OCEAN_PREFER_OPENAI_API", None)


def probe_codex_cli_installed() -> bool:
    return shutil.which("codex") is not None


def probe_claude_cli_installed() -> bool:
    return shutil.which("claude") is not None


def probe_openai_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def probe_gemini_api_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip())


def probe_cursor_cli() -> bool:
    return shutil.which("cursor") is not None or shutil.which("cursor-agent") is not None


def get_openai_model(cwd: Path | None = None) -> str:
    """Resolved OpenAI chat model: ``OCEAN_OPENAI_MODEL`` env, then ``openai_model`` in prefs, then default."""
    env_m = (os.getenv("OCEAN_OPENAI_MODEL") or os.getenv("OCEAN_CODEX_MODEL") or "").strip()
    if env_m:
        return env_m
    disk = (load_prefs(cwd).get("openai_model") or "").strip()
    if disk:
        return disk
    return DEFAULT_OPENAI_MODEL


def get_gemini_model(cwd: Path | None = None) -> str:
    """Resolved Gemini model id: ``OCEAN_GEMINI_MODEL`` env, then ``gemini_model`` in prefs, then default."""
    env_m = (os.getenv("OCEAN_GEMINI_MODEL") or "").strip()
    if env_m:
        return env_m
    disk = (load_prefs(cwd).get("gemini_model") or "").strip()
    if disk:
        return disk
    return DEFAULT_GEMINI_MODEL


def prompt_codegen_model_if_needed(backend: str, cwd: Path | None = None) -> str:
    """When backend uses HTTP APIs, persist a model choice (interactive once; prefs thereafter)."""
    root = cwd or Path.cwd()
    if backend == "openai_api":
        return _prompt_openai_model_menu(root)
    if backend == "gemini_api":
        return _prompt_gemini_model_menu(root)
    return ""


def _prompt_openai_model_menu(root: Path) -> str:
    if os.getenv("OCEAN_TEST") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        return get_openai_model(root)
    if os.getenv("OCEAN_SKIP_MODEL_PROMPT") in ("1", "true", "True"):
        return get_openai_model(root)
    if not _interactive_stdin():
        return get_openai_model(root)
    if (os.getenv("OCEAN_OPENAI_MODEL") or os.getenv("OCEAN_CODEX_MODEL") or "").strip():
        return get_openai_model(root)
    data = load_prefs(root)
    if (data.get("openai_model") or "").strip():
        return get_openai_model(root)
    try:
        from rich.prompt import Prompt

        lines = ["Pick OpenAI model for codegen (API):"] + [
            f"  [{k}] {mid}" for k, mid in OPENAI_MODEL_MENU
        ]
        print("\n".join(lines))
        choice = Prompt.ask(
            "Choose model (1–4)",
            choices=[k for k, _ in OPENAI_MODEL_MENU],
            default="1",
        )
    except Exception:
        return get_openai_model(root)
    picked = dict(OPENAI_MODEL_MENU).get(choice.strip(), DEFAULT_OPENAI_MODEL)
    save_prefs({"openai_model": picked}, root)
    return picked


def _prompt_gemini_model_menu(root: Path) -> str:
    if os.getenv("OCEAN_TEST") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        return get_gemini_model(root)
    if os.getenv("OCEAN_SKIP_MODEL_PROMPT") in ("1", "true", "True"):
        return get_gemini_model(root)
    if not _interactive_stdin():
        return get_gemini_model(root)
    if (os.getenv("OCEAN_GEMINI_MODEL") or "").strip():
        return get_gemini_model(root)
    data = load_prefs(root)
    if (data.get("gemini_model") or "").strip():
        return get_gemini_model(root)
    try:
        from rich.prompt import Prompt

        lines = ["Pick Gemini model for codegen (API):"] + [
            f"  [{k}] {mid}" for k, mid in GEMINI_MODEL_MENU
        ]
        print("\n".join(lines))
        choice = Prompt.ask(
            "Choose model (1–4)",
            choices=[k for k, _ in GEMINI_MODEL_MENU],
            default="1",
        )
    except Exception:
        return get_gemini_model(root)
    picked = dict(GEMINI_MODEL_MENU).get(choice.strip(), DEFAULT_GEMINI_MODEL)
    save_prefs({"gemini_model": picked}, root)
    return picked


def probe_snapshot(cwd: Path | None = None) -> dict[str, Any]:
    """Structured hints for prompts and doctor (no network)."""
    root = cwd or Path.cwd()
    return {
        "codex_cli": probe_codex_cli_installed(),
        "claude_cli": probe_claude_cli_installed(),
        "openai_api_key": probe_openai_api_key(),
        "gemini_api_key": probe_gemini_api_key(),
        "cursor_cli": probe_cursor_cli(),
        "docs_dir": str(root / "docs"),
        "prefs_file": str(prefs_path(root)),
        "openai_model": get_openai_model(root),
        "gemini_model": get_gemini_model(root),
    }


def apply_backend_env_from_prefs(cwd: Path | None = None) -> str:
    b = get_codegen_backend(cwd)
    set_codegen_backend_env(b)
    return b


def _interactive_stdin() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def prompt_codegen_backend_if_needed(cwd: Path | None = None) -> str:
    """Persist backend choice when missing and stdin is interactive."""
    root = cwd or Path.cwd()
    data = load_prefs(root)
    existing = (data.get("codegen_backend") or "").strip().lower()
    if existing in VALID_BACKENDS:
        set_codegen_backend_env(existing)
        return existing
    env_override = (os.getenv("OCEAN_CODEGEN_BACKEND") or "").strip().lower()
    if env_override in VALID_BACKENDS:
        save_prefs({"codegen_backend": env_override}, root)
        set_codegen_backend_env(env_override)
        return env_override
    if os.getenv("OCEAN_TEST") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        set_codegen_backend_env("codex")
        return "codex"
    if os.getenv("OCEAN_SKIP_BACKEND_PROMPT") in ("1", "true", "True"):
        set_codegen_backend_env("codex")
        return "codex"
    if not _interactive_stdin():
        set_codegen_backend_env("codex")
        return "codex"

    snap = probe_snapshot(root)
    lines = [
        "Pick your coding agent:",
        f"  [1] codex  — OpenAI Codex CLI ({'found' if snap['codex_cli'] else 'not on PATH'})",
        f"  [2] claude — Anthropic Claude CLI ({'found' if snap['claude_cli'] else 'not on PATH'})",
        "  [3] cursor — Cursor IDE handoffs (writes docs/handoffs/ for Composer)",
        f"  [4] openai_api — OpenAI API direct ({'key set' if snap['openai_api_key'] else 'no key'})",
        f"  [5] gemini_api — Google Gemini API ({'key set' if snap['gemini_api_key'] else 'no key'})",
        "  [6] dry_plan_only — plan only, no codegen",
    ]
    # Auto-detect best default
    if snap["codex_cli"]:
        default_choice = "1"
    elif snap["claude_cli"]:
        default_choice = "2"
    elif snap["cursor_cli"]:
        default_choice = "3"
    else:
        default_choice = "6"
    try:
        from rich.prompt import Prompt

        print("\n".join(lines))
        choice = Prompt.ask(
            "Choose agent (1–6)",
            choices=["1", "2", "3", "4", "5", "6"],
            default=default_choice,
        )
    except Exception:
        set_codegen_backend_env("codex")
        return "codex"

    mapping = {
        "1": "codex",
        "2": "claude",
        "3": "cursor_handoff",
        "4": "openai_api",
        "5": "gemini_api",
        "6": "dry_plan_only",
    }
    backend = mapping.get(choice.strip(), "codex")
    save_prefs({"codegen_backend": backend}, root)
    set_codegen_backend_env(backend)
    return backend


_SLUG_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _slug(s: str) -> str:
    t = _SLUG_RE.sub("-", s.strip().lower()).strip("-")
    return (t[:60] or "task") + ".md"


def write_cursor_handoffs(
    backlog: list[Any],
    spec: Any,
    docs_dir: Path,
    *,
    feed_fn: Any | None = None,
) -> Path:
    """Write docs/handoffs/*.md with copy-paste prompts for Cursor."""
    handoffs = docs_dir / HANDOFFS_DIRNAME
    handoffs.mkdir(parents=True, exist_ok=True)
    readme = handoffs / "README.md"
    lines_r = [
        "# Cursor handoffs (Ocean)",
        "",
        "Ocean is in **cursor_handoff** mode: run these prompts in **Cursor** (Composer / Agent),",
        "or attach them via Ocean's MCP server (`ocean mcp-server`).",
        "",
        f"- Project: **{getattr(spec, 'name', '(unknown)')}** ({getattr(spec, 'kind', '?')})",
        "",
        "## Tasks",
        "",
    ]
    for i, task in enumerate(backlog, start=1):
        title = getattr(task, "title", str(task))
        desc = getattr(task, "description", "")
        owner = getattr(task, "owner", "")
        files = getattr(task, "files_touched", []) or []
        fname = f"{i:02d}-{_slug(title)}"
        path = handoffs / fname
        body = "\n".join(
            [
                f"# {title}",
                "",
                f"Owner: {owner}",
                "",
                "## Context",
                desc or "(no description)",
                "",
                "## Files to touch",
                ", ".join(files) if files else "(tbd)",
                "",
                "## Instruction for Cursor",
                "Implement the above in this repo. Keep changes minimal and tested.",
                "",
            ]
        )
        path.write_text(body, encoding="utf-8")
        lines_r.append(f"- [{owner}] [{title}]({fname})")

    readme.write_text("\n".join(lines_r) + "\n", encoding="utf-8")

    if feed_fn:
        try:
            feed_fn(f"🌊 Ocean: Wrote Cursor handoffs under {handoffs}")
            feed_fn("🌊 Ocean: Open files in Cursor or run `ocean mcp-server` from the IDE.")
        except Exception:
            pass
    return handoffs
