# Test Report

Generated: 2025-09-05T20:43:52.664332

## Pytest Output

````

==================================== ERRORS ====================================
___________________ ERROR collecting tests/test_cli_chat.py ____________________
venv/lib/python3.13/site-packages/_pytest/python.py:498: in importtestmodule
    mod = import_path(
venv/lib/python3.13/site-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/usr/local/Cellar/python@3.13/3.13.6/Frameworks/Python.framework/Versions/3.13/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
venv/lib/python3.13/site-packages/_pytest/assertion/rewrite.py:186: in exec_module
    exec(co, module.__dict__)
tests/test_cli_chat.py:3: in <module>
    from ocean.cli import app, entrypoint
ocean/cli.py:21: in <module>
    from .agents import default_agents
ocean/agents.py:17: in <module>
    from . import codex_exec
E     File "/Users/reif/Documents/The Tauati's Life/not-secret-project-files/ocean/ocean/codex_exec.py", line 485
E       try:
E       ^^^
E   IndentationError: expected an indented block after 'if' statement on line 483
____________________ ERROR collecting tests/test_planner.py ____________________
venv/lib/python3.13/site-packages/_pytest/python.py:498: in importtestmodule
    mod = import_path(
venv/lib/python3.13/site-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/usr/local/Cellar/python@3.13/3.13.6/Frameworks/Python.framework/Versions/3.13/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
venv/lib/python3.13/site-packages/_pytest/assertion/rewrite.py:186: in exec_module
    exec(co, module.__dict__)
tests/test_planner.py:5: in <module>
    from ocean.planner import generate_backlog, write_backlog
ocean/planner.py:8: in <module>
    from .agents import default_agents
ocean/agents.py:17: in <module>
    from . import codex_exec
E     File "/Users/reif/Documents/The Tauati's Life/not-secret-project-files/ocean/ocean/codex_exec.py", line 485
E       try:
E       ^^^
E   IndentationError: expected an indented block after 'if' statement on line 483
=========================== short test summary info ============================
ERROR tests/test_cli_chat.py
ERROR tests/test_planner.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!

````

Exit code: 0
