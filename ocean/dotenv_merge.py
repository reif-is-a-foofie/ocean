"""Merge KEY=VALUE pairs into a .env file without loading secrets elsewhere."""

from __future__ import annotations

from pathlib import Path


def merge_dotenv_assignments(path: Path, updates: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    keys_done: set[str] = set()
    out: list[str] = []

    def esc_value(v: str) -> str:
        if "\n" in v or "#" in v:
            escaped = v.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if " " in v or "\t" in v:
            return f'"{v}"'
        return v

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        k = line.split("=", 1)[0].strip()
        if k in updates:
            out.append(f"{k}={esc_value(updates[k])}")
            keys_done.add(k)
        else:
            out.append(line)
    for k, v in updates.items():
        if k not in keys_done:
            out.append(f"{k}={esc_value(v)}")
    path.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
