"""CLI help smoke tests for deprecated ``ocean tui`` (no app run)."""


def test_cli_tui_help():
    from typer.testing import CliRunner

    from ocean.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["tui", "--help"])
    assert r.exit_code == 0
    combined = r.output.lower()
    assert "textual" in combined or "ocean" in combined


def test_cli_chat_help():
    from typer.testing import CliRunner

    from ocean.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["chat", "--help"])
    assert r.exit_code == 0
    assert "onboarding" in r.output.lower() or "clarify" in r.output.lower() or "crew" in r.output.lower()
