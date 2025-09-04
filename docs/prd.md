# Ocean Project PRD — Web Tic-Tac-Toe

## Summary
Build a small web-based Tic-Tac-Toe game with a 1‑player mode (play against the computer AI). If you win, enter your name to record a high score. Keep it simple and fast to run locally.

## Goals
- Single‑player Tic‑Tac‑Toe vs computer
- Simple, responsive UI (HTML/CSS/JS)
- Minimal backend with health check and scores API
- Persist high scores locally (file or SQLite)
- Clear instructions and quick start script

## Non‑Goals
- Multiplayer networking
- Authentication/user accounts
- Sophisticated graphics or frameworks

## Requirements
- 3x3 board, player is X, computer is O
- Basic computer AI (at least block winning moves; preferably minimax for unbeatable AI)
- When the player wins, prompt for a name and save the score with timestamp
- Show top 10 scores on the page
- Backend endpoints:
  - GET `/healthz` → `{ ok: true }`
  - GET `/scores` → list of scores (JSON)
  - POST `/scores` → body `{ name: string, result: 'win'|'loss'|'draw', ts?: string }`
- Serve static UI from `ui/`

## Tech
- Backend: FastAPI, Uvicorn
- Storage: SQLite or local JSON (choose simplest)
- Frontend: Plain HTML/CSS/JS (no heavy frameworks)
- Dev: Python 3.11+, `run.sh` helper, Dockerfile + CI

## UX Notes
- Board shows turn status and game result (Win/Loss/Draw)
- “New Game” button resets the board
- “High Scores” panel lists top results

## Stretch (optional)
- Difficulty toggle (easy/unbeatable)
- Animations for win line

## Constraints
- Minimal dependencies
- Work offline, no cloud services required
