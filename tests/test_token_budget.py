"""Token budget ledger (rolling hour)."""

from __future__ import annotations

import json
import time
from pathlib import Path

from ocean import token_budget


def test_note_and_usage_recent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    token_budget.note_usage(100, cwd=tmp_path)
    token_budget.note_usage(50, cwd=tmp_path)
    assert token_budget.usage_recent(token_budget._ledger_path(tmp_path)) == 150


def test_budget_cap_from_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OCEAN_TOKEN_BUDGET_PER_HOUR", "1000")
    assert token_budget.budget_cap(tmp_path) == 1000


def test_prune_old_events(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    p = token_budget._ledger_path(tmp_path)
    past = time.time() - 7200
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"events": [{"t": past, "n": 999}, {"t": time.time(), "n": 1}]}),
        encoding="utf-8",
    )
    assert token_budget.usage_recent(p) == 1
