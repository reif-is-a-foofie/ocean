from __future__ import annotations

import base64
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .actors import load_actors
from .advisor import ask_chat_advisor
from .product_loop import DOCTRINE_FILES, collect_build_context, read_doctrine_summary, record_feedback, turn


def product_chat(
    project_root: str | Path,
    message: str,
    *,
    screenshots: list[dict[str, str]] | None = None,
    test_notes: str = "",
    update_feedback: bool = False,
    use_advisor: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"project_root does not exist: {root}")

    saved_screenshots = save_screenshots(root, screenshots or [])
    referenced_files = read_referenced_files(root, message)
    file_updates = apply_chat_file_updates(root, message)
    feedback_result = None
    if update_feedback and message.strip():
        feedback_result = record_feedback(root, message, test_context=test_notes or None)

    payload = {
        "project_root": str(root),
        "message": message.strip(),
        "test_notes": test_notes.strip(),
        "screenshots": saved_screenshots,
        "referenced_files": referenced_files,
        "file_updates": file_updates,
        "actors": load_actors(root),
        "doctrine_summary": read_doctrine_summary(root),
        "build_context": collect_build_context(root),
        "recent_chat": recent_chat(root),
    }
    prompt = build_product_chat_prompt(payload)
    advisor = ask_chat_advisor(prompt, cwd=root) if use_advisor else None
    response = _fallback_response(payload) if advisor is None else advisor.text
    if file_updates:
        updated = ", ".join(update["path"] for update in file_updates)
        response = f"Updated {updated}.\n\n{response}"

    loop_result = None
    job_plan = None
    if _looks_like_next_action_request(message):
        loop_result = turn(
            root,
            user_turn=message,
            feedback=message if update_feedback else "",
            test_results=test_notes,
            use_advisor=use_advisor,
        )
        try:
            from .jobs import plan_jobs

            job_plan = plan_jobs(root, user_turn=message, test_results=test_notes, use_advisor=use_advisor)
        except Exception:
            job_plan = None

    team_messages = build_team_messages(payload, response=response, job_plan=job_plan)

    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "message": message,
        "response": response,
        "screenshots": saved_screenshots,
        "test_notes": test_notes,
        "file_updates": file_updates,
        "team_messages": team_messages,
        "job_plan": job_plan,
        "advisor": advisor.__dict__ if advisor else None,
    }
    append_chat(root, entry)
    return {
        "project_root": str(root),
        "response": response,
        "screenshots": saved_screenshots,
        "file_updates": file_updates,
        "advisor": advisor.__dict__ if advisor else None,
        "advisor_prompt": prompt,
        "feedback_result": feedback_result,
        "loop_result": loop_result,
        "job_plan": job_plan,
        "team_messages": team_messages,
        "chat_entry": entry,
    }


def build_product_chat_prompt(payload: dict[str, Any]) -> str:
    return (
        "You are Ocean's product conversation advisor for an agentic coding workflow.\n\n"
        "The user is testing work in motion. Help them reason about product value, screenshots, behavior, "
        "feedback, and the next smallest useful change. Do not act like a terminal. Use plain assistant language.\n\n"
        "If screenshots are present, use the file paths and the user's notes. If your runtime cannot inspect images, "
        "say what you can infer from the notes and ask for the missing visual detail.\n\n"
        "When useful, return:\n"
        "- a direct answer to the user's question\n"
        "- what this implies for product doctrine\n"
        "- the next test the user should run\n"
        "- the next highest-value task for the coding agent\n\n"
        "Context JSON:\n"
        + json.dumps(payload, indent=2, sort_keys=True)
    )


def build_team_messages(
    payload: dict[str, Any],
    *,
    response: str,
    job_plan: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    actors = {actor["id"]: actor for actor in payload.get("actors") or []}
    screenshots = payload.get("screenshots") or []
    updates = payload.get("file_updates") or []
    referenced = payload.get("referenced_files") or []
    jobs = (job_plan or {}).get("jobs") or []
    first_job = jobs[0] if jobs else None

    def actor_message(actor_id: str, body: str, *, artifacts: list[dict[str, str]] | None = None) -> dict[str, Any]:
        actor = actors.get(actor_id, {"id": actor_id, "name": actor_id.title(), "role": "Agent", "phase": "build"})
        return {
            "actor_id": actor["id"],
            "actor_name": actor["name"],
            "role": actor["role"],
            "phase": actor.get("phase") or "build",
            "body": body,
            "artifacts": artifacts or [],
        }

    artifacts: list[dict[str, str]] = []
    for shot in screenshots:
        artifacts.append({"kind": "screenshot", "label": shot.get("name") or "Screenshot", "path": shot.get("path") or ""})
    for update in updates:
        artifacts.append({"kind": "file", "label": update["path"], "path": update["path"]})
    for ref in referenced[:3]:
        artifacts.append({"kind": "file", "label": ref["path"], "path": ref["path"]})

    captain_body = (
        f"I am turning this into one handoff: {first_job['title']}."
        if first_job
        else "I captured the product signal. If nobody redirects us, the next move is to pick the smallest useful build step and hand it to the coding tool."
    )
    scrooge_body = "Benefit check: this should reduce setup friction, increase trust, or make the demo easier to sell. Anything else waits."
    edna_body = (
        f"I have {len(screenshots)} screenshot artifact(s) to judge the experience from."
        if screenshots
        else "I am watching for plain-language setup, visible progress, and a first run that feels obvious without a manual."
    )
    q_body = (
        f"I can give Cursor this discrete job now: {first_job['cursor_prompt']}"
        if first_job
        else "I am waiting for a scoped job, then I will keep the implementation small and repo-native."
    )
    mario_body = (
        "Ship check: after the job lands, I want a local run, a screenshot or demo link, and the exact command that proves it works."
    )

    return [
        actor_message("captain", captain_body, artifacts=artifacts),
        actor_message("scrooge", scrooge_body),
        actor_message("edna", edna_body),
        actor_message("q", q_body),
        actor_message("mario", mario_body),
    ]


def save_screenshots(root: Path, screenshots: list[dict[str, str]]) -> list[dict[str, str]]:
    saved: list[dict[str, str]] = []
    target = root / ".ocean" / "screenshots"
    target.mkdir(parents=True, exist_ok=True)
    for index, shot in enumerate(screenshots):
        data_url = (shot.get("data_url") or "").strip()
        if not data_url:
            continue
        match = re.match(r"data:(image/[a-zA-Z0-9.+-]+);base64,(.*)", data_url, re.DOTALL)
        if not match:
            continue
        mime, raw = match.groups()
        ext = {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/webp": "webp",
            "image/gif": "gif",
        }.get(mime, "png")
        name = _clean_name(shot.get("name") or f"screenshot-{index + 1}.{ext}")
        if "." not in name:
            name = f"{name}.{ext}"
        path = target / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{name}"
        path.write_bytes(base64.b64decode(raw))
        saved.append(
            {
                "name": shot.get("name") or name,
                "path": str(path.relative_to(root)),
                "mime": mime,
                "note": shot.get("note") or "",
            }
        )
    return saved


def recent_chat(root: Path, limit: int = 8) -> list[dict[str, Any]]:
    path = root / ".ocean" / "chat.jsonl"
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            data = json.loads(line)
        except Exception:
            continue
        if isinstance(data, dict):
            entries.append(data)
    return entries


def read_referenced_files(root: Path, message: str, *, limit: int = 5) -> list[dict[str, str]]:
    refs = []
    for match in re.findall(r"@([A-Za-z0-9_./-]+)", message):
        if len(refs) >= limit:
            break
        path = (root / match).resolve()
        if root not in path.parents or not path.is_file():
            continue
        if path.stat().st_size > 80_000:
            refs.append({"path": match, "content": "(file too large to include)"})
            continue
        refs.append({"path": match, "content": path.read_text(encoding="utf-8", errors="replace")})
    return refs


def apply_chat_file_updates(root: Path, message: str) -> list[dict[str, str]]:
    updates: list[dict[str, str]] = []
    allowed = {name.lower(): name for name in DOCTRINE_FILES}
    allowed.update({name.removesuffix(".md").lower(): name for name in DOCTRINE_FILES})

    # Examples:
    # update vision: ...
    # set VISION.md to ...
    # append to TASKS.md: ...
    patterns = [
        (r"(?is)\b(?:update|set|rewrite)\s+([A-Z_]+(?:\.md)?)\s*(?:to|:|-)\s*(.+)", "replace"),
        (r"(?is)\b(?:append|add)\s+(?:to\s+)?([A-Z_]+(?:\.md)?)\s*(?:to|:|-)\s*(.+)", "append"),
    ]
    for pattern, mode in patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        raw_name, body = match.groups()
        key = raw_name.strip().lower()
        name = allowed.get(key) or allowed.get(key.removesuffix(".md"))
        if not name:
            continue
        body = body.strip()
        if not body:
            continue
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "replace":
            content = _with_heading(name, body)
            path.write_text(content, encoding="utf-8")
        else:
            existing = path.read_text(encoding="utf-8") if path.exists() else f"# {name.removesuffix('.md').replace('_', ' ').title()}\n"
            path.write_text(existing.rstrip() + "\n\n" + body + "\n", encoding="utf-8")
        updates.append({"path": name, "mode": mode})
        break
    return updates


def _with_heading(name: str, body: str) -> str:
    if body.lstrip().startswith("#"):
        return body.rstrip() + "\n"
    title = name.removesuffix(".md").replace("_", " ").title()
    return f"# {title}\n\n{body.rstrip()}\n"


def append_chat(root: Path, entry: dict[str, Any]) -> None:
    path = root / ".ocean" / "chat.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _fallback_response(payload: dict[str, Any]) -> str:
    message = payload.get("message") or ""
    screenshots = payload.get("screenshots") or []
    return (
        "I captured this product conversation locally. No reasoning CLI is configured, so I prepared "
        "an advisor prompt for Cursor or Codex to answer with its own model.\n\n"
        f"Message: {message}\n"
        f"Screenshots attached: {len(screenshots)}\n\n"
        "Configure `OCEAN_CHAT_ADVISOR_CMD` or `OCEAN_CHAT_ADVISOR=codex` to have Ocean call a local reasoning engine directly."
    )


def _looks_like_next_action_request(message: str) -> bool:
    text = message.lower()
    return any(phrase in text for phrase in ["next", "build", "feature", "task", "roadmap", "prioritize"])


def _clean_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return cleaned or "screenshot.png"
