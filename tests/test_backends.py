"""Tests for codegen backend prefs and Codex failure classification."""

from pathlib import Path

from ocean.backends import (
    VALID_BACKENDS,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_MODEL,
    get_codegen_backend,
    get_gemini_model,
    get_openai_model,
    probe_snapshot,
    prompt_codegen_model_if_needed,
    save_prefs,
    write_cursor_handoffs,
)
from ocean.cli import classify_codex_exec_failure
from ocean.models import ProjectSpec, Task


def test_classify_quota_billing():
    s = "Error: you have exceeded your monthly credits quota billing"
    assert classify_codex_exec_failure(s) == "quota_billing"


def test_classify_rate_limit():
    assert classify_codex_exec_failure("HTTP 429 rate limit") == "rate_limit"


def test_classify_auth():
    assert classify_codex_exec_failure("401 unauthorized token expired") == "auth_permission"


def test_get_codegen_backend_from_env(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OCEAN_CODEGEN_BACKEND", "cursor_handoff")
    assert get_codegen_backend() == "cursor_handoff"


def test_get_codegen_backend_from_prefs(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OCEAN_CODEGEN_BACKEND", raising=False)
    save_prefs({"codegen_backend": "dry_plan_only"}, tmp_path)
    assert get_codegen_backend(tmp_path) == "dry_plan_only"


def test_probe_snapshot_keys():
    snap = probe_snapshot()
    assert set(snap.keys()) >= {
        "codex_cli",
        "openai_api_key",
        "gemini_api_key",
        "cursor_cli",
        "docs_dir",
        "prefs_file",
        "openai_model",
        "gemini_model",
    }
    assert isinstance(snap["openai_model"], str) and snap["openai_model"]
    assert isinstance(snap["gemini_model"], str) and snap["gemini_model"]


def test_get_models_from_prefs(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    monkeypatch.delenv("OCEAN_OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OCEAN_CODEX_MODEL", raising=False)
    monkeypatch.delenv("OCEAN_GEMINI_MODEL", raising=False)
    save_prefs({"openai_model": "gpt-4o", "gemini_model": "gemini-2.0-flash"}, tmp_path)
    assert get_openai_model(tmp_path) == "gpt-4o"
    assert get_gemini_model(tmp_path) == "gemini-2.0-flash"


def test_get_openai_model_env_overrides_prefs(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    save_prefs({"openai_model": "gpt-4o"}, tmp_path)
    monkeypatch.setenv("OCEAN_OPENAI_MODEL", "gpt-4.1-mini")
    assert get_openai_model(tmp_path) == "gpt-4.1-mini"


def test_prompt_codegen_model_skips_for_codex(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    assert prompt_codegen_model_if_needed("codex", tmp_path) == ""
    assert prompt_codegen_model_if_needed("claude", tmp_path) == ""


def test_prompt_codegen_model_under_pytest_returns_default(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    assert prompt_codegen_model_if_needed("gemini_api", tmp_path) == DEFAULT_GEMINI_MODEL
    assert prompt_codegen_model_if_needed("openai_api", tmp_path) == DEFAULT_OPENAI_MODEL


def test_write_cursor_handoffs_creates_files(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    spec = ProjectSpec(name="P", kind="web")
    tasks = [
        Task(title="Do thing", description="desc", owner="Q", files_touched=["a.py"]),
    ]
    hdir = write_cursor_handoffs(tasks, spec, docs, feed_fn=None)
    assert hdir.is_dir()
    assert (hdir / "README.md").exists()
    assert list(hdir.glob("*.md"))


def test_valid_backends_contains_expected():
    assert "codex" in VALID_BACKENDS
    assert "cursor_handoff" in VALID_BACKENDS
    assert "gemini_api" in VALID_BACKENDS
