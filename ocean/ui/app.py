"""Textual shell entry — UI only; logic lives in ``ocean.core``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input

from ocean.core.orchestrator import CommandResult, Orchestrator
from ocean.core.state import build_export_payload
from ocean.ui.screens.main import MainWorkspace


class OceanTextualApp(App[None]):
    """Minimal Ocean control room — Pilot-testable."""

    TITLE = "Ocean"
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, cwd: Path | None = None) -> None:
        super().__init__()
        self.core = Orchestrator(cwd=cwd)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield MainWorkspace(self.core)
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.query_one("#command-input", Input).focus()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "command-input":
            return
        text = event.value
        event.input.value = ""
        res = self.core.handle_command(text)
        try:
            ws = self.query_one("#main-workspace", MainWorkspace)
            ws.refresh_all()
        except Exception:
            pass
        if res == CommandResult.QUIT:
            self.exit()

    def export_state(self) -> dict[str, Any]:
        focused: str | None = None
        try:
            if self.focused is not None:
                wid = getattr(self.focused, "id", None)
                focused = str(wid) if wid else type(self.focused).__name__
        except Exception:
            focused = None
        inp_val = ""
        try:
            inp_val = self.query_one("#command-input", Input).value
        except Exception:
            pass
        screen_name = getattr(self.screen, "name", None) or "main"
        return build_export_payload(
            orchestrator=self.core,
            current_screen=str(screen_name),
            focused_widget=focused,
            command_input_value=inp_val,
        )


def run_ocean_textual_app() -> None:
    OceanTextualApp().run()
