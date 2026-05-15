"""setup_gemini: user vs embedded resolution and embedded daily cap."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from ocean import setup_gemini as sg


def test_user_key_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "user-secret")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    k, src = sg.resolve_gemini_key_for_early_brain()
    assert k == "user-secret"
    assert src == "user"


def test_embedded_when_no_user(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr(sg, "embedded_gemini_key", lambda: "emb")
    monkeypatch.setattr(sg, "_usage_path", lambda: tmp_path / "embedded_gemini_daily.json")
    k, src = sg.resolve_gemini_key_for_early_brain()
    assert k == "emb"
    assert src == "embedded"


def test_embedded_respects_daily_cap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OCEAN_EMBEDDED_GEMINI_DAILY_CAP", "2")
    monkeypatch.setattr(sg, "embedded_gemini_key", lambda: "emb")
    p = tmp_path / "embedded_gemini_daily.json"
    monkeypatch.setattr(sg, "_usage_path", lambda: p)
    from datetime import date

    p.write_text(json.dumps({"day": date.today().isoformat(), "count": 2}), encoding="utf-8")

    k, src = sg.resolve_gemini_key_for_early_brain()
    assert k is None
    assert src == "none"


def test_embedded_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OCEAN_DISABLE_EMBEDDED_GEMINI", "1")
    k, src = sg.resolve_gemini_key_for_early_brain()
    assert k is None
    assert src == "none"
