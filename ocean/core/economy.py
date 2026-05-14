"""Coin economy: 100 coins/hour minted and spread evenly across personas.

Session model:
- Each session has a fixed budget (default 30 coins).
- Every persona submits one or more bids (task + coin amount).
- All bids are sorted descending by amount.
- Tasks are selected greedily until the budget is consumed.
- Only winning personas spend their coins; losers keep theirs for next session.

This means a persona that saves across sessions can place a dominant bid
and guarantee their task goes first.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PERSONAS = ["Mario", "Q", "Tony", "Moroni", "Edna"]
HOURLY_SUPPLY = 100          # total coins minted per hour
SESSION_BUDGET = 30          # coin budget consumed per loop session
_ECONOMY_FILE = "docs/economy.json"
_MIN_MINT = 0.5              # mint when at least half a coin is due


@dataclass
class Wallet:
    persona: str
    balance: float = 0.0

    def deposit(self, amount: float) -> None:
        self.balance = round(self.balance + amount, 4)

    def spend(self, amount: float) -> bool:
        if amount > self.balance + 1e-9:
            return False
        self.balance = round(max(0.0, self.balance - amount), 4)
        return True

    def can_bid(self, amount: float) -> bool:
        return self.balance >= amount - 1e-9


@dataclass
class Nomination:
    persona: str
    task_title: str
    task_description: str
    bid: float          # coins offered — also the "cost" consumed from session budget
    rationale: str


@dataclass
class SessionResult:
    selected: list[Nomination]      # tasks dispatched this session
    deferred: list[Nomination]      # tasks that didn't fit; personas keep their coins
    budget_used: float
    budget_remaining: float


class CoinMint:
    """Mints coins over time, distributes evenly, runs the session auction."""

    def __init__(self, cwd: Path | None = None, session_budget: float = SESSION_BUDGET):
        self.cwd = Path(cwd or Path.cwd())
        self.session_budget = session_budget
        self.wallets: dict[str, Wallet] = {}
        self._last_mint_ts: float = 0.0
        self._load()

    def _path(self) -> Path:
        return self.cwd / _ECONOMY_FILE

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for p in PERSONAS:
                    bal = float(data.get("wallets", {}).get(p, 0.0))
                    self.wallets[p] = Wallet(p, bal)
                self._last_mint_ts = float(data.get("last_mint_ts", 0.0))
                return
            except Exception:
                pass
        # Fresh start — seed each persona with their first hour allocation
        per = HOURLY_SUPPLY / len(PERSONAS)
        for p in PERSONAS:
            self.wallets[p] = Wallet(p, per)
        self._last_mint_ts = time.time()
        self._save()

    def _save(self) -> None:
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "wallets": {p: w.balance for p, w in self.wallets.items()},
                    "last_mint_ts": self._last_mint_ts,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def tick(self) -> float:
        """Mint coins proportional to elapsed time. Returns coins newly minted."""
        now = time.time()
        elapsed_hours = (now - self._last_mint_ts) / 3600.0
        coins = HOURLY_SUPPLY * elapsed_hours
        if coins >= _MIN_MINT:
            per = coins / len(self.wallets)
            for w in self.wallets.values():
                w.deposit(per)
            self._last_mint_ts = now
            self._save()
            return round(coins, 2)
        return 0.0

    def run_session(self, nominations: list[Nomination]) -> SessionResult:
        """Greedy fill: sort bids descending, select until session_budget consumed.

        Only winning personas are charged. Losers keep all their coins.
        """
        # Only include nominations the persona can actually cover
        valid = [n for n in nominations if self.wallets[n.persona].can_bid(n.bid)]
        sorted_noms = sorted(valid, key=lambda n: n.bid, reverse=True)

        selected: list[Nomination] = []
        deferred: list[Nomination] = []
        remaining = self.session_budget

        for nom in sorted_noms:
            if nom.bid <= remaining + 1e-9:
                selected.append(nom)
                remaining -= nom.bid
            else:
                deferred.append(nom)

        # Charge only winners
        for nom in selected:
            self.wallets[nom.persona].spend(nom.bid)
        self._save()

        return SessionResult(
            selected=selected,
            deferred=deferred,
            budget_used=round(self.session_budget - remaining, 4),
            budget_remaining=round(remaining, 4),
        )

    def balances(self) -> dict[str, float]:
        return {p: w.balance for p, w in self.wallets.items()}

    def balance_str(self) -> str:
        return " | ".join(f"{p}={v:.1f}" for p, v in self.balances().items())
