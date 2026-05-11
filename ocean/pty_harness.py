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
