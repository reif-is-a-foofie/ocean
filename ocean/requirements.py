from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class CheckResult:
    ok: bool
    label: str
    detail: str = ""


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_yaml_if_available(path: Path) -> Optional[dict]:
    try:
        import yaml  # type: ignore
    except Exception:
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_requirements(docs_dir: Path) -> Tuple[Optional[list], str]:
    """Load requirements from docs/requirements.json or docs/requirements.yml.

    Returns (requirements_list_or_None, source_path_string).
    """
    j = docs_dir / "requirements.json"
    y = docs_dir / "requirements.yml"
    if j.exists():
        obj = _read_json(j) or {}
        reqs = obj.get("requirements") if isinstance(obj, dict) else None
        return (reqs if isinstance(reqs, list) else None, str(j))
    if y.exists():
        obj = _read_yaml_if_available(y) or {}
        reqs = obj.get("requirements") if isinstance(obj, dict) else None
        return (reqs if isinstance(reqs, list) else None, str(y))
    return None, ""


def _http_check(item: dict) -> CheckResult:
    import urllib.request, urllib.error, time
    url = item.get("url") or ""
    label = item.get("label") or f"HTTP: {url}"
    expect_status = int(item.get("expect_status", 200))
    expect_contains = item.get("expect_contains")
    retries = int(item.get("retries", 3))
    delay = float(item.get("delay", 1.0))
    last_err = ""
    for i in range(max(1, retries)):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ocean-requirements/1"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = getattr(resp, "status", 0) or resp.getcode()
                body = resp.read().decode("utf-8", errors="ignore")
                if status != expect_status:
                    last_err = f"status={status} != {expect_status}"
                elif expect_contains and (expect_contains not in body):
                    last_err = f"missing substring: {expect_contains!r}"
                else:
                    return CheckResult(True, label, f"OK {status}")
        except Exception as e:
            last_err = str(e)
        time.sleep(delay)
    return CheckResult(False, label, last_err)


def _file_exists_check(item: dict) -> CheckResult:
    p = Path(item.get("path") or "")
    label = item.get("label") or f"File exists: {p}"
    ok = p.exists()
    return CheckResult(ok, label, "exists" if ok else "missing")


def validate(requirements: list) -> Tuple[bool, List[CheckResult]]:
    """Validate a list of requirement items.

    Supported kinds:
      - http: {url, expect_status=200, expect_contains?, retries?, delay?}
      - file: {path}
    """
    results: List[CheckResult] = []
    ok_all = True
    for item in requirements:
        if not isinstance(item, dict):
            results.append(CheckResult(False, "invalid item", "not an object"))
            ok_all = False
            continue
        kind = (item.get("kind") or "").lower()
        if kind == "http":
            r = _http_check(item)
        elif kind == "file":
            r = _file_exists_check(item)
        else:
            r = CheckResult(False, f"unknown kind: {kind}", "unsupported")
        results.append(r)
        if not r.ok:
            ok_all = False
    return ok_all, results


def write_report(docs_dir: Path, results: List[CheckResult], source: str) -> Path:
    out = docs_dir / "requirements_report.md"
    lines = ["# Requirements Report", ""]
    if source:
        lines.append(f"Source: {source}")
        lines.append("")
    for r in results:
        status = "✅" if r.ok else "❌"
        lines.append(f"- {status} {r.label} — {r.detail}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out

