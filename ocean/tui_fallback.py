from __future__ import annotations

import curses
import json
import os
import threading
import time
from pathlib import Path
from typing import List

ROOT = Path.cwd()
DOCS = ROOT / "docs"
LOGS = ROOT / "logs"


class State:
    def __init__(self) -> None:
        self.chat: List[str] = ["🌊 Ocean Python TUI — q to quit • r to reload • : for commands"]
        self.backlog: List[str] = ["(no backlog)"]
        self.team: List[str] = ["(no team events)"]
        self.logs: List[str] = []
        self.approvals: List[str] = []
        self.status: str = "Ready"
        self.cmd_mode: bool = False
        self.input_buf: str = ""
        self.lock = threading.Lock()
        self.running = True

    def append_chat(self, line: str) -> None:
        with self.lock:
            self.chat.append(line)

    def set_status(self, s: str) -> None:
        with self.lock:
            self.status = s


def _safe_read(path: Path, limit: int = 200_000) -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""
    return ""


def load_backlog(st: State) -> None:
    data_path = DOCS / "backlog.json"
    lines: List[str] = []
    try:
        raw = _safe_read(data_path)
        if raw:
            arr = json.loads(raw)
            for t in arr[:100]:
                owner = t.get("owner", "?")
                title = t.get("title", "(untitled)")
                lines.append(f"[{owner}] {title}")
    except Exception:
        lines = []
    with st.lock:
        st.backlog = lines or ["(no backlog)"]


def tail_logs(st: State) -> None:
    # Best effort: display the last ~200 lines of most recent session log
    while st.running:
        latest = None
        try:
            if LOGS.exists():
                for p in LOGS.glob("session-*.log"):
                    if (not latest) or p.stat().st_mtime > latest.stat().st_mtime:
                        latest = p
        except Exception:
            latest = None
        lines: List[str] = []
        if latest:
            try:
                text = _safe_read(latest)
                if text:
                    lines = text.splitlines()[-200:]
            except Exception:
                lines = []
        approvals = [l for l in lines if ("[ASK]" in l) or ("[APPROVAL]" in l)]
        with st.lock:
            st.logs = lines
            st.approvals = approvals
        time.sleep(1.2)


def _find_latest_events() -> Path | None:
    try:
        latest = None
        for p in LOGS.glob("events-*.jsonl"):
            if (not latest) or p.stat().st_mtime > latest.stat().st_mtime:
                latest = p
        return latest
    except Exception:
        return None


def tail_events(st: State) -> None:
    # Parse structured events from logs/events-*.jsonl and show team chatter
    last_pos = 0
    current_file: Path | None = None
    while st.running:
        p = _find_latest_events()
        if not p:
            time.sleep(1.0)
            continue
        if current_file != p:
            current_file = p
            last_pos = 0
        lines: List[str] = []
        try:
            with open(current_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(last_pos)
                for raw in f.readlines()[-400:]:
                    try:
                        import json as _json
                        ev = _json.loads(raw)
                    except Exception:
                        continue
                    kind = ev.get("event")
                    agent = ev.get("agent", "?")
                    title = ev.get("title")
                    if kind == "phase_start":
                        cnt = ev.get("count", "?")
                        lines.append(f"[{agent}] ▶ phase start — {cnt} task(s)")
                    elif kind == "task_start":
                        lines.append(f"[{agent}] ✳ start — {title}")
                    elif kind == "task_end":
                        lines.append(f"[{agent}] ✓ done — {title}")
                    elif kind == "phase_end":
                        lines.append(f"[{agent}] ■ phase end")
                last_pos = f.tell()
        except Exception:
            lines = []
        if lines:
            with st.lock:
                st.team = (st.team + lines)[-200:]
        time.sleep(0.8)


def draw(stdscr, st: State) -> None:
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    # Layout: sidebar 24 cols | main flex | team 30 cols
    left_w = 24
    right_w = 30
    input_h = 3
    logs_h = 5
    main_w = max_x - left_w - right_w - 2
    main_h = max_y - input_h - logs_h - 2

    def box(y, x, h, w, title: str = ""):
        try:
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(y, x, "+" + "-" * (w - 2) + "+")
            for i in range(1, h - 1):
                stdscr.addstr(y + i, x, "|")
                stdscr.addstr(y + i, x + w - 1, "|")
            stdscr.addstr(y + h - 1, x, "+" + "-" * (w - 2) + "+")
            if title:
                stdscr.addstr(y, x + 2, f" {title} ", curses.A_REVERSE)
            stdscr.attroff(curses.A_BOLD)
        except curses.error:
            pass

    with st.lock:
        chat = list(st.chat)[- (main_h - 2):]
        backlog = list(st.backlog)[: (main_h - 2)]
        queues = ["Codex Queue: idle", "Ocean Queue: idle"]
        approvals = list(st.approvals)[- (main_h - 6):]
        logs = list(st.logs)[- (logs_h - 2):]
        status = st.status
        cmd_prompt = ": " + st.input_buf if st.cmd_mode else ": (press : to command)"

    # Sidebar
    box(0, 0, main_h, left_w, "Queues")
    y = 1
    for q in queues:
        try:
            stdscr.addstr(y, 2, q[: left_w - 4])
        except curses.error:
            pass
        y += 1
    if approvals:
        y += 1
        try:
            stdscr.addstr(y, 2, "Approvals:")
        except curses.error:
            pass
        y += 1
        for a in approvals:
            if y >= main_h - 1:
                break
            try:
                stdscr.addstr(y, 2, a[: left_w - 4])
            except curses.error:
                pass
            y += 1

    # Chat
    box(0, left_w + 1, main_h, main_w, "Chat")
    y = 1
    for line in chat:
        if y >= main_h - 1:
            break
        try:
            stdscr.addstr(y, left_w + 3, line[: main_w - 4])
        except curses.error:
            pass
        y += 1

    # Team chatter
    box(0, left_w + 1 + main_w + 1, main_h, right_w, "Team")
    y = 1
    for b in st.team:
        if y >= main_h - 1:
            break
        try:
            stdscr.addstr(y, left_w + 1 + main_w + 3, b[: right_w - 4])
        except curses.error:
            pass
        y += 1

    # Input
    box(main_h, 0, input_h, max_x, "Input")
    try:
        stdscr.addstr(main_h + 1, 2, cmd_prompt[: max_x - 4])
    except curses.error:
        pass

    # Logs
    box(main_h + input_h, 0, logs_h, max_x, "Logs")
    y = main_h + input_h + 1
    for l in logs:
        try:
            stdscr.addstr(y, 2, l[: max_x - 4])
        except curses.error:
            pass
        y += 1

    # Status (append at end)
    try:
        stdscr.addstr(max_y - 1, 2, ("Status: " + status)[: max_x - 4], curses.A_DIM)
    except curses.error:
        pass

    stdscr.refresh()


def handle_command(cmd: str, st: State) -> None:
    c = cmd.strip()
    if not c:
        return
    if c == "help":
        st.append_chat("Commands: help • reload • status • prd: <text> • q")
        st.append_chat("Build flows require Codex and should be run from shell: 'ocean chat'")
        return
    if c in {"r", "reload"}:
        load_backlog(st)
        st.append_chat("Backlog reloaded.")
        return
    if c == "status":
        st.append_chat("Status: tui-fallback active • logs/backlog monitored")
        return
    if c.startswith("prd:"):
        text = c.split(":", 1)[1].strip()
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "prd.md").write_text(text + "\n", encoding="utf-8")
        st.append_chat("PRD updated: docs/prd.md")
        return
    if c in {"q", "quit", "exit"}:
        st.running = False
        return
    st.append_chat(f"Unknown command: {c}")


def run() -> int:
    st = State()
    LOGS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    load_backlog(st)

    t_logs = threading.Thread(target=tail_logs, args=(st,), daemon=True)
    t_logs.start()
    t_events = threading.Thread(target=tail_events, args=(st,), daemon=True)
    t_events.start()

    def _loop(stdscr):
        # Safer input/display settings
        curses.noecho()
        curses.cbreak()
        try:
            curses.curs_set(0)
        except Exception:
            pass
        stdscr.keypad(True)
        stdscr.timeout(120)  # block up to 120ms for input; reduces redraw churn
        last = 0.0
        while st.running:
            now = time.time()
            if now - last > 0.25:  # redraw at ~4 FPS maximum
                draw(stdscr, st)
                last = now
            try:
                ch = stdscr.getch()
            except Exception:
                ch = -1
            if ch == -1:
                continue
            if ch in (ord('q'), ord('Q')) and not st.cmd_mode:
                st.running = False
                break
            if ch == ord(':') and not st.cmd_mode:
                st.cmd_mode = True
                st.input_buf = ""
                continue
            if st.cmd_mode:
                if ch in (curses.KEY_ENTER, 10, 13):
                    cmd = st.input_buf
                    st.input_buf = ""
                    st.cmd_mode = False
                    handle_command(cmd, st)
                elif ch in (27,):  # ESC
                    st.cmd_mode = False
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    st.input_buf = st.input_buf[:-1]
                else:
                    try:
                        st.input_buf += chr(ch)
                    except Exception:
                        pass
        return 0

    return curses.wrapper(_loop)


if __name__ == "__main__":
    raise SystemExit(run())
