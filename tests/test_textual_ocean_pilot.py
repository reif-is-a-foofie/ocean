"""Textual Pilot tests for ``OceanTextualApp`` (bare ``ocean`` UI)."""

from __future__ import annotations

import asyncio

from textual.widgets import Input

from ocean.testing.scenarios import pilot_failure_report
from ocean.ui.app import OceanTextualApp


async def _launch_export():
    app = OceanTextualApp()
    async with app.run_test(size=(100, 32)) as pilot:
        assert pilot.app.screen is not None
        st = pilot.app.export_state()
        assert st["current_screen"]
        assert isinstance(st["visible_events"], list)
        assert len(st["visible_events"]) >= 1
        assert isinstance(st["active_agents"], list)
        assert isinstance(st["pending_tasks"], list)
        assert st["last_error"] is None
        assert "onboarding_phase" in st
        assert "project_configured" in st


def test_pilot_app_launches_and_export_state() -> None:
    asyncio.run(_launch_export())


async def _help_feed():
    app = OceanTextualApp()
    async with app.run_test(size=(100, 32)) as pilot:
        inp = pilot.app.query_one("#command-input", Input)
        inp.focus()
        inp.value = "help"
        await pilot.press("enter")
        texts = " ".join(e["text"] for e in pilot.app.export_state()["visible_events"])
        assert "Commands" in texts or "help" in texts.lower()


def test_pilot_help_adds_feed_event() -> None:
    asyncio.run(_help_feed())


async def _task_add():
    app = OceanTextualApp()
    async with app.run_test(size=(100, 32)) as pilot:
        inp = pilot.app.query_one("#command-input", Input)
        inp.focus()
        inp.value = "task add Write Pilot tests"
        await pilot.press("enter")
        st = pilot.app.export_state()
        titles = [t["title"] for t in st["pending_tasks"]]
        assert any("Pilot" in t for t in titles)


def test_pilot_task_add_updates_tasks() -> None:
    asyncio.run(_task_add())


async def _invalid():
    app = OceanTextualApp()
    async with app.run_test(size=(100, 32)) as pilot:
        inp = pilot.app.query_one("#command-input", Input)
        inp.focus()
        inp.value = "not_a_real_command_xyz"
        await pilot.press("enter")
        st = pilot.app.export_state()
        assert st["last_error"]
        assert "Unknown" in st["last_error"]


def test_pilot_invalid_command_sets_last_error() -> None:
    asyncio.run(_invalid())


async def _quit():
    app = OceanTextualApp()
    async with app.run_test(size=(100, 32)) as pilot:
        inp = pilot.app.query_one("#command-input", Input)
        inp.focus()
        inp.value = "quit"
        await pilot.press("enter")


def test_pilot_quit_exits_cleanly() -> None:
    asyncio.run(_quit())


def test_pilot_onboarding_prompt_visible_in_fresh_workspace(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    async def run():
        app = OceanTextualApp(cwd=tmp_path)
        async with app.run_test(size=(100, 32)) as pilot:
            st = pilot.app.export_state()
            assert st["onboarding_phase"] == "name"
            assert st["project_configured"] is False
            ev = " ".join(e["text"] for e in st["visible_events"])
            assert "Moroni" in ev or "project" in ev.lower()

    asyncio.run(run())


def test_pilot_failure_report_shape() -> None:
    exc = ValueError("boom")
    rep = pilot_failure_report(
        scenario="demo",
        expected="ok",
        actual="fail",
        app=None,
        exc=exc,
    )
    assert rep["scenario"] == "demo"
    assert rep["traceback"] and "boom" in rep["traceback"]
    assert rep["exported_app_state"] is None
