from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ocean.actors import add_actor_skill, coverage_report, load_actors, save_actors, update_actor
from ocean.jobs import plan_jobs
from ocean.product_chat import product_chat, recent_chat
from ocean.product_loop import DOCTRINE_FILES, bootstrap_doctrine, record_feedback, turn


ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"
UI_DIST_DIR = UI_DIR / "dist"
STATIC_UI_DIR = UI_DIST_DIR if UI_DIST_DIR.exists() else UI_DIR

app = FastAPI(title="Ocean Control Room", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_UI_DIR.exists():
    if UI_DIST_DIR.exists() and (UI_DIST_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(UI_DIST_DIR / "assets")), name="assets")
    app.mount("/ui", StaticFiles(directory=str(STATIC_UI_DIR), html=True), name="ui")


class ProjectRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))


class ActorUpdate(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    name: str | None = None
    role: str | None = None
    mission: str | None = None
    phase: str | None = None
    skills: list[str] | None = None
    tools: list[str] | None = None
    active: bool | None = None


class SkillRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    skill: str


class ActorsSaveRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    actors: list[dict[str, Any]]


class TurnRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    user_turn: str = ""
    feedback: str = ""
    test_results: str = ""
    candidate_tasks: list[str] = Field(default_factory=list)
    use_advisor: bool = True


class JobPlanRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    user_turn: str = ""
    test_results: str = ""
    candidate_tasks: list[str] = Field(default_factory=list)
    use_advisor: bool = True


class FeedbackRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    feedback: str
    source: str = "Reif"
    test_context: str | None = None
    update_files: bool = True


class ChatScreenshot(BaseModel):
    name: str = "screenshot.png"
    data_url: str
    note: str = ""


class ChatRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    message: str
    screenshots: list[ChatScreenshot] = Field(default_factory=list)
    test_notes: str = ""
    update_feedback: bool = False
    use_advisor: bool = True


class FileReadRequest(BaseModel):
    project_root: str = Field(default_factory=lambda: str(ROOT))
    path: str


@app.get("/")
def index():
    index_path = STATIC_UI_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"name": "Ocean Control Room", "ui": "/ui"}


@app.get("/healthz")
def healthz():
    return {"ok": True, "status": "healthy"}


@app.get("/api/state")
def state(project_root: str = str(ROOT)):
    root = _resolve_root(project_root)
    bootstrap_doctrine(root)
    return {
        "project_root": str(root),
        "actors": load_actors(root),
        "coverage": coverage_report(root),
        "doctrine": _read_doctrine(root),
    }


@app.get("/api/actors")
def actors(project_root: str = str(ROOT)):
    root = _resolve_root(project_root)
    return {"project_root": str(root), "actors": load_actors(root)}


@app.put("/api/actors")
def replace_actors(request: ActorsSaveRequest):
    root = _resolve_root(request.project_root)
    return {"project_root": str(root), "actors": save_actors(request.actors, root)}


@app.patch("/api/actors/{actor_id}")
def patch_actor(actor_id: str, request: ActorUpdate):
    root = _resolve_root(request.project_root)
    patch = request.model_dump(exclude_none=True) if hasattr(request, "model_dump") else request.dict(exclude_none=True)
    patch.pop("project_root", None)
    return {"project_root": str(root), "actor": update_actor(actor_id, patch, root)}


@app.post("/api/actors/{actor_id}/skills")
def create_actor_skill(actor_id: str, request: SkillRequest):
    root = _resolve_root(request.project_root)
    return {"project_root": str(root), "actor": add_actor_skill(actor_id, request.skill, root)}


@app.get("/api/coverage")
def coverage(project_root: str = str(ROOT)):
    root = _resolve_root(project_root)
    return {"project_root": str(root), "coverage": coverage_report(root)}


@app.post("/api/ocean/turn")
def ocean_turn(request: TurnRequest):
    root = _resolve_root(request.project_root)
    try:
        return turn(
            root,
            user_turn=request.user_turn,
            feedback=request.feedback,
            test_results=request.test_results,
            candidate_tasks=request.candidate_tasks,
            use_advisor=request.use_advisor,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/jobs/plan")
def jobs_plan(request: JobPlanRequest):
    root = _resolve_root(request.project_root)
    try:
        return plan_jobs(
            root,
            user_turn=request.user_turn,
            test_results=request.test_results,
            candidate_tasks=request.candidate_tasks,
            use_advisor=request.use_advisor,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/feedback")
def feedback(request: FeedbackRequest):
    root = _resolve_root(request.project_root)
    try:
        return record_feedback(
            root,
            request.feedback,
            source=request.source,
            test_context=request.test_context,
            update_files=request.update_files,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/chat")
def chat_history(project_root: str = str(ROOT)):
    root = _resolve_root(project_root)
    return {"project_root": str(root), "messages": recent_chat(root, limit=40)}


@app.post("/api/chat")
def chat(request: ChatRequest):
    root = _resolve_root(request.project_root)
    shots = [
        shot.model_dump() if hasattr(shot, "model_dump") else shot.dict()
        for shot in request.screenshots
    ]
    try:
        return product_chat(
            root,
            request.message,
            screenshots=shots,
            test_notes=request.test_notes,
            update_feedback=request.update_feedback,
            use_advisor=request.use_advisor,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/files")
def files(project_root: str = str(ROOT), limit: int = 160):
    root = _resolve_root(project_root)
    return {"project_root": str(root), "files": _file_tree(root, limit=limit)}


@app.post("/api/files/read")
def read_file(request: FileReadRequest):
    root = _resolve_root(request.project_root)
    path = _safe_child(root, request.path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {request.path}")
    if path.stat().st_size > 200_000:
        raise HTTPException(status_code=400, detail="File is too large to preview")
    return {
        "project_root": str(root),
        "path": str(path.relative_to(root)),
        "content": path.read_text(encoding="utf-8", errors="replace"),
    }


@app.get("/api/artifacts")
def artifact(project_root: str, path: str):
    root = _resolve_root(project_root)
    artifact_path = _safe_child(root, path)
    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {path}")
    return FileResponse(artifact_path)


@app.post("/api/doctrine/bootstrap")
def bootstrap(request: ProjectRequest):
    root = _resolve_root(request.project_root)
    return bootstrap_doctrine(root)


def _resolve_root(project_root: str) -> Path:
    root = Path(project_root or ROOT).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid project_root: {root}")
    return root


def _read_doctrine(root: Path) -> dict[str, str]:
    bootstrap_doctrine(root)
    result: dict[str, str] = {}
    for name in DOCTRINE_FILES:
        path = root / name
        if path.exists():
            result[name] = path.read_text(encoding="utf-8", errors="ignore")
    return result


def _safe_child(root: Path, rel_path: str) -> Path:
    path = (root / rel_path).resolve()
    if root not in path.parents and path != root:
        raise HTTPException(status_code=400, detail="Path escapes project root")
    return path


def _file_tree(root: Path, *, limit: int = 160) -> list[dict[str, Any]]:
    ignored = {".git", ".ocean", "__pycache__", ".pytest_cache", "node_modules", "venv", ".venv", "logs", "dist", "build"}
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in ignored for part in rel.parts):
            continue
        if path.is_file():
            files.append({"path": str(rel), "size": path.stat().st_size})
        if len(files) >= limit:
            break
    return files
