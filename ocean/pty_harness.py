"""Run Ocean (or any command) under a real PTY — for integration tests and local smoke.

Plain subprocess is not a TTY, so launcher / Rich prompts behave differently. Use this when
you need **isatty() == True** without a human terminal (CI, Cursor agent shell, etc.).
"""

from __future__ import annotations

import errno
import os
import pty
import re
import select
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


@dataclass
class PtyResult:
    output: str
    exit_code: int | None
    timed_out: bool


def _wait_for_regex(
    master_fd: int,
    *,
    pattern: re.Pattern[str] | None,
    deadline_s: float,
    idle_after_data_s: float = 0.35,
    max_bytes: int = 512_000,
) -> tuple[bytes, bool]:
    """Accumulate PTY output until ``pattern`` matches (on ANSI-stripped decode), idle, EOF, or deadline.

    If ``pattern`` is None, perform one short read cycle (no prompt wait) then return.
    Returns ``(data, timed_out)``.
    """
    chunks: list[bytes] = []
    total = 0
    end = time.monotonic() + deadline_s
    last_data: float | None = None
    eof = False

    if pattern is None:
        timeout = min(0.25, max(0.05, end - time.monotonic()))
        r, _, _ = select.select([master_fd], [], [], timeout)
        if r:
            try:
                data = os.read(master_fd, 65536)
                if data:
                    chunks.append(data)
                    total += len(data)
            except OSError as e:
                if e.errno in (errno.EIO, errno.EPIPE):
                    eof = True
                else:
                    raise
        return b"".join(chunks), False

    while time.monotonic() < end and total < max_bytes:
        timeout = min(0.4, end - time.monotonic())
        if timeout <= 0:
            break
        r, _, _ = select.select([master_fd], [], [], timeout)
        if not r:
            if last_data is not None and (time.monotonic() - last_data) >= idle_after_data_s:
                text = strip_ansi(b"".join(chunks).decode("utf-8", errors="replace"))
                if pattern.search(text):
                    break
            continue
        try:
            data = os.read(master_fd, 65536)
        except OSError as e:
            if e.errno in (errno.EIO, errno.EPIPE):
                eof = True
                break
            raise
        if not data:
            eof = True
            break
        chunks.append(data)
        total += len(data)
        last_data = time.monotonic()
        text = strip_ansi(b"".join(chunks).decode("utf-8", errors="replace"))
        if pattern.search(text):
            break
    matched = bool(pattern.search(strip_ansi(b"".join(chunks).decode("utf-8", errors="replace"))))
    timed_out = not eof and not matched and time.monotonic() >= end - 1e-6
    return b"".join(chunks), timed_out


def read_until(
    master_fd: int,
    *,
    deadline_s: float,
    idle_after_data_s: float = 0.35,
    max_bytes: int = 512_000,
) -> tuple[bytes, bool]:
    """Read from PTY until deadline, idle period after last chunk, EOF, or max_bytes.

    Returns ``(data, timed_out)`` where ``timed_out`` is True if deadline hit without EOF.
    """
    chunks: list[bytes] = []
    total = 0
    end = time.monotonic() + deadline_s
    last_data: float | None = None
    eof = False
    while time.monotonic() < end and total < max_bytes:
        timeout = min(0.4, end - time.monotonic())
        if timeout <= 0:
            break
        r, _, _ = select.select([master_fd], [], [], timeout)
        if not r:
            if last_data is not None and (time.monotonic() - last_data) >= idle_after_data_s:
                break
            continue
        try:
            data = os.read(master_fd, 65536)
        except OSError as e:
            if e.errno in (errno.EIO, errno.EPIPE):
                eof = True
                break
            raise
        if not data:
            eof = True
            break
        chunks.append(data)
        total += len(data)
        last_data = time.monotonic()
    timed_out = not eof and time.monotonic() >= end - 1e-6
    return b"".join(chunks), timed_out


def run_under_pty(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout_s: float = 30.0,
    child_alarm_s: int | None = None,
) -> PtyResult:
    """Fork child with controlling PTY; child execs ``argv[0]`` with ``argv``.

    Stops after **timeout_s** read budget and sends **SIGTERM** to the child (smoke / capture runs).
    """
    cwd = Path(cwd or Path.cwd()).resolve()
    child_env = {**os.environ, **(env or {})}

    pid, master_fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(cwd)
            if child_alarm_s:
                signal.alarm(child_alarm_s)
            os.execvpe(argv[0], argv, child_env)
        except Exception:
            os._exit(127)
        os._exit(127)

    exit_code: int | None = None
    t_out = False
    try:
        raw, t_out = read_until(master_fd, deadline_s=timeout_s)
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass
        try:
            os.kill(pid, signal.SIGTERM)
            _pid, st = os.waitpid(pid, 0)
            exit_code = os.WEXITSTATUS(st) if os.WIFEXITED(st) else None
        except ChildProcessError:
            pass
        except ProcessLookupError:
            pass

    text = raw.decode("utf-8", errors="replace")
    return PtyResult(output=text, exit_code=exit_code, timed_out=t_out)


def run_under_pty_scripted(
    argv: list[str],
    steps: list[tuple[str | None, str]],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    total_timeout_s: float = 90.0,
    terminate_child: bool = True,
) -> PtyResult:
    """Run a command under a PTY and drive stdin with simple regex-gated steps.

    Each step is ``(expect_regex, send_text)``. If ``expect_regex`` is None, the send happens
    after a brief initial select (no prompt wait). ``send_text`` is written UTF-8; a newline
    is appended automatically if missing.

    Use this for integration smoke (e.g. ``ocean chat-repl``) where ``CliRunner`` is not a TTY.
    """
    cwd = Path(cwd or Path.cwd()).resolve()
    child_env = {**os.environ, **(env or {})}
    deadline = time.monotonic() + total_timeout_s
    all_chunks: list[bytes] = []

    pid, master_fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(cwd)
            os.execvpe(argv[0], argv, child_env)
        except Exception:
            os._exit(127)
        os._exit(127)

    exit_code: int | None = None
    timed_out = False
    try:
        for expect_re, send_text in steps:
            remain = max(0.1, deadline - time.monotonic())
            pat = re.compile(expect_re) if expect_re else None
            chunk, step_to = _wait_for_regex(master_fd, pattern=pat, deadline_s=remain)
            all_chunks.append(chunk)
            if step_to:
                timed_out = True
            payload = send_text if send_text.endswith("\n") else (send_text + "\n")
            os.write(master_fd, payload.encode("utf-8"))
        # Trailing drain
        remain = max(0.1, deadline - time.monotonic())
        tail, _ = read_until(master_fd, deadline_s=min(remain, 3.0), idle_after_data_s=0.4)
        all_chunks.append(tail)
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass
        if terminate_child:
            try:
                os.kill(pid, signal.SIGTERM)
                _pid, st = os.waitpid(pid, 0)
                exit_code = os.WEXITSTATUS(st) if os.WIFEXITED(st) else None
            except ChildProcessError:
                pass
            except ProcessLookupError:
                pass
        else:
            try:
                _pid, st = os.waitpid(pid, 0)
                exit_code = os.WEXITSTATUS(st) if os.WIFEXITED(st) else None
            except ChildProcessError:
                pass

    raw = b"".join(all_chunks)
    text = raw.decode("utf-8", errors="replace")
    return PtyResult(output=text, exit_code=exit_code, timed_out=timed_out)


def _main() -> None:
    """``python -m ocean.pty_harness -- <cmd>...``"""
    if "--" not in sys.argv:
        print("usage: python -m ocean.pty_harness -- <executable> [args...]", file=sys.stderr)
        raise SystemExit(2)
    idx = sys.argv.index("--")
    cmd = sys.argv[idx + 1 :]
    if not cmd:
        print("missing command after --", file=sys.stderr)
        raise SystemExit(2)
    r = run_under_pty(cmd, cwd=Path.cwd(), timeout_s=float(os.getenv("OCEAN_PTY_TIMEOUT", "45")))
    sys.stdout.write(r.output[:100_000])
    raise SystemExit(r.exit_code if r.exit_code is not None else 1)


if __name__ == "__main__":
    _main()
