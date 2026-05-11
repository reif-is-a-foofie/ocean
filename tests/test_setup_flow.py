from pathlib import Path

from ocean.setup_flow import resolve_ocean_repo_root


def test_resolve_ocean_repo_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ocean"\n', encoding="utf-8")
    (tmp_path / "ocean").mkdir()
    (tmp_path / "ocean" / "__init__.py").write_text('"""pkg"""', encoding="utf-8")
    assert resolve_ocean_repo_root(tmp_path) == tmp_path.resolve()
