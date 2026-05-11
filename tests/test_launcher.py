"""Launcher: Toad-first on bare ``ocean`` (TTY); ``chat`` for CI / no Toad."""

from __future__ import annotations

import sys

import pytest

from ocean import launcher


def test_resolve_bare_ocean_argv_chat_when_automation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCEAN_TEST", "1")
    assert launcher.resolve_bare_ocean_argv() == ["chat"]


def test_resolve_bare_ocean_argv_chat_when_not_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCEAN_TEST", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    assert launcher.resolve_bare_ocean_argv() == ["chat"]


def test_toad_binary_prefers_same_venv_executable(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    toad_path = bindir / "toad"
    toad_path.write_text("#!/bin/sh\necho toad\n", encoding="utf-8")
    toad_path.chmod(0o755)
    fake_py = bindir / "python3"
    fake_py.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(fake_py))
    monkeypatch.delenv("OCEAN_SKIP_TOAD", raising=False)
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)
    assert launcher.toad_binary() == str(toad_path)


def test_resolve_bare_ocean_argv_chat_when_tty_no_toad(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(launcher, "is_automation", lambda: False)
    monkeypatch.setattr(launcher, "ensure_toad_installed", lambda: False)
    monkeypatch.delenv("OCEAN_DEFAULT_UI", raising=False)
    monkeypatch.delenv("OCEAN_SKIP_TOAD", raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)
    assert launcher.resolve_bare_ocean_argv() == ["chat"]
    err = capsys.readouterr().err
    assert "toad" in err.lower()
    assert "chat" in err.lower()


def test_ensure_toad_install_skipped_when_automation(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    def boom(*_a, **_k):
        called.append("run")
        raise AssertionError("should not run subprocess in automation")

    monkeypatch.setenv("OCEAN_TEST", "1")
    monkeypatch.setattr(launcher, "toad_binary", lambda: None)
    monkeypatch.setattr(launcher.subprocess, "run", boom)
    assert launcher.ensure_toad_installed() is False
    assert called == []


def test_ensure_toad_pip_writes_venv_binary(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    bindir = tmp_path / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    py = bindir / "python3"
    py.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(py))
    monkeypatch.setattr(launcher, "is_automation", lambda: False)
    monkeypatch.setattr(launcher, "is_interactive_terminal", lambda: True)
    monkeypatch.delenv("OCEAN_SKIP_TOAD", raising=False)
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)

    def fake_run(cmd, **_kwargs):
        if len(cmd) >= 4 and cmd[0] == str(py) and list(cmd[1:4]) == ["-m", "pip", "install"]:
            toad_path = bindir / "toad"
            toad_path.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
            toad_path.chmod(0o755)
        import subprocess as sp

        return sp.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)
    assert launcher.ensure_toad_installed() is True
    assert launcher.toad_binary() == str(bindir / "toad")


def test_resolve_bare_ocean_argv_chat_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher, "is_automation", lambda: False)
    monkeypatch.setenv("OCEAN_DEFAULT_UI", "chat")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    assert launcher.resolve_bare_ocean_argv() == ["chat"]


def test_resolve_bare_ocean_argv_chat_when_skip_toad(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher, "is_automation", lambda: False)
    monkeypatch.setenv("OCEAN_SKIP_TOAD", "1")
    monkeypatch.delenv("OCEAN_DEFAULT_UI", raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    assert launcher.resolve_bare_ocean_argv() == ["chat"]
