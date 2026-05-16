"""First-run onboarding: crew without project.json, setup JSONL events, dotenv merge, OpenAI prompt TTY."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ocean.cli import app
from ocean.dotenv_merge import merge_dotenv_assignments

runner = CliRunner()


def _patch_cli_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import ocean.cli as cli_mod

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli_mod, "ROOT", tmp_path)
    monkeypatch.setattr(cli_mod, "DOCS", tmp_path / "docs")
    monkeypatch.setattr(cli_mod, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(cli_mod, "BACKEND", tmp_path / "backend")
    monkeypatch.setattr(cli_mod, "UI", tmp_path / "ui")
    monkeypatch.setattr(cli_mod, "DEVOPS", tmp_path / "devops")
    monkeypatch.setattr(cli_mod, "PROJECTS", tmp_path / "projects")
    monkeypatch.setenv("OCEAN_DISABLE_WORKSPACE", "1")


def test_crew_runs_without_project_json(monkeypatch, tmp_path: Path):
    _patch_cli_paths(monkeypatch, tmp_path)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)
    monkeypatch.setenv("OCEAN_DISABLE_CODEX", "1")
    monkeypatch.setenv("OCEAN_SIMPLE_FEED", "1")
    monkeypatch.delenv("OCEAN_EVENTS_FILE", raising=False)

    r = runner.invoke(app, ["crew"])
    assert r.exit_code == 0
    assert "Crew assembled" in r.output


def test_chat_emits_setup_jsonl(monkeypatch, tmp_path: Path):
    from rich.prompt import Prompt

    _patch_cli_paths(monkeypatch, tmp_path)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)

    answers = iter(
        [
            "Test Project",
            "web",
            "A test",
            "ship",
            "none",
        ]
    )

    def fake_prompt(text, default=None, choices=None):
        t = str(text)
        if "Project name" in t:
            return next(answers)
        if "Project type" in t:
            return next(answers)
        if "description" in t.lower():
            return next(answers)
        if "Goals" in t:
            return next(answers)
        if "Constraints" in t:
            return next(answers)
        return default if default is not None else ""

    monkeypatch.setattr(Prompt, "ask", fake_prompt)
    monkeypatch.setenv("OCEAN_DISABLE_CODEX", "1")
    monkeypatch.setenv("OCEAN_SIMPLE_FEED", "1")
    monkeypatch.setenv("OCEAN_SKIP_BACKEND_PROMPT", "1")
    monkeypatch.setenv("OCEAN_SKIP_REPO_PROMPT", "1")
    monkeypatch.delenv("OCEAN_EVENTS_FILE", raising=False)

    r = runner.invoke(app, ["chat"])
    assert r.exit_code == 0
    jsonl_files = sorted((tmp_path / "logs").glob("events-*.jsonl"))
    assert jsonl_files, "expected events JSONL"
    payload_lines = []
    for pth in jsonl_files:
        for line in pth.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload_lines.append(json.loads(line))
    welcomes = [
        x
        for x in payload_lines
        if x.get("event") == "setup" and x.get("phase") == "setup" and x.get("id") == "welcome"
    ]
    assert any(x.get("kind") == "phase_start" for x in welcomes)
    assert any(x.get("kind") == "phase_end" for x in welcomes)
    assert any(x.get("id") == "project_clarify" and x.get("kind") == "phase_end" for x in payload_lines)


def test_merge_dotenv_assignments_updates_key(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("FOO=1\nOTHER=x\n", encoding="utf-8")
    merge_dotenv_assignments(p, {"FOO": "2", "NEW": "y"})
    text = p.read_text(encoding="utf-8")
    assert "FOO=2" in text
    assert "OTHER=x" in text
    assert "NEW=y" in text


def test_prompt_openai_key_skips_when_non_tty(monkeypatch, tmp_path: Path):
    import ocean.cli as cli_mod

    _patch_cli_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli_mod, "_is_test_env", lambda: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    evt = tmp_path / "evt.jsonl"
    monkeypatch.setenv("OCEAN_EVENTS_FILE", str(evt))
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(cli_mod.sys.stdout, "isatty", lambda: True)

    def boom(_prompt: str = "") -> str:
        raise AssertionError("getpass should not run without tty")

    monkeypatch.setattr(cli_mod.getpass, "getpass", boom)

    evt.write_text("", encoding="utf-8")
    cli_mod._prompt_openai_api_key_if_needed()


@pytest.fixture
def mcp_stdio_cmd_onboarding() -> list[str]:
    return [sys.executable, "-m", "ocean.mcp_server"]


def test_mcp_stdio_ocean_set_codegen_backend(mcp_stdio_cmd_onboarding: list[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from ocean.mcp_client import StdioJsonRpcClient

    monkeypatch.chdir(tmp_path)
    client = StdioJsonRpcClient(cmd=mcp_stdio_cmd_onboarding)
    client.start()
    try:
        client.initialize(timeout=10)
        ok = client.call_tool(
            "ocean_set_codegen_backend",
            {"project_root": str(tmp_path), "backend": "dry_plan_only"},
        )
        body = ok["structuredContent"]
        assert body.get("ok") is True
        assert body.get("codegen_backend") == "dry_plan_only"
        bad = client.call_tool(
            "ocean_set_codegen_backend",
            {"backend": "bogus_backend"},
        )
        assert bad["structuredContent"].get("ok") is False
    finally:
        client.stop()


def test_prompt_openai_tty_saves_env(monkeypatch, tmp_path: Path):
    import ocean.cli as cli_mod

    _patch_cli_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli_mod, "_is_test_env", lambda: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OCEAN_EVENTS_FILE", str(tmp_path / "evt.jsonl"))
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli_mod.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(cli_mod.getpass, "getpass", lambda _p="": "sk-fake-secret")

    cli_mod._prompt_openai_api_key_if_needed()

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=" in env_text
    assert os.environ.get("OPENAI_API_KEY") == "sk-fake-secret"


def test_quickstart_existing_key_requires_explicit_choice(monkeypatch, tmp_path: Path):
    import ocean.cli as cli_mod
    from rich.prompt import Prompt

    _patch_cli_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli_mod, "_is_test_env", lambda: False)
    monkeypatch.delenv("OCEAN_CODEGEN_BACKEND", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "AIza-existing-secret")
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli_mod.sys.stdout, "isatty", lambda: True)

    prompts: list[str] = []

    def fake_prompt(text, default=None, choices=None):
        prompts.append(str(text))
        assert choices and "3" in choices
        return "3"

    monkeypatch.setattr(Prompt, "ask", fake_prompt)

    backend = cli_mod._quickstart_login_if_possible(tmp_path)

    assert backend == "gemini_api"
    assert "Choose login" in prompts
    prefs = json.loads((tmp_path / "docs" / "ocean_prefs.json").read_text(encoding="utf-8"))
    assert prefs["codegen_backend"] == "gemini_api"


def test_quickstart_pasted_openai_key_is_parsed_and_saved(monkeypatch, tmp_path: Path):
    import ocean.cli as cli_mod
    from rich.prompt import Prompt

    _patch_cli_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli_mod, "_is_test_env", lambda: False)
    monkeypatch.delenv("OCEAN_CODEGEN_BACKEND", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli_mod.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: "2")
    monkeypatch.setattr(cli_mod.getpass, "getpass", lambda _p="": "sk-test-secret")

    backend = cli_mod._quickstart_login_if_possible(tmp_path)

    assert backend == "openai_api"
    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=sk-test-secret" in env_text
    prefs = json.loads((tmp_path / "docs" / "ocean_prefs.json").read_text(encoding="utf-8"))
    assert prefs["codegen_backend"] == "openai_api"


def test_quickstart_pasted_assignment_extracts_key(monkeypatch, tmp_path: Path):
    import ocean.cli as cli_mod
    from rich.prompt import Prompt

    _patch_cli_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli_mod, "_is_test_env", lambda: False)
    monkeypatch.delenv("OCEAN_CODEGEN_BACKEND", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli_mod.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: "2")
    monkeypatch.setattr(cli_mod.getpass, "getpass", lambda _p="": "export GEMINI_API_KEY='AIza-test-secret-value'")

    backend = cli_mod._quickstart_login_if_possible(tmp_path)

    assert backend == "gemini_api"
    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=AIza-test-secret-value" in env_text
    assert "export GEMINI_API_KEY" not in env_text


def test_quickstart_subscription_login_is_default(monkeypatch, tmp_path: Path):
    import ocean.cli as cli_mod
    from rich.prompt import Prompt

    _patch_cli_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cli_mod, "_is_test_env", lambda: False)
    monkeypatch.delenv("OCEAN_CODEGEN_BACKEND", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli_mod.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: "1")
    calls: list[str] = []
    monkeypatch.setattr(cli_mod, "_ensure_codex_auth", lambda: calls.append("auth"))

    backend = cli_mod._quickstart_login_if_possible(tmp_path)

    assert backend == "codex"
    assert calls == ["auth"]
    prefs = json.loads((tmp_path / "docs" / "ocean_prefs.json").read_text(encoding="utf-8"))
    assert prefs["codegen_backend"] == "codex"


def test_quickstart_cursor_handoff_pref_still_offers_login(monkeypatch, tmp_path: Path):
    import ocean.cli as cli_mod
    from rich.prompt import Prompt

    _patch_cli_paths(monkeypatch, tmp_path)
    prefs_path = tmp_path / "docs" / "ocean_prefs.json"
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    prefs_path.write_text(json.dumps({"codegen_backend": "cursor_handoff"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(cli_mod, "_is_test_env", lambda: False)
    monkeypatch.delenv("OCEAN_CODEGEN_BACKEND", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli_mod.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: "1")
    calls: list[str] = []
    monkeypatch.setattr(cli_mod, "_ensure_codex_auth", lambda: calls.append("auth"))

    backend = cli_mod._quickstart_login_if_possible(tmp_path)

    assert backend == "codex"
    assert calls == ["auth"]
    prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
    assert prefs["codegen_backend"] == "codex"
