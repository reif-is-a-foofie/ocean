from __future__ import annotations

from pathlib import Path

import pytest

from ocean import proposal_board as pb


def test_publish_list_finalize(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    p = pb.publish_proposal(
        root,
        "Moroni",
        {"title": "Slice 1", "rationale": "smallest next win", "value": "high"},
    )
    assert p.name == "Moroni.json"
    board = pb.list_board(root)
    assert board.get("status") == "open"
    assert "Moroni" in board["proposals"]
    peer = pb.read_peer(root, "Q", "Moroni")
    assert peer and peer.get("title") == "Slice 1"
    pb.revise_own(root, "Moroni", {"cost": "low"})
    again = pb.read_peer(root, "Moroni", "Moroni")
    assert again and again.get("cost") == "low" and again.get("title") == "Slice 1"
    arch = pb.finalize_round(root, label="t1")
    assert arch.is_dir()
    board_final = pb.list_board(root)
    assert board_final.get("status") == "archived"


def test_publish_rejects_unknown_persona(tmp_path: Path) -> None:
    root = tmp_path / "p"
    (root / "docs").mkdir(parents=True)
    with pytest.raises(ValueError, match="cannot publish"):
        pb.publish_proposal(root, "Ocean", {"title": "x"})
