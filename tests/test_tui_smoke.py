"""Toad-only ``ocean tui`` — CLI help smoke test (no exec)."""


def test_cli_tui_help():
    from typer.testing import CliRunner

    from ocean.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["tui", "--help"])
    assert r.exit_code == 0
    assert "Toad" in r.output or "tui" in r.output.lower()
