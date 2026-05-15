"""Persona YAML resolution: nested cwd and docs/bundle sync."""

from __future__ import annotations

from pathlib import Path

from ocean.persona import load_personas, resolve_personas_yaml_path


def test_load_personas_walks_parents(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "personas.yaml").write_text(
        "agents:\n  Moroni:\n    traits: [calm]\n    skills: [planning]\n",
        encoding="utf-8",
    )
    nested = root / "nested" / "deep"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    data = load_personas()
    assert "Moroni" in data
    assert data["Moroni"]["traits"] == ["calm"]
    assert data["Moroni"]["skills"] == ["planning"]


def test_resolve_personas_explicit_path_overrides_walk(tmp_path: Path) -> None:
    p = tmp_path / "docs" / "personas.yaml"
    p.parent.mkdir(parents=True)
    p.write_text("agents:\n  Q:\n    traits: [t]\n    skills: [s]\n", encoding="utf-8")
    data = load_personas(p)
    assert "Q" in data
    assert resolve_personas_yaml_path(search_start=tmp_path) == p.resolve()


def test_bundled_personas_matches_docs_in_repo() -> None:
    repo = Path(__file__).resolve().parents[1]
    docp = repo / "docs" / "personas.yaml"
    bundlep = repo / "ocean" / "personas.yaml"
    if docp.is_file() and bundlep.is_file():
        assert docp.read_text(encoding="utf-8") == bundlep.read_text(encoding="utf-8")
