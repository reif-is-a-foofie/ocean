"""Unit tests for early LLM brain (mocked HTTP)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from ocean.brain_client import early_brain_enabled, fetch_early_loop_brain_text


def test_early_brain_disabled(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OCEAN_EARLY_BRAIN", "0")
    (tmp_path / "VISION.md").write_text("# V\nx\n", encoding="utf-8")
    assert fetch_early_loop_brain_text(cwd=tmp_path) is None


def test_early_brain_openai_mock(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OCEAN_EARLY_BRAIN", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    (tmp_path / "VISION.md").write_text("# Vision\nShip small.\n", encoding="utf-8")

    resp = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": "- First\n- Second"}}]}
    resp.raise_for_status = MagicMock()

    with patch("ocean.brain_client.get_codegen_backend", return_value="openai_api"):
        with patch("ocean.brain_client.httpx.post", return_value=resp) as post:
            out = fetch_early_loop_brain_text(cwd=tmp_path, timeout=5.0)
    assert out
    assert "- First" in out
    post.assert_called_once()
    assert "api.openai.com" in str(post.call_args)


def test_early_brain_wrong_backend(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    (tmp_path / "VISION.md").write_text("# V\n", encoding="utf-8")
    with patch("ocean.brain_client.get_codegen_backend", return_value="codex"):
        assert fetch_early_loop_brain_text(cwd=tmp_path) is None


def test_early_brain_enabled_default(monkeypatch) -> None:
    monkeypatch.delenv("OCEAN_EARLY_BRAIN", raising=False)
    assert early_brain_enabled() is True
