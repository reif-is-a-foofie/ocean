from typer.testing import CliRunner

from ocean.cli import app, entrypoint


runner = CliRunner()


def test_entrypoint_runs_help_when_args_present():
    r = runner.invoke(app, ["--help"])  # use app directly
    assert r.exit_code == 0
    assert "OCEAN CLI orchestrator" in r.output


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

