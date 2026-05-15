from typer.testing import CliRunner

from ocean.cli import app, entrypoint


runner = CliRunner()


def test_entrypoint_bare_adds_chat_subcommand(monkeypatch):
    import ocean.cli as cli_mod

    recorded: list[list[str]] = []

    def capture_app() -> None:
        recorded.append(list(cli_mod.sys.argv))

    monkeypatch.setattr(cli_mod, "app", capture_app)
    monkeypatch.setattr(cli_mod.sys, "argv", ["ocean"])
    cli_mod.entrypoint()
    assert cli_mod.sys.argv == ["ocean", "chat"]
    assert recorded == [["ocean", "chat"]]


def test_entrypoint_with_args_untouched(monkeypatch):
    import ocean.cli as cli_mod

    recorded: list[list[str]] = []

    def capture_app() -> None:
        recorded.append(list(cli_mod.sys.argv))

    monkeypatch.setattr(cli_mod, "app", capture_app)
    monkeypatch.setattr(cli_mod.sys, "argv", ["ocean", "--version"])
    cli_mod.entrypoint()
    assert cli_mod.sys.argv == ["ocean", "--version"]
    assert recorded == [["ocean", "--version"]]


def test_ask_non_tty_skips_rich_prompt_outside_pytest(monkeypatch):
    """Agent shells often have no TTY; Rich Prompt EOF prints Aborted — use defaults."""
    import ocean.cli as cli_mod
    from rich.prompt import Prompt

    def boom(*_a, **_k):
        raise AssertionError("Prompt.ask must not run when stdin is non-TTY outside pytest")

    monkeypatch.setattr(Prompt, "ask", boom)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("OCEAN_TEST", raising=False)
    monkeypatch.setattr(cli_mod.sys.stdin, "isatty", lambda: False)
    monkeypatch.setenv("OCEAN_ALLOW_QUESTIONS", "1")

    assert cli_mod._ask("label", default="hello") == "hello"
    assert cli_mod._ask("pick", choices=["a", "b"], default="") == "a"


def test_chat_non_interactive(monkeypatch, tmp_path):
    # Simulate a non-interactive run by patching Rich prompts
    from ocean import cli as cli_mod
    from rich.prompt import Prompt

    answers = {
        "name": "Test Project",
        "kind": "web",
        "description": "A test",
        "goals": "ship",
        "constraints": "none",
    }

    def fake_prompt(text, default=None, choices=None):
        if "Project name" in text:
            return answers["name"]
        if "Project type" in text:
            return answers["kind"]
        if "description" in text:
            return answers["description"]
        if "goals" in text:
            return answers["goals"]
        if "constraints" in text:
            return answers["constraints"]
        return default

    monkeypatch.setattr(Prompt, "ask", fake_prompt)

    # Run chat command and assert it completes
    # Disable codex during unit test to avoid external dependency
    monkeypatch.setenv("OCEAN_DISABLE_CODEX", "1")
    monkeypatch.setenv("OCEAN_SIMPLE_FEED", "1")
    monkeypatch.setenv("OCEAN_SKIP_REPO_PROMPT", "1")
    r = runner.invoke(app, ["chat"])  # do not call entrypoint directly in tests
    assert r.exit_code == 0
    assert "Crew assembled" in r.output


def test_clarify_command():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "clarify" in r.output


def test_crew_command():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "crew" in r.output


def test_doctor_command_is_listed():
    r = runner.invoke(app, ["doctor", "--help"])
    assert r.exit_code == 0
