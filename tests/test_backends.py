"""Tests for codegen backend prefs and Codex failure classification."""

from pathlib import Path

from ocean.backends import (
    VALID_BACKENDS,
    get_codegen_backend,
    probe_snapshot,
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
    assert set(snap.keys()) >= {"codex_cli", "openai_api_key", "cursor_cli", "docs_dir", "prefs_file"}


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
