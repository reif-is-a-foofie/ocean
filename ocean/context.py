from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from .models import ProjectSpec
from . import brave_search


DOCS = Path("docs")


def ensure_docs_dir() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)


def _truncate_read(p: Path, limit: int) -> str:
    try:
        return p.read_text(encoding="utf-8")[:limit]
    except Exception:
        return ""


def build_context_summary() -> Path:
    """Create docs/context_summary.md capturing local project context."""
    ensure_docs_dir()
    out = DOCS / "context_summary.md"
    lines: list[str] = []
    # Core docs
    lines.append("## project.json")
    lines.append(_truncate_read(DOCS / "project.json", 6000))
    lines.append("\n## backlog.json")
    lines.append(_truncate_read(DOCS / "backlog.json", 6000))
    lines.append("\n## plan.md")
    lines.append(_truncate_read(DOCS / "plan.md", 6000))
    lines.append("\n## prd.md (truncated)")
    lines.append(_truncate_read(DOCS / "prd.md", 8000))

    # Simple tree view (depth <= 3)
    lines.append("\n## repository tree (depth=3)")
    root = Path(".")
    for base in [Path("."), Path("backend"), Path("ui"), Path("devops"), DOCS]:
        if not base.exists():
            continue
        lines.append(f"# {base}")
        for path in sorted(base.rglob("*")):
            try:
                rel = path.relative_to(root)
                if len(rel.parts) > 3 or path.is_dir():
                    continue
                lines.append(str(rel))
            except Exception:
                continue

    # File samples
    lines.append("\n## file samples (truncated)")
    for base in [Path("backend"), Path("ui"), DOCS]:
        if not base.exists():
            continue
        for f in sorted(base.rglob("*")):
            if f.is_file() and f.suffix in {".py", ".md", ".json", ".yml", ".yaml", ".html", ".css"}:
                lines.append(f"### {f}")
                lines.append(_truncate_read(f, 4000))

    out.write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    return out


def brave_queries_for(spec: ProjectSpec) -> list[str]:
    qs: list[str] = []
    if spec.kind in ("web", "api"):
        qs.append("FastAPI best practices 2025")
        qs.append("GitHub Actions Python pytest example")
    if spec.kind == "web":
        qs.append("HTML CSS landing page accessibility checklist")
    return qs


def build_search_context(queries: Iterable[str]) -> Optional[Path]:
    if not brave_search.is_configured():
        return None
    ensure_docs_dir()
    out = DOCS / "search_context.md"
    lines: list[str] = ["# Brave Search Context\n"]
    for q in queries:
        data = brave_search.search(q)
        if not data:
            continue
        lines.append(f"\n## {q}")
        lines.append(brave_search.summarize_results(data))
    if len(lines) == 1:
        return None
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def build_context_bundle(spec: Optional[ProjectSpec]) -> Path:
    """Create docs/context_bundle.md by concatenating summary + search context."""
    ensure_docs_dir()
    summary = build_context_summary()
    search_path = None
    if spec is not None:
        qs = brave_queries_for(spec)
        if qs:
            search_path = build_search_context(qs)
    bundle = DOCS / "context_bundle.md"
    parts = [summary.read_text(encoding="utf-8")]
    if search_path and search_path.exists():
        parts.append(search_path.read_text(encoding="utf-8"))
    bundle.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return bundle

