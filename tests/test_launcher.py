"""Launcher helpers for bare ``ocean`` (Textual vs chat routing)."""

from __future__ import annotations

import pytest

from ocean import launcher


def test_resolve_bare_ocean_argv_returns_chat() -> None:
    assert launcher.resolve_bare_ocean_argv() == ["chat"]


def test_want_chat_instead_of_tui(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCEAN_DEFAULT_UI", raising=False)
    assert launcher.want_chat_instead_of_tui() is False
    monkeypatch.setenv("OCEAN_DEFAULT_UI", "chat")
    assert launcher.want_chat_instead_of_tui() is True


def test_is_automation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCEAN_TEST", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert launcher.is_automation() is False
    monkeypatch.setenv("OCEAN_TEST", "1")
    assert launcher.is_automation() is True
