from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
from datetime import datetime

app = FastAPI(title="Ocean Project PRD — Web Tic-Tac-Toe", version="0.1.0")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SCORES_PATH = DATA_DIR / "scores.json"


def _load_scores() -> list[dict]:
    if not SCORES_PATH.exists():
        return []
    try:
        return json.loads(SCORES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_scores(items: list[dict]) -> None:
    SCORES_PATH.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


class ScoreIn(BaseModel):
    name: str
    result: str  # 'win' | 'loss' | 'draw'
    ts: str | None = None

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {"message": "Welcome to Ocean Project PRD — Web Tic-Tac-Toe", "type": "web"}

@app.get('/healthz')
def healthz():
    return {'ok': True, 'status': 'healthy'}

@app.get('/scores')
def get_scores():
    """Return top scores (wins first, then recent)."""
    items = _load_scores()
    # sort: wins first, then by ts desc
    def key(it):
        return (0 if it.get('result') == 'win' else 1, it.get('ts', ''))
    items_sorted = sorted(items, key=key)
    return {"scores": items_sorted[:10]}


@app.post('/scores')
def post_score(score: ScoreIn):
    if score.result not in {'win', 'loss', 'draw'}:
        raise HTTPException(status_code=400, detail="invalid result")
    items = _load_scores()
    ts = score.ts or datetime.utcnow().isoformat()
    items.append({"name": score.name.strip()[:40] or "Anon", "result": score.result, "ts": ts})
    _save_scores(items)
    return {"ok": True}
