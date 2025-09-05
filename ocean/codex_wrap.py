from __future__ import annotations

import os
import shutil
import sys
import threading
import time
from typing import Dict, List
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
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

def _append(author: str, text: str) -> None:
    FEED.append({
        "time": _now(),
        "author": author,
        "emoji": EMOJI.get(author, "💬"),
        "text": text,
    })
    _render()

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
    console.clear()
    console.print("🌊 Ocean Feed")
    for m in FEED[-200:]:
        prefix = Text(f"[{m['time']}] {m['emoji']} {m['author']}: ")
        body = _format_with_links(m['text'])
        prefix.extend(body)
        console.print(prefix)
    console.print("")

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


def run(argv: List[str] | None = None) -> int:
    """Run a simple CLI feed with input at bottom; stream Codex + team events."""
    argv = list(argv or [])
    codex = shutil.which("codex")
    if not codex:
        sys.stderr.write("Codex CLI not found. Install with: brew install codex\n")
        return 127

    # Require a real TTY for interactive feed
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        sys.stdout.write("[Ocean] Feed requires a real terminal (TTY). Run in Terminal/iTerm.\n")
        return 2

    import pty, select

    # Spawn codex chat in a PTY so we can feed input and capture output
    master, slave = pty.openpty()
    pid = os.fork()
    if pid == 0:
        try:
            os.setsid()
        except Exception:
            pass
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        try:
            os.close(master)
            os.close(slave)
        except Exception:
            pass
        os.execvp(codex, ["codex", "chat", *argv])
        os._exit(127)

    # Parent
    try:
        os.close(slave)
    except Exception:
        pass

    stop = threading.Event()
    _append("Ocean", "Chat started. I’ll orchestrate and keep this feed updated.")

    def reader_loop():
        buf = b""
        while not stop.is_set():
            r, _, _ = select.select([master], [], [], 0.1)
            if master in r:
                try:
                    data = os.read(master, 4096)
                except OSError:
                    break
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        s = line.decode(errors="ignore").rstrip()
                    except Exception:
                        s = ""
                    if s:
                        _append("Ocean", s)
        if buf:
            try:
                s = buf.decode(errors="ignore").strip()
            except Exception:
                s = ""
            if s:
                _append("Ocean", s)

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
                    last_pos = f.tell()
            except Exception:
                pass
            time.sleep(0.8)

    t_out = threading.Thread(target=reader_loop, daemon=True)
    t_out.start()
    t_evt = threading.Thread(target=events_loop, daemon=True)
    t_evt.start()

    session = PromptSession()
    # Autostart orchestration to begin chatter immediately (fire-and-forget)
    try:
        subprocess.Popen([sys.executable, "-m", "ocean.cli", "autostart"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        with patch_stdout(raw=True):
            while True:
                try:
                    text = session.prompt("You> ")
                except (EOFError, KeyboardInterrupt):
                    text = "/exit"
                msg = text.strip()
                if not msg:
                    continue
                _append("You", msg)
                if msg in {"/exit", ":q", ":quit", ":exit"}:
                    try:
                        os.write(master, ("/exit\n").encode())
                    except Exception:
                        pass
                    break
                try:
                    os.write(master, (msg + "\n").encode())
                except Exception:
                    break
    finally:
        stop.set()
        try:
            t_out.join(timeout=1.0)
            t_evt.join(timeout=1.0)
        except Exception:
            pass
        try:
            os.close(master)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
