"""Tests for ocean bench_runner (offline; no network)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from ocean import bench_runner as br


def _git_init(p: Path) -> None:
    (p / "README.md").write_text("# tiny\n", encoding="utf-8")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run(["git", "init"], cwd=p, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=p, check=True, capture_output=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=p, check=True, capture_output=True, env=env)
    subprocess.run(["git", "commit", "-m", "init"], cwd=p, check=True, capture_output=True, env=env)


def test_load_allowlist_and_pick(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    yml = tmp_path / "b.yaml"
    yml.write_text(
        "repos:\n  - name: a\n    url: https://example.com/a.git\n  - name: b\n    path: /tmp\n",
        encoding="utf-8",
    )
    specs = br.load_bench_allowlist(yml)
    assert len(specs) == 2
    assert br.pick_repo(yml, seed=1).name in {"a", "b"}


def test_execute_bench_at_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCEAN_TEST", "1")
    ws = tmp_path / "ws"
    ws.mkdir()
    _git_init(ws)
    out = tmp_path / "out"
    out.mkdir()
    rep = br.execute_bench_at(
        ws,
        output_dir=out,
        bench_id="fixture1",
        run_codegen=True,
        run_pytest=False,
        report_extras={"fixture": True},
    )
    assert rep.get("fixture") is True
    kinds = [e.get("kind") for e in rep.get("trace_events") or []]
    assert "project_state" in kinds
    assert "persona_nominations" in kinds
    assert "next_action" in kinds
    llm = rep.get("llm_invocations") or []
    assert llm and llm[0].get("skipped_reason")
    jf = out / "bench-fixture1.json"
    assert jf.exists()
    data = json.loads(jf.read_text(encoding="utf-8"))
    assert "code_delta" in data
    assert (out / "bench-fixture1.md").exists()


def test_materialize_copy(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "f.txt").write_text("x", encoding="utf-8")
    spec = br.BenchRepoSpec(name="src", path=str(src))
    dest_parent = tmp_path / "dest"
    out = br.materialize_repo(spec, dest_parent, allow_network=False)
    assert (out / "f.txt").read_text() == "x"


def test_network_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCEAN_BENCH_NETWORK", raising=False)
    assert br.network_allowed(False) is False
    monkeypatch.setenv("OCEAN_BENCH_NETWORK", "1")
    assert br.network_allowed(False) is True
