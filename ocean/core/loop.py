"""Autonomous loop: ocean lives here.

Each iteration is a session:
  1. Mint coins proportional to elapsed time (100/hr across 5 personas)
  2. Each persona nominates a task and bids coins
  3. Session auction: sort bids descending, fill until 30-coin budget consumed
  4. Dispatch selected tasks in bid order (highest bid = most important, goes first)
  5. Losers keep their coins — they'll bid higher next session
  6. Pause until next mint cycle, then repeat

Token rate limit: if the rolling hourly token count hits the ceiling,
sleep until enough of the window expires to continue.
"""

from __future__ import annotations

import time
from pathlib import Path

from ..feed import feed as _feed
from ..token_budget import usage_recent, note_usage
from .economy import CoinMint, SESSION_BUDGET
from .scheduler import PersonaScheduler, load_project_state

_DEFAULT_TOKEN_LIMIT = 200_000   # tokens per rolling hour
_SESSION_PAUSE = 5               # seconds between sessions (readable output)


def _token_limit(cwd: Path) -> int:
    import os
    from ..backends import load_prefs
    raw = os.getenv("OCEAN_TOKEN_BUDGET_PER_HOUR", "").strip()
    if not raw:
        p = load_prefs(cwd).get("token_budget_per_hour")
        raw = str(p).strip() if p else ""
    try:
        v = int(raw)
        return v if v > 0 else _DEFAULT_TOKEN_LIMIT
    except ValueError:
        return _DEFAULT_TOKEN_LIMIT


def _ledger_path(cwd: Path) -> Path:
    d = cwd / ".ocean"
    d.mkdir(parents=True, exist_ok=True)
    return d / "token_ledger.json"


def _wait_seconds_until_free(cwd: Path, limit: int) -> float:
    import json, time as _t
    path = _ledger_path(cwd)
    if not path.exists():
        return 0.0
    try:
        events = json.loads(path.read_text()).get("events", [])
        now = _t.time()
        window = [e for e in events if now - float(e.get("t", 0)) <= 3600]
        used = sum(int(e.get("n", 0)) for e in window)
        if used < limit:
            return 0.0
        oldest = min(float(e.get("t", now)) for e in window)
        return max(0.0, 3600.0 - (now - oldest))
    except Exception:
        return 0.0


def _dispatch(description: str, cwd: Path) -> int:
    """Call the agent, write output to workspace/, return estimated tokens used."""
    from .. import codex_exec as _cx
    result = _cx.generate_files_with_fallback(
        description, context_file=cwd / "docs" / "project.json"
    )
    if not result:
        return len(description) // 4
    if "__cursor_handoff__" in result:
        _feed("🌊 Ocean: cursor handoff written — open in Cursor Composer")
        return len(description) // 4
    workspace = cwd / "workspace"
    workspace.mkdir(exist_ok=True)
    for path, content in result.items():
        out = workspace / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        _feed(f"🌊 Ocean: ✅ workspace/{path}")
    return max(len(description) // 4, len(str(result)) // 4)


def run(cwd: Path | None = None) -> None:
    """Start the autonomous loop. Runs until KeyboardInterrupt."""
    cwd = Path(cwd or Path.cwd()).resolve()
    mint = CoinMint(cwd)
    scheduler = PersonaScheduler()
    token_limit = _token_limit(cwd)
    session = 0

    _feed(f"🌊 Ocean: alive — session budget {SESSION_BUDGET} coins | token ceiling {token_limit:,}/hr")
    _feed(f"🌊 Ocean: wallets — {mint.balance_str()}")

    while True:
        session += 1

        # ── mint ──────────────────────────────────────────────────────────────
        minted = mint.tick()
        if minted >= 0.5:
            _feed(f"🌊 Ocean: +{minted:.1f} coins minted — {mint.balance_str()}")

        # ── token rate limit ──────────────────────────────────────────────────
        used = usage_recent(_ledger_path(cwd))
        if used >= token_limit:
            wait = _wait_seconds_until_free(cwd, token_limit)
            _feed(f"🌊 Ocean: token ceiling {used:,}/{token_limit:,} — sleeping {wait:.0f}s")
            time.sleep(max(60.0, wait))
            continue

        # ── nominations ───────────────────────────────────────────────────────
        state = load_project_state(cwd)
        nominations = scheduler.nominate_all(state, mint.wallets)

        if not nominations:
            _feed("🌊 Ocean: all wallets empty — sleeping 60s for next mint")
            time.sleep(60)
            continue

        # ── session auction ───────────────────────────────────────────────────
        result = mint.run_session(nominations)

        _feed(
            f"🌊 Ocean: session {session} — "
            f"budget {SESSION_BUDGET} coins | "
            f"used {result.budget_used:.1f} | "
            f"dispatching {len(result.selected)} task(s) | "
            f"deferred {len(result.deferred)}"
        )
        _feed(f"🌊 Ocean: wallets after auction — {mint.balance_str()}")

        if result.deferred:
            deferred_names = ", ".join(
                f"{n.persona}({n.bid:.1f})" for n in result.deferred
            )
            _feed(f"🌊 Ocean: deferred (saving coins) — {deferred_names}")

        # ── dispatch selected tasks in bid order ──────────────────────────────
        for nom in result.selected:
            _feed(f"🌊 Ocean: [{nom.persona} bid={nom.bid:.1f}] {nom.task_title}")
            _feed(f"🌊 Ocean: {nom.persona} says: {nom.rationale}")
            tokens = _dispatch(nom.task_description, cwd)
            note_usage(tokens, cwd)

        if not result.selected:
            _feed("🌊 Ocean: nothing fit the budget this session — all coins saved")

        time.sleep(_SESSION_PAUSE)
