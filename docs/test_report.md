# Test Report

Generated: 2026-05-12T10:17:21.139038

## Pytest Output

````
..............sFFFF...............................................s..... [100%]
=================================== FAILURES ===================================
____________________ test_control_room_state_jobs_and_chat _____________________

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-175/test_control_room_state_jobs_a0')

    def test_control_room_state_jobs_and_chat(tmp_path):
        client = TestClient(app)
    
        state = client.get("/api/state", params={"project_root": str(tmp_path)}).json()
>       assert state["coverage"]["gaps"] == []
               ^^^^^^^^^^^^^^^^^
E       KeyError: 'coverage'

tests/test_control_room.py:10: KeyError
____________________________ test_filesystem_routes ____________________________

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-175/test_filesystem_routes0')

    def test_filesystem_routes(tmp_path):
        client = TestClient(app)
        (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")
    
        files = client.get("/api/files", params={"project_root": str(tmp_path)}).json()
>       assert {"path": "README.md", "size": 8} in files["files"]
                                                   ^^^^^^^^^^^^^^
E       KeyError: 'files'

tests/test_control_room.py:45: KeyError
_____________________ test_chat_can_update_doctrine_files ______________________

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-175/test_chat_can_update_doctrine_0')

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
    
>       assert result["file_updates"] == [{"path": "VISION.md", "mode": "replace"}]
               ^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'file_updates'

tests/test_control_room.py:66: KeyError
____________________ test_chat_saves_screenshot_as_artifact ____________________

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-175/test_chat_saves_screenshot_as_0')

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
    
>       path = result["screenshots"][0]["path"]
               ^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'screenshots'

tests/test_control_room.py:90: KeyError
=========================== short test summary info ============================
FAILED tests/test_control_room.py::test_control_room_state_jobs_and_chat - Ke...
FAILED tests/test_control_room.py::test_filesystem_routes - KeyError: 'files'
FAILED tests/test_control_room.py::test_chat_can_update_doctrine_files - KeyE...
FAILED tests/test_control_room.py::test_chat_saves_screenshot_as_artifact - K...

````

Exit code: 1
