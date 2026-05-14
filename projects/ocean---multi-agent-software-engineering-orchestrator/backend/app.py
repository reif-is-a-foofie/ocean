from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="OCEAN - Multi-Agent Software Engineering Orchestrator",
    version="0.1.0",
)


@app.get("/")
def index() -> dict[str, str]:
    return {
        "name": "OCEAN - Multi-Agent Software Engineering Orchestrator",
        "status": "ready",
        "message": "Ocean runs the crew and timing; you steer goals and say when we're done.",
    }


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {"ok": True, "status": "healthy"}
