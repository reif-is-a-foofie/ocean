#!/usr/bin/env python3
"""Validate docs/personas.yaml: each default chat-crew agent has a non-empty skills list.

Exit 0 if OK, 1 if validation fails. Safe to run from cron or CI.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (default: parent of scripts/)",
    )
    args = parser.parse_args(argv)
    root = (args.root or _repo_root()).resolve()
    sys.path.insert(0, str(root))

    from ocean.persona import load_personas
    from ocean.personas import AGENT_EMOJI

    required = [n for n in AGENT_EMOJI if n not in ("Ocean", "You")]
    path = root / "docs" / "personas.yaml"
    if not path.exists():
        print(f"ERROR: missing {path}", file=sys.stderr)
        return 1

    data = load_personas(path)
    errors: list[str] = []
    for name in sorted(required):
        persona = data.get(name)
        if not persona:
            errors.append(f"{name}: missing agent block under agents:")
            continue
        skills = persona.get("skills")
        if not isinstance(skills, list) or len(skills) == 0:
            errors.append(f"{name}: skills must be a non-empty YAML list")
            continue
        if not all(isinstance(s, str) and s.strip() for s in skills):
            errors.append(f"{name}: each skill must be a non-empty string")
            continue
        sd = persona.get("skill_discovery")
        if sd is not None:
            if not isinstance(sd, list) or len(sd) == 0:
                errors.append(f"{name}: skill_discovery must be a non-empty YAML list when present")
            elif not all(isinstance(s, str) and s.strip() for s in sd):
                errors.append(f"{name}: each skill_discovery item must be a non-empty string")
        rf = persona.get("research_focus")
        if rf is not None and (not isinstance(rf, str) or not rf.strip()):
            errors.append(f"{name}: research_focus must be a non-empty string when present")

    if errors:
        print("Persona skills check failed:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"OK: {len(required)} crew agents have skills in {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
