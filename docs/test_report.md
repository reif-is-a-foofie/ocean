# Test Report

Generated: 2025-09-05T20:01:19.158447

## Pytest Output

````
.F..s.                                                                   [100%]
=================================== FAILURES ===================================
__________________________ test_chat_non_interactive ___________________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x106032ea0>
tmp_path = PosixPath('/private/var/folders/tr/sdscsr7x7r3grp1qymk8zkk40000gn/T/pytest-of-reif/pytest-56/test_chat_non_interactive0')

    def test_chat_non_interactive(monkeypatch, tmp_path):
        # Simulate a non-interactive run by patching Rich prompts
        from ocean import cli as cli_mod
        from rich.prompt import Prompt
    
        answers = {
            "name": "Test Project",
            "kind": "web",
            "description": "A test",
            "goals": "ship",
            "constraints": "none",
        }
    
        def fake_prompt(text, default=None, choices=None):
            if "Project name" in text:
                return answers["name"]
            if "Project type" in text:
                return answers["kind"]
            if "description" in text:
                return answers["description"]
            if "goals" in text:
                return answers["goals"]
            if "constraints" in text:
                return answers["constraints"]
            return default
    
        monkeypatch.setattr(Prompt, "ask", fake_prompt)
    
        # Run chat command and assert it completes
        # Disable codex during unit test to avoid external dependency
        monkeypatch.setenv("OCEAN_DISABLE_CODEX", "1")
        monkeypatch.setenv("OCEAN_SIMPLE_FEED", "1")
        r = runner.invoke(app, ["chat"])  # do not call entrypoint directly in tests
>       assert r.exit_code == 0
E       assert 2 == 0
E        +  where 2 = <Result SystemExit(2)>.exit_code

tests/test_cli_chat.py:48: AssertionError
=========================== short test summary info ============================
FAILED tests/test_cli_chat.py::test_chat_non_interactive - assert 2 == 0

````

Exit code: 0
