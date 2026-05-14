"""Concrete Textual onboarding scenarios — shared by Pilot tests and the tmux driver.

These are **product-shaped** flows (real wording, localhost scope). They validate that
Ocean captures a ``docs/project.json`` spec and can queue follow-up tasks. They do **not**
invoke Codex/codegen (that remains ``ocean chat`` / tooling outside this shell).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator


@dataclass(frozen=True)
class TextualProductScenario:
    """One end-to-end story: Moroni clarify (5 lines) + optional shell commands after save."""

    id: str
    title: str
    summary: str
    onboarding_lines: tuple[str, str, str, str, str]
    post_save_commands: tuple[str, ...] = ()
    expect_spec_keys: dict[str, Any] | None = None

    def iter_all_commands(self) -> Iterator[str]:
        yield from self.onboarding_lines
        yield from self.post_save_commands


# --- Scenarios (keep lines ASCII-only and tmux-safe: avoid embedded quotes in goals.) ---

TIC_TAC_TOE_LOCALHOST = TextualProductScenario(
    id="tic_tac_toe_localhost",
    title="Tic-tac-toe on localhost",
    summary="Two-player grid game in the browser on 127.0.0.1; hot reload dev loop.",
    onboarding_lines=(
        "TicTacLocalhost",
        "web",
        "Two player tic tac toe in the browser on localhost without accounts or server deploy.",
        "mvp,localhost,keyboard",
        "none",
    ),
    post_save_commands=(
        "task add Implement 3x3 board state in TypeScript",
        "task add Add win detection and stalemate",
        "task add Wire localhost dev server and README run steps",
    ),
    expect_spec_keys={"name": "TicTacLocalhost", "kind": "web"},
)

PADDLE_WARS_KEEN = TextualProductScenario(
    id="paddle_wars_keen",
    title="Paddle arena (Keen-style bonus game)",
    summary="Single-screen paddle ball arena inspired by Commander Keen-style bonus rounds; runs locally.",
    onboarding_lines=(
        "PaddleKeenArena",
        "web",
        "Single screen paddle arena with ball physics and bricks; runs on localhost for iteration.",
        "physics,60fps,iterate",
        "keyboard only,no network multiplayer yet",
    ),
    post_save_commands=(
        "task add Implement paddle movement and ball velocity with fixed timestep",
        "task add Add brick grid collisions and score HUD",
        "task add Add pause menu and restart flow",
    ),
    expect_spec_keys={"name": "PaddleKeenArena", "kind": "web"},
)

CLI_DEVTOOLS = TextualProductScenario(
    id="cli_devtools_scratch",
    title="CLI scratch tools",
    summary="Local Python CLI utilities for dev ergonomics; no web UI.",
    onboarding_lines=(
        "DevScratchCLI",
        "cli",
        "Small command line helpers for repo hygiene and smoke checks on localhost.",
        "fast,scriptable,tests",
        "no cloud deploy",
    ),
    post_save_commands=("task add Add argparse entry and pytest smoke",),
    expect_spec_keys={"name": "DevScratchCLI", "kind": "cli"},
)

SCENARIOS: dict[str, TextualProductScenario] = {
    s.id: s
    for s in (TIC_TAC_TOE_LOCALHOST, PADDLE_WARS_KEEN, CLI_DEVTOOLS)
}


def get_scenario(scenario_id: str) -> TextualProductScenario:
    if scenario_id not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS))
        raise KeyError(f"unknown scenario {scenario_id!r}; choose one of: {known}")
    return SCENARIOS[scenario_id]


def list_scenario_ids() -> list[str]:
    return sorted(SCENARIOS.keys())
