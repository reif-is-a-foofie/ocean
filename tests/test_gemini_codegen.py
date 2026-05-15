"""Tests for Gemini / OpenAI HTTP codegen helpers (no network)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_gemini_api_codegen_parses_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict]] = []

    def fake_post(url: str, headers: dict | None = None, json: dict | None = None, timeout: object = None):
        calls.append((url, json or {}))

        class Resp:
            status_code = 200

            def json(self) -> dict:
                return {
                    "candidates": [{"content": {"parts": [{"text": '{"x.py": "y = 1\\n"}'}]}}],
                    "usageMetadata": {"totalTokenCount": 10},
                }

        return Resp()

    monkeypatch.setattr("ocean.codex_exec.httpx.post", fake_post)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    from ocean import codex_exec as ce

    out = ce._gemini_api_codegen("instruction text", timeout=30)
    assert out == {"x.py": "y = 1\n"}
    assert calls and "gemini-flash-latest" in calls[0][0]
    assert (calls[0][1].get("generationConfig") or {}).get("responseMimeType") == "application/json"


def test_gemini_api_uses_prefs_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ocean_prefs.json").write_text(
        '{"codegen_backend": "gemini_api", "gemini_model": "gemini-2.0-flash"}\n',
        encoding="utf-8",
    )
    calls: list[str] = []

    def fake_post(url: str, headers: dict | None = None, json: dict | None = None, timeout: object = None):
        calls.append(url)

        class Resp:
            status_code = 200

            def json(self) -> dict:
                return {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}

        return Resp()

    monkeypatch.setattr("ocean.codex_exec.httpx.post", fake_post)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("OCEAN_GEMINI_MODEL", raising=False)

    from ocean import codex_exec as ce

    ce._gemini_api_codegen("x", timeout=5)
    assert calls and "models/gemini-2.0-flash:generateContent" in calls[0]


def test_openai_api_branch_in_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ocean_prefs.json").write_text('{"codegen_backend": "openai_api"}\n', encoding="utf-8")

    def fake_post(url: str, headers: dict | None = None, json: dict | None = None, timeout: object = None):
        class Resp:
            status_code = 200

            def json(self) -> dict:
                return {
                    "choices": [{"message": {"content": '{"a.txt": "hi"}'}}],
                    "usage": {"total_tokens": 5},
                }

        return Resp()

    monkeypatch.setattr("ocean.codex_exec.httpx.post", fake_post)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OCEAN_CODEGEN_BACKEND", raising=False)

    from ocean import codex_exec as ce

    got = ce.generate_files_with_fallback("make a file", timeout=20)
    assert got == {"a.txt": "hi"}
