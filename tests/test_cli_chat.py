from typer.testing import CliRunner

from ocean.cli import app, entrypoint


runner = CliRunner()


def test_entrypoint_runs_help_when_args_present():
    r = runner.invoke(app, ["--help"])  # use app directly
    assert r.exit_code == 0
    assert "OCEAN CLI orchestrator" in r.output


def test_chat_non_interactive(monkeypatch, tmp_path):
    # Simulate a non-interactive run by patching prompts
    from ocean import cli as cli_mod

    answers = {
        "name": "Test Project",
        "kind": "web",
        "description": "A test",
        "goals": "ship",
        "constraints": "none",
    }

    def fake_prompt(text, default=None):
        if text.startswith("Project name"):
            return answers["name"]
        if text.startswith("Project type"):
            return answers["kind"]
        if text.startswith("One-line description"):
            return answers["description"]
        if text.startswith("Primary goals"):
            return answers["goals"]
        if text.startswith("Constraints"):
            return answers["constraints"]
        return default

    monkeypatch.setattr(cli_mod.typer, "prompt", fake_prompt)

    # Run chat command and assert it completes
    r = runner.invoke(app, ["chat"])  # do not call entrypoint directly in tests
    assert r.exit_code == 0
    assert "Spinning up the crew" in r.output

