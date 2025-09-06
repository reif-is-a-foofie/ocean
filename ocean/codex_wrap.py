from __future__ import annotations

import os
import shutil
import sys
import threading
import time
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.text import Text
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.widgets import TextArea
import re
import subprocess

ROOT = Path.cwd()
LOGS = ROOT / "logs"


def banner() -> str:
    return "\n🌊 Ocean Chat — simple feed. Type /exit to quit.\n"


EMOJI: Dict[str, str] = {
    "Ocean": "🌊",
    # Team identities
    "Moroni": "🕹️",  # Architect / Brain
    "Q": "🔫",        # Backend Engineer (squirt gun)
    "Edna": "🍩",     # UI/UX Engineer
    "Mario": "🍄",    # DevOps
    "Tony": "🚀",     # Experimenter / Test Pilot
}


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")

FEED: List[dict] = []
console = Console()
_TASK_STATUS: Dict[Tuple[str, str], str] = {}
_TASK_INTENT: Dict[Tuple[str, str], str] = {}
_TASK_ORDER: List[Tuple[str, str]] = []
_PHASE_ENDED: Dict[str, bool] = {}
_ALL_DONE_POSTED: bool = False
_UI_OUTPUT: TextArea | None = None

def _typewriter_print(text: str) -> None:
    import os
    import sys
    import time
    tw_env = os.getenv("OCEAN_TYPEWRITER")
    tw = True if tw_env is None else (tw_env in ("1", "true", "True"))
    if os.getenv("OCEAN_TEST") == "1":
        tw = False
    delay = 0.025
    try:
        delay = float(os.getenv("OCEAN_TYPEWRITER_DELAY", "0.025"))
    except Exception:
        pass
    human = os.getenv("OCEAN_TYPEWRITER_HUMAN", "1") not in ("0", "false", "False")
    var = float(os.getenv("OCEAN_TW_VARIANCE", "0.6"))
    punct_mult = float(os.getenv("OCEAN_TW_PUNCT_MULT", "4.0"))
    comma_mult = float(os.getenv("OCEAN_TW_COMMA_MULT", "2.0"))
    space_mult = float(os.getenv("OCEAN_TW_SPACE_MULT", "0.3"))
    max_delay = float(os.getenv("OCEAN_TW_MAX_DELAY", "0.12"))
    if tw and sys.stdout.isatty() and delay > 0:
        try:
            for ch in text:
                sys.stdout.write(ch)
                sys.stdout.flush()
                if ch != "\n":
                    if human:
                        mult = 1.0
                        if ch == ' ':
                            mult = space_mult
                        elif ch in '.!?':
                            mult = punct_mult
                        elif ch in ',;:':
                            mult = comma_mult
                        import random as _rand
                        jitter = 1.0 + _rand.uniform(-var, var)
                        d = min(max(delay * mult * jitter, 0.0), max_delay)
                        if d > 0:
                            time.sleep(d)
                    else:
                        time.sleep(delay)
            if not text.endswith("\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
            return
        except Exception:
            pass
    console.print(text)


def _append(author: str, text: str) -> None:
    msg = {
        "time": _now(),
        "author": author,
        "emoji": EMOJI.get(author, "💬"),
        "text": text,
    }
    FEED.append(msg)
    # Incremental print: update UI if present; else print to console
    line = f"[{msg['time']}] {msg['emoji']} {msg['author']}: "
    short = msg['text'] if ("http://" in msg['text'] or "https://" in msg['text']) else (msg['text'][:49] + ('…' if len(msg['text'])>50 else ''))
    if _UI_OUTPUT is not None:
        try:
            app = get_app()
            def _do():
                _UI_OUTPUT.buffer.insert_text(line + short + "\n")
                _UI_OUTPUT.buffer.cursor_position = len(_UI_OUTPUT.buffer.text)
            app.call_from_executor(_do)
        except Exception:
            console.print(line + short)
    else:
        _typewriter_print(line + short)

def _format_with_links(text: str) -> Text:
    # Detect URLs and style them as clickable links
    url_re = re.compile(r"https?://[^\s]+")
    out = Text()
    last = 0
    for m in url_re.finditer(text):
        if m.start() > last:
            out.append(text[last:m.start()])
        url = m.group(0)
        out.append(url, style=f"link {url}")
        last = m.end()
    if last < len(text):
        out.append(text[last:])
    return out

def _render() -> None:
    # Legacy full redraw (unused). Kept for reference.
    for m in FEED[-200:]:
        prefix = Text(f"[{m['time']}] {m['emoji']} {m['author']}: ")
        body = _format_with_links(m['text'])
        prefix.append_text(body)
        console.print(prefix)

def _format_event_for_feed(ev: dict) -> tuple[str, str] | None:
    kind = ev.get("event")
    agent = ev.get("agent", "?")
    title = ev.get("title")
    if kind == "phase_start":
        cnt = ev.get("count", "?")
        return agent, f"▶ phase start — {cnt} task(s)"
    if kind == "task_start":
        return agent, f"✳ start — {title}"
    if kind == "task_end":
        return agent, f"✓ done — {title}"
    if kind == "phase_end":
        return agent, "■ phase end"
    return None


def _update_task_registry(ev: dict) -> bool:
    """Update in-memory task state. Returns True if there was a visible change."""
    global _ALL_DONE_POSTED
    kind = ev.get("event")
    agent = ev.get("agent", "?")
    title = (ev.get("title") or "").strip()
    changed = False
    if kind == "task_start" and title:
        key = (agent, title)
        if key not in _TASK_STATUS:
            _TASK_ORDER.append(key)
        if _TASK_STATUS.get(key) != "in progress":
            _TASK_STATUS[key] = "in progress"
            changed = True
        intent = (ev.get("intent") or "").strip()
        if intent:
            _TASK_INTENT[key] = intent
    elif kind == "task_end" and title:
        key = (agent, title)
        if key not in _TASK_STATUS:
            _TASK_ORDER.append(key)
        if _TASK_STATUS.get(key) != "done":
            _TASK_STATUS[key] = "done"
            changed = True
        intent = (ev.get("intent") or "").strip()
        if intent and not _TASK_INTENT.get(key):
            _TASK_INTENT[key] = intent
    elif kind == "phase_end":
        _PHASE_ENDED[agent] = True
        changed = True

    # Reset final flag if any new activity starts
    if kind == "task_start":
        _ALL_DONE_POSTED = False
    return changed


def _post_task_snapshot_if_needed() -> None:
    """Emit a compact snapshot of current tasks and final wrap when complete."""
    global _ALL_DONE_POSTED
    if not _TASK_ORDER:
        return
    # Build snapshot grouped by agent, preserving insertion order
    grouped: Dict[str, List[Tuple[str, str]]] = {}
    for agent, title in _TASK_ORDER:
        status = _TASK_STATUS.get((agent, title), "in progress")
        grouped.setdefault(agent, []).append((title, status))

    lines: List[str] = ["Current tasks"]
    for agent, items in grouped.items():
        for i, (title, status) in enumerate(items):
            prefix = f"{EMOJI.get(agent, '👥')} {agent} — " if i == 0 else " " * (len(agent) + 4)
            key = (agent, title)
            why = _TASK_INTENT.get(key)
            if why:
                # keep intent concise for the feed
                short = why if len(why) <= 120 else (why[:117] + "…")
                lines.append(f"  {prefix}{title} ({status}) — {short}")
            else:
                lines.append(f"  {prefix}{title} ({status})")
    _append("Ocean", "\n".join(lines))

    # Final wrap-up when all tasks are done and at least one phase ended
    if (not any(st == "in progress" for st in _TASK_STATUS.values())) and _PHASE_ENDED and not _ALL_DONE_POSTED:
        _ALL_DONE_POSTED = True
        _append("Ocean", "✅ All tasks complete.")


def run(argv: List[str] | None = None) -> int:
    """Run a simple CLI feed with input at bottom; stream Codex + team events."""
    argv = list(argv or [])
    # Disable CPR (cursor position requests) to avoid stray escape codes on macOS Terminal
    os.environ.setdefault("PROMPT_TOOLKIT_NO_CPR", "1")
    codex = shutil.which("codex")
    if not codex:
        sys.stderr.write("Codex CLI not found. Install with: brew install codex\n")
        return 127

    # Allow non-UI stream mode without a TTY
    stream_mode = os.getenv("OCEAN_NO_UI") in ("1", "true", "True")
    if (not sys.stdin.isatty() or not sys.stdout.isatty()) and not stream_mode:
        sys.stdout.write("[Ocean] Feed requires a real terminal (TTY). Run in Terminal/iTerm, or use --no-ui.\n")
        return 2

    # Spawn codex chat as a subprocess with pipes for feed integration
    proc = subprocess.Popen(
        [codex, "chat", *argv],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    stop = threading.Event()
    if stream_mode:
        console.print("🌊 Ocean Feed")
        _append("Ocean", "Init: loading personas & context…")
        _append("Ocean", "Init: starting Codex chat…")
        _append("Ocean", "Init: queuing build (autostart)…")
        _append("Ocean", "Init: queuing repo-scout…")
    # Build minimal full-screen UI: scrollable feed + pinned input
    output = TextArea(style="class:output", text="🌊 Ocean Feed\n", read_only=True, scrollbar=True, wrap_lines=True)
    input_field = TextArea(height=1, prompt="You> ", multiline=False)
    kb = KeyBindings()

    @kb.add("enter")
    def _(event):
        text = input_field.text.strip()
        input_field.buffer.reset()
        if not text:
            return
        _append("You", text)
        if text in {"/exit", ":q", ":quit", ":exit"}:
            try:
                if proc.stdin:
                    proc.stdin.write("/exit\n")
                    proc.stdin.flush()
            except Exception:
                pass
            event.app.exit(result=0)
            return
        if text in {"/continue", ":continue", "/resume"}:
            # Touch logs/continue to signal Ocean loop
            try:
                (LOGS).mkdir(parents=True, exist_ok=True)
                (LOGS / "continue").write_text("ok", encoding="utf-8")
                _append("Ocean", "Continue signal sent to build loop.")
            except Exception:
                pass
            return
        try:
            if proc.stdin:
                proc.stdin.write(text + "\n")
                proc.stdin.flush()
        except Exception:
            event.app.exit(result=0)

    layout = Layout(HSplit([output, Window(height=1, char="-"), input_field]))
    app = None
    if not stream_mode:
        app = Application(layout=layout, key_bindings=kb, full_screen=True)
        # Extra guard: mark output as non-CPR if supported by this prompt_toolkit version
        try:
            out = getattr(app, "output", None)
            if out is not None and hasattr(out, "responds_to_cpr"):
                setattr(out, "responds_to_cpr", False)
        except Exception:
            pass
        # Register UI output for _append
        global _UI_OUTPUT
        _UI_OUTPUT = output
        # Verbose startup (single-line, under 50 chars)
        _append("Ocean", "Init: loading personas & context…")
        _append("Ocean", "Init: starting Codex chat…")
        _append("Ocean", "Init: queuing build (autostart)…")
        _append("Ocean", "Init: queuing repo-scout…")

    def reader_loop():
        if not proc.stdout:
            return
        for line in iter(proc.stdout.readline, ""):
            s = line.rstrip("\n")
            if s:
                _append("Ocean", s)
        try:
            proc.stdout.close()
        except Exception:
            pass

    def _find_latest_events() -> Path | None:
        try:
            latest = None
            for p in LOGS.glob("events-*.jsonl"):
                if (not latest) or p.stat().st_mtime > latest.stat().st_mtime:
                    latest = p
            return latest
        except Exception:
            return None

    def events_loop():
        last_pos = 0
        current: Path | None = None
        while not stop.is_set():
            p = _find_latest_events()
            if not p:
                time.sleep(0.8)
                continue
            if p != current:
                current = p
                last_pos = 0
            try:
                with open(current, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(last_pos)
                    for raw in f.readlines()[-400:]:
                        try:
                            import json as _json
                            ev = _json.loads(raw)
                        except Exception:
                            continue
                        ft = _format_event_for_feed(ev)
                        if ft:
                            who, txt = ft
                            _append(who, txt)
                        if ev.get("event") == "note":
                            t = ev.get("title") or ""
                            _append(ev.get("agent", "Ocean"), t)
                        # Runtime hints (URLs and quick tests)
                        if ev.get("event") == "runtime":
                            urls = ev.get("urls") or []
                            if isinstance(urls, list):
                                for u in urls:
                                    _append("Ocean", f"Runtime: {u}")
                                    if isinstance(u, str) and u.endswith("/healthz"):
                                        _append("Ocean", f"Test: curl -fsSL {u} | jq")
                            _append("Ocean", "Tip: open the UI link in your browser; use the health URL to verify the backend.")
                        if _update_task_registry(ev):
                            _post_task_snapshot_if_needed()
                    last_pos = f.tell()
            except Exception:
                pass
            time.sleep(0.8)

    t_out = threading.Thread(target=reader_loop, daemon=True)
    t_out.start()
    t_evt = threading.Thread(target=events_loop, daemon=True)
    t_evt.start()

    # Autostart continuous orchestration and repo-scout to begin chatter immediately (fire-and-forget)
    try:
        # Continuous loop: never exits; emits events for the REPL
        subprocess.Popen([sys.executable, "-m", "ocean.cli", "loop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen([sys.executable, "-m", "ocean.cli", "scout"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        if app is not None:
            return app.run()
        # Stream mode: keep running until Codex chat exits or user sends /exit
        return proc.wait()
    finally:
        stop.set()
        try:
            t_out.join(timeout=1.0)
            t_evt.join(timeout=1.0)
        except Exception:
            pass
        try:
            proc.terminate()
        except Exception:
            pass
        try:
            proc.wait(timeout=2)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
