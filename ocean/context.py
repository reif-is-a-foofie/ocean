from __future__ import annotations
from pathlib import Path
from typing import Iterable, Optional

from .models import ProjectSpec


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


# Brave Search integration removed; Codex --search handles web access when enabled


def build_context_bundle(spec: Optional[ProjectSpec]) -> Path:
    """Create docs/context_bundle.md.

    Bundle now includes only the local context summary. Online search context is
    delegated to Codex (--search) during codegen.
    """
    ensure_docs_dir()
    summary = build_context_summary()
    bundle = DOCS / "context_bundle.md"
    parts = [summary.read_text(encoding="utf-8")]
    bundle.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return bundle
