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
from typing import Any

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


class PtyScenarioError(RuntimeError):
    """Raised when a scripted PTY scenario step times out or is misconfigured."""

    def __init__(self, message: str, *, output_plain: str) -> None:
        super().__init__(message)
        self.output_plain = output_plain


def tail_plain(text: str, *, lines: int = 48) -> str:
    """Last ``lines`` non-ANSI lines for failure diagnostics."""
    ls = strip_ansi(text).splitlines()
    return "\n".join(ls[-lines:])


def _expand_placeholders(obj: Any, mapping: dict[str, str]) -> Any:
    if isinstance(obj, str):
        out = obj
        for k, v in mapping.items():
            out = out.replace(f"${{{k}}}", v)
        return out
    if isinstance(obj, list):
        return [_expand_placeholders(x, mapping) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _expand_placeholders(v, mapping) for k, v in obj.items()}
    return obj


def load_pty_scenario_yaml(
    path: Path | str,
    *,
    placeholders: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Load a YAML scenario: ``command``, optional ``env``, ``steps`` list."""
    try:
        import yaml  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PyYAML is required for YAML PTY scenarios") from e
    p = Path(path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PtyScenarioError(f"scenario root must be a mapping: {p}", output_plain="")
    ph = {"PYTHON": sys.executable, **(placeholders or {})}
    return _expand_placeholders(raw, ph)  # type: ignore[return-value]


def run_under_pty_scenario(
    scenario: dict[str, Any],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    total_timeout_s: float = 120.0,
    terminate_child: bool = True,
) -> PtyResult:
    """Run ``scenario['command']`` under PTY; each step waits for ``expect`` then ``send``s."""
    cmd = scenario.get("command")
    if not isinstance(cmd, list) or not cmd or not all(isinstance(x, str) for x in cmd):
        raise PtyScenarioError("scenario['command'] must be a non-empty list of strings", output_plain="")
    steps_raw = scenario.get("steps") or []
    if not isinstance(steps_raw, list) or not steps_raw:
        raise PtyScenarioError("scenario['steps'] must be a non-empty list", output_plain="")

    cwd = Path(cwd or Path.cwd()).resolve()
    child_env = {**os.environ, **(env or {})}
    scen_env = scenario.get("env") or {}
    if isinstance(scen_env, dict):
        for k, v in scen_env.items():
            child_env[str(k)] = str(v)

    deadline = time.monotonic() + total_timeout_s
    all_chunks: list[bytes] = []

    pid, master_fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(cwd)
            os.execvpe(cmd[0], cmd, child_env)
        except Exception:
            os._exit(127)
        os._exit(127)

    exit_code: int | None = None
    timed_out = False
    try:
        for i, step in enumerate(steps_raw):
            if not isinstance(step, dict):
                raise PtyScenarioError(f"step {i} must be a mapping", output_plain=strip_ansi(b"".join(all_chunks).decode("utf-8", errors="replace")))
            send_text = step.get("send")
            if not isinstance(send_text, str):
                raise PtyScenarioError(f"step {i} missing string 'send'", output_plain=tail_plain(b"".join(all_chunks).decode("utf-8", errors="replace")))
            expect_any = step.get("expect_any")
            expect_re = step.get("expect")
            pat: re.Pattern[str] | None
            if expect_any is not None:
                if not isinstance(expect_any, list) or not expect_any:
                    raise PtyScenarioError(f"step {i} expect_any must be non-empty list", output_plain="")
                combined = "|".join(f"(?:{x})" for x in expect_any if isinstance(x, str))
                pat = re.compile(combined)
            elif expect_re is None:
                pat = None
            elif isinstance(expect_re, str):
                pat = re.compile(expect_re)
            else:
                raise PtyScenarioError(f"step {i} expect must be string or null", output_plain="")

            step_timeout = float(step["timeout_s"]) if step.get("timeout_s") is not None else min(60.0, max(5.0, deadline - time.monotonic()))
            remain = max(0.1, deadline - time.monotonic())
            step_deadline = min(step_timeout, remain)
            chunk, step_to = _wait_for_regex(master_fd, pattern=pat, deadline_s=step_deadline)
            all_chunks.append(chunk)
            if step_to:
                timed_out = True
                plain = strip_ansi(b"".join(all_chunks).decode("utf-8", errors="replace"))
                detail = tail_plain(plain)
                raise PtyScenarioError(
                    f"step {i} timed out waiting for {expect_re!r} / expect_any={expect_any!r}\n--- tail ---\n{detail}",
                    output_plain=plain,
                )
            payload = send_text if send_text.endswith("\n") else (send_text + "\n")
            os.write(master_fd, payload.encode("utf-8"))
        remain = max(0.1, deadline - time.monotonic())
        tail, _ = read_until(master_fd, deadline_s=min(remain, 4.0), idle_after_data_s=0.45)
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


def run_under_pty_scenario_file(
    scenario_path: Path | str,
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    total_timeout_s: float = 120.0,
    terminate_child: bool = True,
    placeholders: dict[str, str] | None = None,
) -> PtyResult:
    scenario = load_pty_scenario_yaml(scenario_path, placeholders=placeholders)
    return run_under_pty_scenario(
        scenario,
        cwd=cwd,
        env=env,
        total_timeout_s=total_timeout_s,
        terminate_child=terminate_child,
    )


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
