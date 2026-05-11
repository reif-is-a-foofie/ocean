import sys
from pathlib import Path

from ocean.mcp_client import StdioJsonRpcClient
from ocean.product_loop import bootstrap_doctrine, next_action, normalize_advisor_recommendation, record_feedback, turn


def test_bootstrap_and_feedback_update_doctrine(tmp_path: Path):
    result = bootstrap_doctrine(tmp_path, vision="External product intelligence for coding agents.")

    assert "VISION.md" in result["created"]
    assert (tmp_path / "PRODUCT_PRINCIPLES.md").exists()
    assert (tmp_path / "UX_RULES.md").exists()

    feedback = record_feedback(
        tmp_path,
        "This feels too technical. Lucky should explain what is happening like a smart assistant, not a terminal.",
    )

    assert "language_tone" in feedback["categories"]
    assert "PRODUCT_PRINCIPLES.md" in feedback["updated_files"]
    assert "plain assistant language" in (tmp_path / "PRODUCT_PRINCIPLES.md").read_text()
    assert "Every setup step" in (tmp_path / "UX_RULES.md").read_text()
    assert "friendly setup narration" in (tmp_path / "TASKS.md").read_text()


def test_next_action_prioritizes_external_mcp_cursor_loop(tmp_path: Path):
    bootstrap_doctrine(tmp_path)
    (tmp_path / "TASKS.md").write_text(
        "# Tasks\n\n"
        "- [ ] Add another model provider.\n"
        "- [ ] Create first-run onboarding for Cursor MCP setup.\n",
        encoding="utf-8",
    )

    guidance = next_action(
        tmp_path,
        user_turn="Upgrade Ocean so it can run as an MCP outside the codebase and help Cursor on each turn.",
        use_advisor=False,
    )

    assert guidance.selected_task is not None
    assert "MCP server" in guidance.selected_task.title or "Cursor" in guidance.selected_task.title
    assert "Captain" in "\n".join(guidance.instructions)
    assert "Ocean is not trying to be a full brain" in guidance.advisor_prompt
    assert "build_context" in guidance.advisor_prompt


def test_turn_combines_feedback_and_pm_guidance(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Test App\n\nA target repo under test.\n", encoding="utf-8")
    result = turn(
        tmp_path,
        user_turn="Build-test-feedback loop for Cursor.",
        feedback="The setup is confusing and needs a five minute first run.",
        test_results="Unit tests passed.",
        use_advisor=False,
    )

    assert result["feedback_result"]["categories"]
    assert result["selected_task"]
    assert "smallest next change" in result["mcp_instruction"]
    assert result["build_context"]["important_files"]


def test_mcp_server_lists_and_calls_tools(tmp_path: Path):
    client = StdioJsonRpcClient(cmd=[sys.executable, "-m", "ocean.mcp_server"])
    try:
        client.start()
        initialized = client.initialize(timeout=5)
        assert initialized["serverInfo"]["name"] == "ocean"
        tools = client.list_tools()
        names = {tool["name"] for tool in tools}
        assert "ocean_turn" in names

        result = client.call_tool(
            "ocean_turn",
            {
                "project_root": str(tmp_path),
                "user_turn": "Run Ocean as MCP outside the codebase for Cursor.",
                "use_advisor": False,
            },
        )
        assert "content" in result
        assert result["structuredContent"]["selected_task"]
        assert result["structuredContent"]["build_context"]
    finally:
        client.stop()


def test_normalizes_reasoning_engine_json():
    parsed = normalize_advisor_recommendation(
        {
            "recommended_task": {
                "title": "Create Cursor MCP onboarding",
                "rationale": "It reduces setup friction.",
                "scores": {"user_value": 5, "risk": 2},
            },
            "feature_set": ["Cursor config", "first successful turn"],
            "agent_instructions": ["Make the setup observable."],
        }
    )

    assert parsed["recommended_task"]["title"] == "Create Cursor MCP onboarding"
    assert parsed["recommended_task"]["scores"]["user_value"] == 5
    assert parsed["feature_set"] == ["Cursor config", "first successful turn"]
