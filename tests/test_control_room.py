from fastapi.testclient import TestClient

from backend.app import app


def test_control_room_state_jobs_and_chat(tmp_path):
    client = TestClient(app)

    state = client.get("/api/state", params={"project_root": str(tmp_path)}).json()
    assert state["coverage"]["gaps"] == []
    assert len(state["actors"]) == 5
    assert any(actor["id"] == "scrooge" for actor in state["actors"])

    jobs = client.post(
        "/api/jobs/plan",
        json={
            "project_root": str(tmp_path),
            "user_turn": "Drive this toward adoption and revenue.",
            "candidate_tasks": ["First-run onboarding", "Another provider"],
            "use_advisor": False,
        },
    ).json()
    assert any(job["actor_id"] == "scrooge" for job in jobs["jobs"])
    assert len(jobs["jobs"]) <= 5
    assert jobs["jobs"][0]["cursor_prompt"]

    chat = client.post(
        "/api/chat",
        json={
            "project_root": str(tmp_path),
            "message": "What benefit is this creating and how do we monetize it?",
            "use_advisor": False,
        },
    ).json()
    assert chat["response"]
    assert chat["advisor_prompt"]
    assert [item["actor_id"] for item in chat["team_messages"]] == ["captain", "scrooge", "edna", "q", "mario"]


def test_filesystem_routes(tmp_path):
    client = TestClient(app)
    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")

    files = client.get("/api/files", params={"project_root": str(tmp_path)}).json()
    assert {"path": "README.md", "size": 8} in files["files"]

    read = client.post(
        "/api/files/read",
        json={"project_root": str(tmp_path), "path": "README.md"},
    ).json()
    assert read["content"] == "# Hello\n"


def test_chat_can_update_doctrine_files(tmp_path):
    client = TestClient(app)

    result = client.post(
        "/api/chat",
        json={
            "project_root": str(tmp_path),
            "message": "update VISION.md: Ocean should stay chat-only and keep filesystem changes conversational.",
            "use_advisor": False,
        },
    ).json()

    assert result["file_updates"] == [{"path": "VISION.md", "mode": "replace"}]
    assert result["team_messages"][0]["artifacts"][0]["path"] == "VISION.md"
    assert "chat-only" in (tmp_path / "VISION.md").read_text(encoding="utf-8")


def test_chat_saves_screenshot_as_artifact(tmp_path):
    client = TestClient(app)

    result = client.post(
        "/api/chat",
        json={
            "project_root": str(tmp_path),
            "message": "This screenshot feels confusing.",
            "screenshots": [
                {
                    "name": "screen.png",
                    "data_url": "data:image/png;base64,iVBORw0KGgo=",
                    "note": "",
                }
            ],
            "use_advisor": False,
        },
    ).json()

    path = result["screenshots"][0]["path"]
    assert path.startswith(".ocean/screenshots/")
    artifact = client.get("/api/artifacts", params={"project_root": str(tmp_path), "path": path})
    assert artifact.status_code == 200
