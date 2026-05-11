from __future__ import annotations

from pathlib import Path


def runtime_root(cwd: Path | None = None) -> Path:
    """`.ocean` under the workspace (gitignored by default)."""
    root = cwd or Path.cwd()
    d = root / ".ocean"
    d.mkdir(parents=True, exist_ok=True)
    return d


def inbox_pending(root: Path) -> Path:
    p = root / "inbox" / "pending"
    p.mkdir(parents=True, exist_ok=True)
    return p


def inbox_archive(root: Path) -> Path:
    p = root / "inbox" / "archive"
    p.mkdir(parents=True, exist_ok=True)
    return p
