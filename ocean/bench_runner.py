"""Bench harness: materialize a target repo, run Ocean signals, emit evidence JSON + Markdown."""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

BenchEvent = dict[str, Any]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _emit(trace: list[BenchEvent], kind: str, summary: str, detail: Any = None) -> None:
    trace.append(
        {
            "ts": _now_iso(),
            "kind": kind,
            "summary": summary,
            "detail": detail if detail is not None else {},
        }
    )


def tail_plain(text: str, *, lines: int = 48) -> str:
    from ocean import pty_harness

    ls = pty_harness.strip_ansi(text).splitlines()
    return "\n".join(ls[-lines:])


@dataclass
class BenchRepoSpec:
    name: str
    url: str | None = None
    path: str | None = None
    tags: list[str] = field(default_factory=list)


def load_bench_allowlist(config_path: Path | str) -> list[BenchRepoSpec]:
    p = Path(config_path)
    if not p.exists():
        return []
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    repos = raw.get("repos") or []
    out: list[BenchRepoSpec] = []
    if isinstance(repos, list):
        for item in repos:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            url = item.get("url")
            path = item.get("path")
            tags = item.get("tags") if isinstance(item.get("tags"), list) else []
            out.append(
                BenchRepoSpec(
                    name=name,
                    url=str(url).strip() if url else None,
                    path=str(path).strip() if path else None,
                    tags=[str(t) for t in tags],
                )
            )
    return out


def pick_repo(config_path: Path | str, *, seed: int | None = None) -> BenchRepoSpec:
    specs = load_bench_allowlist(config_path)
    if not specs:
        raise ValueError(f"No repos in allowlist: {config_path}")
    if seed is not None:
        rng = random.Random(seed)
        return rng.choice(specs)
    return random.choice(specs)


def _run_git(args: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def capture_git_baseline(root: Path) -> dict[str, Any]:
    chk = _run_git(["rev-parse", "--is-inside-work-tree"], root, timeout=10)
    if chk.returncode != 0 or "true" not in (chk.stdout or "").lower():
        return {"git_available": False}
    head = _run_git(["rev-parse", "HEAD"], root, timeout=10)
    st = _run_git(["status", "--porcelain"], root, timeout=10)
    commit = (head.stdout or "").strip() if head.returncode == 0 else ""
    return {
        "git_available": True,
        "baseline_commit": commit,
        "status_porcelain_before": (st.stdout or "").strip()[:8000],
        "git_clean_before": not (st.stdout or "").strip(),
    }


def compute_code_delta(root: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    if not baseline.get("git_available"):
        return {
            "git_available": False,
            "skipped_reason": "not_a_git_repo",
            "diff_stat": "",
            "status_porcelain": "",
            "touched_paths": [],
            "git_clean_after": True,
        }
    st = _run_git(["status", "--porcelain"], root, timeout=30)
    porcelain = (st.stdout or "").strip()
    paths = [ln[3:].strip() for ln in porcelain.splitlines() if len(ln) > 3][:200]
    base_commit = baseline.get("baseline_commit") or ""
    diff_stat = ""
    if base_commit:
        d = _run_git(["diff", "--stat", base_commit, "--"], root, timeout=60)
        diff_stat = ((d.stdout or "") + (d.stderr or "")).strip()[:12000]
    return {
        "git_available": True,
        "baseline_commit": base_commit,
        "status_porcelain": porcelain[:8000],
        "touched_paths": paths,
        "diff_stat": diff_stat,
        "git_clean_after": not porcelain,
    }


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in s).strip("-")[:80] or "repo"


def materialize_repo(
    spec: BenchRepoSpec,
    dest_parent: Path,
    *,
    allow_network: bool,
    timeout_s: int = 180,
) -> Path:
    """Clone ``spec.url`` or copy ``spec.path`` into ``dest_parent/<slug>``."""
    dest_parent.mkdir(parents=True, exist_ok=True)
    if spec.path:
        src = Path(spec.path).expanduser().resolve()
        if not src.is_dir():
            raise FileNotFoundError(f"bench repo path not found: {src}")
        dest = dest_parent / _slug(spec.name)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, symlinks=True, ignore_dangling_symlinks=True)
        return dest
    if not spec.url:
        raise ValueError("BenchRepoSpec needs url or path")
    if not allow_network:
        raise RuntimeError("Network clone disabled (allow_network=False)")
    dest = dest_parent / _slug(spec.name)
    if dest.exists():
        shutil.rmtree(dest)
    cmd = ["git", "clone", "--depth", "1", spec.url, str(dest)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {proc.stderr or proc.stdout}")
    return dest


def seed_ocean_scaffold(root: Path, trace: list[BenchEvent]) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    pj = docs / "project.json"
    if not pj.exists():
        payload = {
            "name": root.name,
            "kind": "cli",
            "description": "Seeded by Ocean bench for scheduler signal.",
            "goals": ["improve quality", "reduce friction", "ship smallest valuable change"],
            "constraints": ["minimal invasive edits"],
            "createdAt": _now_iso(),
        }
        pj.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    prd = docs / "prd.md"
    if not prd.exists():
        prd.write_text(
            "# Bench PRD\n\nImprove tests, documentation, and the smallest user-visible UX win.\n",
            encoding="utf-8",
        )
    _emit(trace, "repo_baseline", "Seeded docs/project.json and/or docs/prd.md if missing", {"root": str(root)})


def _redact_turn_guidance(d: dict[str, Any]) -> dict[str, Any]:
    out = dict(d)
    ap = out.get("advisor_prompt")
    if isinstance(ap, str) and ap:
        out["advisor_prompt"] = ""
        out["advisor_prompt_len"] = len(ap)
        out["advisor_prompt_sha256"] = hashlib.sha256(ap.encode("utf-8")).hexdigest()
    return out


def _run_pytest_workspace(root: Path, trace: list[BenchEvent], timeout_s: int = 90) -> int | None:
    if not shutil.which("pytest"):
        _emit(trace, "pytest_smoke", "pytest not on PATH", {"skipped": True})
        return None
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    _emit(
        trace,
        "pytest_smoke",
        f"pytest exit {proc.returncode}",
        {"exit_code": proc.returncode, "tail": tail_plain(proc.stdout + "\n" + proc.stderr, lines=20)},
    )
    return proc.returncode


def execute_bench_at(
    workspace: Path,
    *,
    output_dir: Path,
    bench_id: str,
    dry_run: bool = False,
    run_codegen: bool = True,
    codegen_timeout: int = 120,
    run_pytest: bool = False,
    report_extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run evidence pipeline inside ``workspace`` (must exist). Writes ``output_dir/bench-{id}.json``."""
    workspace = workspace.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    trace: list[BenchEvent] = []
    llm_rows: list[dict[str, Any]] = []
    codegen_result: dict[str, Any] = {
        "paths_written": [],
        "paths_modified": [],
        "mapping_file_count": 0,
        "skipped_reason": None,
    }
    t0 = time.monotonic()

    baseline = capture_git_baseline(workspace)
    _emit(trace, "repo_baseline", "Captured git baseline", baseline)

    old = Path.cwd()
    os.chdir(workspace)
    try:
        seed_ocean_scaffold(workspace, trace)

        from ocean.backends import get_codegen_backend, get_gemini_model, get_openai_model
        from ocean.core.economy import CoinMint
        from ocean.core.scheduler import PersonaScheduler, load_project_state

        mint = CoinMint(workspace)
        mint.tick()
        state = load_project_state(workspace)
        _emit(
            trace,
            "project_state",
            "Scheduler project state",
            {
                "has_prd": state.has_prd,
                "has_project_json": state.has_project_json,
                "workspace_file_count": len(state.workspace_files),
                "has_tests": state.has_tests,
                "has_html": state.has_html,
                "has_ci": state.has_ci,
            },
        )
        sched = PersonaScheduler()
        noms = sched.nominate_all(state, mint.wallets)
        _emit(
            trace,
            "persona_nominations",
            f"{len(noms)} nominations",
            {"nominations": [asdict(n) for n in noms]},
        )
        session = mint.run_session(noms)
        _emit(
            trace,
            "selected_task",
            f"Session selected {len(session.selected)} task(s)",
            {
                "selected": [asdict(n) for n in session.selected],
                "deferred": [asdict(n) for n in session.deferred],
                "budget_used": session.budget_used,
            },
        )

        try:
            from ocean import proposal_board as pb

            before = pb.list_board(workspace)
            _emit(trace, "proposal_board_snapshot", "Board before publish", before)
            pb.publish_proposal(
                workspace,
                "Moroni",
                {
                    "title": "Bench governance",
                    "rationale": "Automated bench publish for traceability.",
                    "value": "trace",
                    "cost": "low",
                },
            )
            after = pb.list_board(workspace)
            _emit(trace, "proposal_board_snapshot", "Board after Moroni publish", after)
        except Exception as e:
            _emit(trace, "error", "proposal_board failed", {"error": str(e)})

        from ocean import product_loop as pl

        pl.bootstrap_doctrine(workspace)
        summaries = pl.read_doctrine_summary(workspace)
        _emit(
            trace,
            "doctrine_summary_keys",
            "Doctrine files summarized",
            {"keys": sorted(summaries.keys())},
        )
        guidance = pl.next_action(workspace, user_turn="bench", use_advisor=False)
        _emit(trace, "next_action", "Product loop next_action (local scoring)", _redact_turn_guidance(guidance.to_dict()))

        if dry_run or not run_codegen:
            reason = "dry_run" if dry_run else "run_codegen_disabled"
            codegen_result["skipped_reason"] = reason
            llm_rows.append(
                {
                    "backend": get_codegen_backend(workspace),
                    "skipped_reason": reason,
                    "model": None,
                    "duration_ms": 0,
                }
            )
            _emit(trace, "codex_codegen_start", "Codegen skipped", {"reason": reason})
        else:
            if os.getenv("OCEAN_TEST") == "1" or os.getenv("OCEAN_DISABLE_CODEX") in ("1", "true", "True"):
                codegen_result["skipped_reason"] = "test_or_codex_disabled"
                llm_rows.append(
                    {
                        "backend": get_codegen_backend(workspace),
                        "skipped_reason": "OCEAN_TEST or OCEAN_DISABLE_CODEX",
                        "model": None,
                        "duration_ms": 0,
                    }
                )
                _emit(trace, "codex_codegen_start", "Codegen skipped (test env)", {})
            else:
                from ocean import codex_exec

                instruction = (
                    "Ocean automated bench. Add a tiny artifact: return JSON mapping ONLY the path "
                    "'docs/ocean_bench_touch.md' to a short Markdown file (a few lines) stating the bench run "
                    f"time {_now_iso()} and one improvement suggestion for this repo. No other paths."
                )
                suggested = ["docs/ocean_bench_touch.md"]
                _emit(
                    trace,
                    "codex_codegen_start",
                    "Calling generate_files for bench touch",
                    {"suggested_files": suggested},
                )
                t_llm = time.monotonic()
                mapping = codex_exec.generate_files(
                    instruction,
                    suggested,
                    context_file=None,
                    timeout=codegen_timeout,
                    agent="Bench",
                )
                dt_ms = int((time.monotonic() - t_llm) * 1000)
                mode = codex_exec.last_mode()
                backend = get_codegen_backend(workspace)
                model = None
                if backend == "openai_api":
                    model = get_openai_model(workspace)
                elif backend == "gemini_api":
                    model = get_gemini_model(workspace)
                row: dict[str, Any] = {
                    "backend": backend,
                    "codex_last_mode": mode,
                    "duration_ms": dt_ms,
                    "model": model,
                    "success": bool(mapping),
                }
                if not mapping:
                    row["skipped_reason"] = codex_exec.last_error() or "no_mapping_returned"
                llm_rows.append(row)
                written: list[str] = []
                if isinstance(mapping, dict):
                    codegen_result["mapping_file_count"] = len(mapping)
                    root_res = workspace.resolve()
                    for rel, content in mapping.items():
                        rel_s = str(rel).lstrip("/")
                        target = (workspace / rel_s).resolve()
                        if not str(target).startswith(str(root_res) + os.sep) and target != root_res:
                            continue
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(content, encoding="utf-8")
                        written.append(str(target.relative_to(workspace)))
                    codegen_result["paths_written"] = written
                _emit(
                    trace,
                    "codex_codegen_result",
                    "Codegen finished",
                    {"files": len(written), "mapping_keys": list(mapping.keys()) if isinstance(mapping, dict) else []},
                )

        pytest_exit: int | None = None
        if run_pytest:
            pytest_exit = _run_pytest_workspace(workspace, trace)
        else:
            _emit(trace, "pytest_smoke", "pytest not requested", {"skipped": True})

    except Exception as e:
        _emit(trace, "error", "bench pipeline exception", {"error": str(e)})
        raise
    finally:
        os.chdir(old)

    code_delta = compute_code_delta(workspace, baseline)
    duration_s = round(time.monotonic() - t0, 3)
    report: dict[str, Any] = {
        "bench_id": bench_id,
        "workspace": str(workspace),
        "repo_name": workspace.name,
        "baseline_commit": baseline.get("baseline_commit"),
        "duration_s": duration_s,
        "code_delta": code_delta,
        "trace_events": trace,
        "llm_invocations": llm_rows,
        "codegen_result": codegen_result,
        "pytest_exit_code": pytest_exit,
    }
    if report_extras:
        report.update(report_extras)
    json_path = output_dir / f"bench-{bench_id}.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path = output_dir / f"bench-{bench_id}.md"
    md_path.write_text(render_bench_markdown(report), encoding="utf-8")
    return report


def render_bench_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Ocean bench `{report.get('bench_id')}`",
        "",
        f"- **Workspace:** `{report.get('workspace')}`",
        f"- **Duration (s):** {report.get('duration_s')}",
        f"- **Baseline commit:** `{report.get('baseline_commit')}`",
        "",
        "## What mattered (trace)",
        "",
    ]
    for ev in report.get("trace_events") or []:
        if not isinstance(ev, dict):
            continue
        lines.append(f"- **{ev.get('kind')}:** {ev.get('summary')}")
    lines.extend(
        [
            "",
            "## LLM / codegen",
            "",
        ]
    )
    for row in report.get("llm_invocations") or []:
        lines.append(f"- `{row}`")
    cd = report.get("code_delta") or {}
    lines.extend(
        [
            "",
            "## Code delta",
            "",
            "```text",
            (cd.get("diff_stat") or "(empty)")[:4000],
            "```",
            "",
            f"- **Touched paths:** {len(cd.get('touched_paths') or [])}",
            "",
        ]
    )
    return "\n".join(lines)


def network_allowed(explicit_flag: bool) -> bool:
    return explicit_flag or os.getenv("OCEAN_BENCH_NETWORK", "").strip() == "1"


def bench_repo_from_cli(
    *,
    ocean_root: Path,
    output_dir: Path,
    allowlist_path: Path,
    dry_run: bool,
    list_only: bool,
    allow_network_flag: bool,
    repo_url: str | None,
    repo_path: str | None,
    run_codegen: bool,
    run_pytest: bool,
    seed: int | None,
) -> dict[str, Any] | list[BenchRepoSpec]:
    specs = load_bench_allowlist(allowlist_path)
    if list_only:
        return specs
    if repo_path:
        spec = BenchRepoSpec(name=Path(repo_path).name, path=repo_path)
    elif repo_url:
        spec = BenchRepoSpec(name=_slug(repo_url.split("/")[-1].replace(".git", "")), url=repo_url)
    else:
        spec = pick_repo(allowlist_path, seed=seed)
    bench_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if dry_run:
        return {
            "bench_id": bench_id,
            "dry_run": True,
            "would_clone_or_copy": asdict(spec),
            "work_parent": str((ocean_root / "projects" / f"bench-{bench_id}")),
        }
    allow_net = network_allowed(allow_network_flag)
    if spec.url and not allow_net:
        raise RuntimeError(
            "Clone requires network consent: pass --i-understand-network or set OCEAN_BENCH_NETWORK=1"
        )
    work_parent = ocean_root / "projects" / f"bench-{bench_id}"
    work_parent.mkdir(parents=True, exist_ok=True)
    allow_clone = allow_net if spec.url else True
    workspace = materialize_repo(spec, work_parent, allow_network=allow_clone)
    report = execute_bench_at(
        workspace,
        output_dir=output_dir,
        bench_id=bench_id,
        dry_run=False,
        run_codegen=run_codegen,
        run_pytest=run_pytest,
        report_extras={"bench_spec": asdict(spec)},
    )
    return report

