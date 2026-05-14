"""Primary Textual layout (feed, agents, tasks, command)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Input, Label, RichLog

from ocean.core.orchestrator import Orchestrator


class MainWorkspace(Vertical):
    """Shell layout — no orchestration; calls ``Orchestrator`` only via ``refresh_all``."""

    def __init__(self, core: Orchestrator) -> None:
        super().__init__(id="main-workspace")
        self.core = core

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-row"):
            with Vertical(id="feed-col"):
                yield Label("Event feed")
                yield RichLog(id="event-feed", auto_scroll=True, max_lines=400, wrap=True, highlight=False)
            with Vertical(id="agent-col"):
                yield Label("Agents / status")
                yield DataTable(id="agent-table", zebra_stripes=True)
        with Horizontal(id="bottom-row"):
            with Vertical(id="task-col"):
                yield Label("Tasks")
                yield DataTable(id="task-table", zebra_stripes=True)
            with Vertical(id="cmd-col"):
                yield Label("Command")
                yield Input(placeholder="help | task add … | quit", id="command-input")

    def on_mount(self) -> None:
        agents = self.query_one("#agent-table", DataTable)
        agents.add_columns("Name", "Role", "Status")
        tasks = self.query_one("#task-table", DataTable)
        tasks.add_columns("ID", "Title", "Status")
        self.refresh_all()

    def refresh_all(self) -> None:
        log = self.query_one("#event-feed", RichLog)
        log.clear()
        for ev in self.core.events:
            log.write(f"[dim]{ev.ts}[/dim] [bold]{ev.author}[/bold]: {ev.text}")

        agents = self.query_one("#agent-table", DataTable)
        agents.clear(columns=True)
        agents.add_columns("Name", "Role", "Status")
        from ocean.core.agents import agent_status_snapshot

        for row in agent_status_snapshot():
            agents.add_row(row["name"], row["role"], row["status"])

        tasks = self.query_one("#task-table", DataTable)
        tasks.clear(columns=True)
        tasks.add_columns("ID", "Title", "Status")
        for t in self.core.tasks:
            tasks.add_row(t.id, t.title, t.status)
