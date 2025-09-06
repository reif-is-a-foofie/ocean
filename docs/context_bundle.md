## project.json

{
  "name": "🌊 OCEAN - Multi-Agent Software Engineering Orchestrator",
  "kind": "web",
  "description": "## Summary",
  "goals": [
    "testing enabled",
    "containerized",
    "fastapi backend",
    "static UI"
  ],
  "constraints": [
    "minimal dependencies"
  ],
  "createdAt": "2025-09-05T19:56:28.239293"
}



## backlog.json

[
  {
    "title": "Design web application architecture",
    "description": "Create frontend/backend architecture and data flow",
    "owner": "Moroni",
    "files_touched": [
      "docs/architecture.md",
      "docs/api_design.md"
    ]
  },
  {
    "title": "Create web interface design",
    "description": "Design web-based user interface and user experience",
    "owner": "Edna",
    "files_touched": [
      "ui/index.html",
      "ui/styles.css",
      "docs/design_system.md"
    ]
  },
  {
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
    ]
  },
  {
    "title": "Prepare codegen context",
    "description": "Compress project context and write docs/context_summary.md",
    "owner": "Mario",
    "files_touched": [
      "docs/context_summary.md"
    ]
  },
  {
    "title": "Add CI workflow",
    "description": "Set up automated testing and quality checks",
    "owner": "Mario",
    "files_touched": [
      ".github/workflows/ci.yml"
    ]
  },
  {
    "title": "Create Dockerfile",
    "description": "Containerize application for deployment",
    "owner": "Mario",
    "files_touched": [
      "Dockerfile",
      ".dockerignore"
    ]
  },
  {
    "title": "Create deployment config",
    "description": "Set up deployment configuration for cloud platforms",
    "owner": "Mario",
    "files_touched": [
      "devops/deploy.yaml"
    ]
  },
  {
    "title": "Start local runtime",
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8006/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  }
]



## plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)



## prd.md (truncated)

# 🌊 OCEAN - Multi-Agent Software Engineering Orchestrator

## Summary
# 🌊 OCEAN - Multi-Agent Software Engineering Orchestrator

## Goals
- testing enabled
- containerized
- fastapi backend
- static UI

## Constraints
- minimal dependencies

## Detected
- Kind: web
- Tech: Python/pyproject, requirements.txt, Dockerfile, GitHub Actions



## repository tree (depth=3)

# .

.DS_Store

.cursorrules

.dockerignore

.env

.env.example

.git/COMMIT_EDITMSG

.git/FETCH_HEAD

.git/HEAD

.git/config

.git/description

.git/hooks/applypatch-msg.sample

.git/hooks/commit-msg.sample

.git/hooks/fsmonitor-watchman.sample

.git/hooks/post-update.sample

.git/hooks/pre-applypatch.sample

.git/hooks/pre-commit.sample

.git/hooks/pre-merge-commit.sample

.git/hooks/pre-push.sample

.git/hooks/pre-rebase.sample

.git/hooks/pre-receive.sample

.git/hooks/prepare-commit-msg.sample

.git/hooks/push-to-checkout.sample

.git/hooks/update.sample

.git/index

.git/info/exclude

.git/logs/HEAD

.git/packed-refs

.github/workflows/ci.yml

.gitignore

.pytest_cache/.gitignore

.pytest_cache/CACHEDIR.TAG

.pytest_cache/README.md

CLEANUP-SUMMARY.md

Dockerfile

README.md

__pycache__/game.cpython-313.pyc

backend/__pycache__/app.cpython-313.pyc

backend/app.py

cli.py

cursor.json

devops/deploy.yaml

docs/adr/0001-record-architecture-decisions.md

docs/api_design.md

docs/architecture.md

docs/backlog.json

docs/cli_design.md

docs/context_bundle.md

docs/context_summary.md

docs/deploy.md

docs/first_sprint.md

docs/personas.yaml

docs/plan.md

docs/prd.md

docs/project.json

docs/repo_scout/workflow.yaml

docs/roadmap.md

docs/search_context.md

game.py

install-global.sh

logs/events-20250905-102830.jsonl

logs/events-20250905-110634.jsonl

logs/events-20250905-114922.jsonl

logs/events-20250905-115829.jsonl

logs/events-20250905-120433.jsonl

logs/events-20250905-122414.jsonl

logs/events-20250905-124816.jsonl

logs/events-20250905-130424.jsonl

logs/events-20250905-195554.jsonl

logs/mcp-edna-20250902-191119-rpc.log

logs/mcp-edna-20250902-191119.log

logs/mcp-edna-20250902-204937.log

logs/mcp-edna-20250902-204947.log

logs/mcp-edna-20250902-211429-rpc.log

logs/mcp-edna-20250902-211429.log

logs/mcp-edna-20250902-211729-rpc.log

logs/mcp-edna-20250902-211729.log

logs/mcp-edna-20250902-212113-rpc.log

logs/mcp-edna-20250902-212113.log

logs/mcp-edna-20250902-212122.log

logs/mcp-edna-20250902-212432-rpc.log

logs/mcp-edna-20250902-212432.log

logs/mcp-edna-20250903-095253-rpc.log

logs/mcp-edna-20250903-095253.log

logs/mcp-edna.log

logs/mcp-mario-20250902-191135-rpc.log

logs/mcp-mario-20250902-191135.log

logs/mcp-mario-20250902-204937.log

logs/mcp-mario-20250902-204947.log

logs/mcp-mario-20250902-211829-rpc.log

logs/mcp-mario-20250902-211829.log

logs/mcp-mario-20250902-212122.log

logs/mcp-mario-20250902-212213-rpc.log

logs/mcp-mario-20250902-212213.log

logs/mcp-mario-20250902-212532-rpc.log

logs/mcp-mario-20250902-212532.log

logs/mcp-mario-20250903-095313-rpc.log

logs/mcp-mario-20250903-095313.log

logs/mcp-mario.log

logs/mcp-moroni-20250902-191104-rpc.log

logs/mcp-moroni-20250902-191104.log

logs/mcp-moroni-20250902-204937.log

logs/mcp-moroni-20250902-204947.log

logs/mcp-moroni-20250902-210745-rpc.log

logs/mcp-moroni-20250902-210745.log

logs/mcp-moroni-20250902-211329-rpc.log

logs/mcp-moroni-20250902-211329.log

logs/mcp-moroni-20250902-211629-rpc.log

logs/mcp-moroni-20250902-211629.log

logs/mcp-moroni-20250902-212013-rpc.log

logs/mcp-moroni-20250902-212013.log

logs/mcp-moroni-20250902-212122.log

logs/mcp-moroni-20250902-212332-rpc.log

logs/mcp-moroni-20250902-212332.log

logs/mcp-moroni-20250903-095233-rpc.log

logs/mcp-moroni-20250903-095233.log

logs/mcp-moroni.log

logs/mcp-q-20250902-191119-rpc.log

logs/mcp-q-20250902-191119.log

logs/mcp-q-20250902-204937.log

logs/mcp-q-20250902-204947.log

logs/mcp-q-20250902-211429-rpc.log

logs/mcp-q-20250902-211429.log

logs/mcp-q-20250902-211729-rpc.log

logs/mcp-q-20250902-211729.log

logs/mcp-q-20250902-212113-rpc.log

logs/mcp-q-20250902-212113.log

logs/mcp-q-20250902-212122.log

logs/mcp-q-20250902-212432-rpc.log

logs/mcp-q-20250902-212432.log

logs/mcp-q-20250903-095253-rpc.log

logs/mcp-q-20250903-095253.log

logs/mcp-q.log

logs/mcp-smoke-20250902-224250-rpc.log

logs/mcp-smoke-20250902-224250.log

logs/mcp-smoke-20250903-093920-rpc.log

logs/mcp-smoke-20250903-093920.log

logs/mcp-smoke-20250903-123041-rpc.log

logs/mcp-smoke-20250903-123041.log

logs/mcp-smoke-rpc.log

logs/runtime-backend-20250902-191220.log

logs/runtime-backend-20250902-212832.log

logs/runtime-backend-20250903-095414.log

logs/runtime-backend-20250903-212830.log

logs/runtime-backend-20250903-213311.log

logs/runtime-backend-20250903-213759.log

logs/runtime-backend-20250903-213947.log

logs/runtime-backend-20250905-102841.log

logs/runtime-backend-20250905-130434.log

logs/runtime-ui-20250902-191220.log

logs/runtime-ui-20250902-212832.log

logs/runtime-ui-20250903-095414.log

logs/runtime-ui-20250903-212830.log

logs/runtime-ui-20250903-213311.log

logs/runtime-ui-20250903-213759.log

logs/runtime-ui-20250903-213947.log

logs/runtime-ui-20250905-102841.log

logs/runtime-ui-20250905-130434.log

logs/session-20250902-140754.log

logs/session-20250902-140757.log

logs/session-20250902-143400.log

logs/session-20250902-150610.log

logs/session-20250902-151016.log

logs/session-20250902-151039.log

logs/session-20250902-151833.log

logs/session-20250902-152417.log

logs/session-20250902-153505.log

logs/session-20250902-160416.log

logs/session-20250902-160423.log

logs/session-20250902-160720.log

logs/session-20250902-161327.log

logs/session-20250902-162207.log

logs/session-20250902-162249.log

logs/session-20250902-162251.log

logs/session-20250902-162428.log

logs/session-20250902-162519.log

logs/session-20250902-162530.log

logs/session-20250902-162545.log

logs/session-20250902-162547.log

logs/session-20250902-162711.log

logs/session-20250902-170453.log

logs/session-20250902-170708.log

logs/session-20250902-171102.log

logs/session-20250902-191011.log

logs/session-20250902-192135.log

logs/session-20250902-192154.log

logs/session-20250902-200952.log

logs/session-20250902-203455.log

logs/session-20250902-203741.log

logs/session-20250902-204932.log

logs/session-20250902-204942.log

logs/session-20250902-205103.log

logs/session-20250902-205513.log

logs/session-20250902-205517.log

logs/session-20250902-210740.log

logs/session-20250902-211324.log

logs/session-20250902-211624.log

logs/session-20250902-212008.log

logs/session-20250902-212118.log

logs/session-20250902-212327.log

logs/session-20250903-095214.log

logs/session-20250903-095228.log

logs/session-20250903-122200.log

logs/session-20250903-211742.log

logs/session-20250903-212703.log

logs/session-20250903-212718.log

logs/session-20250903-212731.log

logs/session-20250903-212817.log

logs/session-20250903-224319.log

logs/session-20250904-223136.log

logs/session-20250905-090455.log

logs/session-20250905-091033.log

logs/session-20250905-102332.log

logs/session-20250905-102652.log

logs/session-20250905-103348.log

logs/session-20250905-103719.log

logs/session-20250905-104038.log

logs/session-20250905-104404.log

logs/session-20250905-105758.log

logs/session-20250905-110125.log

logs/session-20250905-110256.log

logs/session-20250905-110743.log

logs/session-20250905-111447.log

logs/session-20250905-111536.log

logs/session-20250905-113320.log

logs/session-20250905-113757.log

logs/session-20250905-114319.log

logs/session-20250905-115328.log

logs/session-20250905-120233.log

logs/session-20250905-130424.log

logs/session-20250905-195554.log

main.py

ocean/__init__.py

ocean/__pycache__/__init__.cpython-313.pyc

ocean/__pycache__/agents.cpython-313.pyc

ocean/__pycache__/brave_search.cpython-313.pyc

ocean/__pycache__/cli.cpython-313.pyc

ocean/__pycache__/codex_client.cpython-313.pyc

ocean/__pycache__/codex_exec.cpython-313.pyc

ocean/__pycache__/codex_wrap.cpython-313.pyc

ocean/__pycache__/context.cpython-313.pyc

ocean/__pycache__/crewai_adapter.cpython-313.pyc

ocean/__pycache__/feed.cpython-313.pyc

ocean/__pycache__/mcp.cpython-313.pyc

ocean/__pycache__/mcp_client.cpython-313.pyc

ocean/__pycache__/models.cpython-313.pyc

ocean/__pycache__/persona.cpython-313.pyc

ocean/__pycache__/planner.cpython-313.pyc

ocean/__pycache__/tui_fallback.cpython-313.pyc

ocean/agents.py

ocean/brave_search.py

ocean/cli.py

ocean/codex_client.py

ocean/codex_exec.py

ocean/codex_wrap.py

ocean/context.py

ocean/crewai_adapter.py

ocean/feed.py

ocean/mcp.py

ocean/mcp_client.py

ocean/models.py

ocean/persona.py

ocean/planner.py

ocean/requirements.py

ocean/tools/__init__.py

ocean/tools/deploy.py

ocean/tools/design_system.py

ocean/tools/v0_cli.py

ocean/tui_fallback.py

ocean-cli

ocean-tui/Cargo.toml

ocean-tui/src/main.rs

ocean.egg-info/PKG-INFO

ocean.egg-info/SOURCES.txt

ocean.egg-info/dependency_links.txt

ocean.egg-info/entry_points.txt

ocean.egg-info/requires.txt

ocean.egg-info/top_level.txt

ocean_brython-snake/.DS_Store

ocean_brython-snake/.dockerignore

ocean_brython-snake/.ocean_workspace

ocean_brython-snake/Dockerfile

ocean_brython-snake/LICENSE

ocean_brython-snake/README.md

ocean_brython-snake/backend/app.py

ocean_brython-snake/brython.html

ocean_brython-snake/devops/deploy.yaml

ocean_brython-snake/docs/api_design.md

ocean_brython-snake/docs/architecture.md

ocean_brython-snake/docs/backlog.json

ocean_brython-snake/docs/context_bundle.md

ocean_brython-snake/docs/context_summary.md

ocean_brython-snake/docs/plan.md

ocean_brython-snake/docs/prd.md

ocean_brython-snake/docs/project.json

ocean_brython-snake/docs/test_report.md

ocean_brython-snake/javascript.html

ocean_brython-snake/logs/codex-edna-20250905-173926.log

ocean_brython-snake/logs/codex-edna-20250905-174258.log

ocean_brython-snake/logs/codex-edna-20250905-174747.log

ocean_brython-snake/logs/codex-edna-20250905-180608.log

ocean_brython-snake/logs/codex-edna-20250905-181039.log

ocean_brython-snake/logs/codex-edna-20250905-182436.log

ocean_brython-snake/logs/codex-edna-20250905-191929.log

ocean_brython-snake/logs/codex-edna-20250905-193235.log

ocean_brython-snake/logs/codex-edna-20250905-194405.log

ocean_brython-snake/logs/codex-mario-20250905-173930.log

ocean_brython-snake/logs/codex-mario-20250905-173934.log

ocean_brython-snake/logs/codex-mario-20250905-173938.log

ocean_brython-snake/logs/codex-mario-20250905-174303.log

ocean_brython-snake/logs/codex-mario-20250905-174308.log

ocean_brython-snake/logs/codex-mario-20250905-174312.log

ocean_brython-snake/logs/codex-mario-20250905-174810.log

ocean_brython-snake/logs/codex-mario-20250905-174832.log

ocean_brython-snake/logs/codex-mario-20250905-174855.log

ocean_brython-snake/logs/codex-mario-20250905-180631.log

ocean_brython-snake/logs/codex-mario-20250905-180654.log

ocean_brython-snake/logs/codex-mario-20250905-180717.log

ocean_brython-snake/logs/codex-mario-20250905-181102.log

ocean_brython-snake/logs/codex-mario-20250905-181124.log

ocean_brython-snake/logs/codex-mario-20250905-182448.log

ocean_brython-snake/logs/codex-mario-20250905-182501.log

ocean_brython-snake/logs/codex-mario-20250905-182513.log

ocean_brython-snake/logs/codex-mario-20250905-191941.log

ocean_brython-snake/logs/codex-mario-20250905-191953.log

ocean_brython-snake/logs/codex-mario-20250905-192005.log

ocean_brython-snake/logs/codex-mario-20250905-193248.log

ocean_brython-snake/logs/codex-mario-20250905-193301.log

ocean_brython-snake/logs/codex-mario-20250905-193314.log

ocean_brython-snake/logs/codex-mario-20250905-194417.log

ocean_brython-snake/logs/codex-mario-20250905-194430.log

ocean_brython-snake/logs/codex-mario-20250905-194442.log

ocean_brython-snake/logs/codex-moroni-20250905-141053.log

ocean_brython-snake/logs/codex-moroni-20250905-145111.log

ocean_brython-snake/logs/codex-moroni-20250905-145133.log

ocean_brython-snake/logs/codex-moroni-20250905-165415.log

ocean_brython-snake/logs/codex-moroni-20250905-170123.log

ocean_brython-snake/logs/codex-moroni-20250905-171105.log

ocean_brython-snake/logs/codex-moroni-20250905-171802.log

ocean_brython-snake/logs/codex-moroni-20250905-172815.log

ocean_brython-snake/logs/codex-moroni-20250905-173913.log

ocean_brython-snake/logs/codex-moroni-20250905-174245.log

ocean_brython-snake/logs/codex-moroni-20250905-174658.log

ocean_brython-snake/logs/codex-moroni-20250905-180518.log

ocean_brython-snake/logs/codex-moroni-20250905-180950.log

ocean_brython-snake/logs/codex-moroni-20250905-182408.log

ocean_brython-snake/logs/codex-moroni-20250905-191736.log

ocean_brython-snake/logs/codex-moroni-20250905-191901.log

ocean_brython-snake/logs/codex-moroni-20250905-193206.log

ocean_brython-snake/logs/codex-moroni-20250905-194045.log

ocean_brython-snake/logs/codex-moroni-20250905-194336.log

ocean_brython-snake/logs/codex-q-20250905-173921.log

ocean_brython-snake/logs/codex-q-20250905-174254.log

ocean_brython-snake/logs/codex-q-20250905-174724.log

ocean_brython-snake/logs/codex-q-20250905-180545.log

ocean_brython-snake/logs/codex-q-20250905-181016.log

ocean_brython-snake/logs/codex-q-20250905-182424.log

ocean_brython-snake/logs/codex-q-20250905-191917.log

ocean_brython-snake/logs/codex-q-20250905-193223.log

ocean_brython-snake/logs/codex-q-20250905-194102.log

ocean_brython-snake/logs/codex-q-20250905-194352.log

ocean_brython-snake/logs/events-20250905-141040.jsonl

ocean_brython-snake/logs/events-20250905-145058.jsonl

ocean_brython-snake/logs/events-20250905-145120.jsonl

ocean_brython-snake/logs/events-20250905-165350.jsonl

ocean_brython-snake/logs/events-20250905-170052.jsonl

ocean_brython-snake/logs/events-20250905-171038.jsonl

ocean_brython-snake/logs/events-20250905-171732.jsonl

ocean_brython-snake/logs/events-20250905-172758.jsonl

ocean_brython-snake/logs/events-20250905-173901.jsonl

ocean_brython-snake/logs/events-20250905-174233.jsonl

ocean_brython-snake/logs/events-20250905-174645.jsonl

ocean_brython-snake/logs/events-20250905-180502.jsonl

ocean_brython-snake/logs/events-20250905-180934.jsonl

ocean_brython-snake/logs/events-20250905-182353.jsonl

ocean_brython-snake/logs/events-20250905-191720.jsonl

ocean_brython-snake/logs/events-20250905-191846.jsonl

ocean_brython-snake/logs/events-20250905-193148.jsonl

ocean_brython-snake/logs/events-20250905-194030.jsonl

ocean_brython-snake/logs/events-20250905-194320.jsonl

ocean_brython-snake/logs/mcp-edna.log

ocean_brython-snake/logs/mcp-mario.log

ocean_brython-snake/logs/mcp-moroni.log

ocean_brython-snake/logs/mcp-q.log

ocean_brython-snake/logs/mcp-tony.log

ocean_brython-snake/logs/runtime-backend-20250905-173938.log

ocean_brython-snake/logs/runtime-backend-20250905-174312.log

ocean_brython-snake/logs/runtime-backend-20250905-174913.log

ocean_brython-snake/logs/runtime-backend-20250905-180735.log

ocean_brython-snake/logs/runtime-backend-20250905-182523.log

ocean_brython-snake/logs/runtime-backend-20250905-192013.log

ocean_brython-snake/logs/runtime-backend-20250905-193321.log

ocean_brython-snake/logs/runtime-backend-20250905-194449.log

ocean_brython-snake/logs/runtime-ui-20250905-173938.log

ocean_brython-snake/logs/runtime-ui-20250905-174312.log

ocean_brython-snake/logs/runtime-ui-20250905-174913.log

ocean_brython-snake/logs/runtime-ui-20250905-180735.log

ocean_brython-snake/logs/runtime-ui-20250905-182523.log

ocean_brython-snake/logs/runtime-ui-20250905-192013.log

ocean_brython-snake/logs/runtime-ui-20250905-193321.log

ocean_brython-snake/logs/runtime-ui-20250905-194449.log

ocean_brython-snake/logs/session-20250905-141040.log

ocean_brython-snake/logs/session-20250905-145058.log

ocean_brython-snake/logs/session-20250905-145120.log

ocean_brython-snake/logs/session-20250905-165350.log

ocean_brython-snake/logs/session-20250905-170052.log

ocean_brython-snake/logs/session-20250905-171038.log

ocean_brython-snake/logs/session-20250905-171732.log

ocean_brython-snake/logs/session-20250905-172758.log

ocean_brython-snake/logs/session-20250905-173901.log

ocean_brython-snake/logs/session-20250905-174233.log

ocean_brython-snake/logs/session-20250905-174645.log

ocean_brython-snake/logs/session-20250905-180502.log

ocean_brython-snake/logs/session-20250905-180934.log

ocean_brython-snake/logs/session-20250905-182353.log

ocean_brython-snake/logs/session-20250905-191720.log

ocean_brython-snake/logs/session-20250905-191846.log

ocean_brython-snake/logs/session-20250905-193148.log

ocean_brython-snake/logs/session-20250905-194030.log

ocean_brython-snake/logs/session-20250905-194320.log

ocean_brython-snake/snake.js

ocean_brython-snake/snake.py

ocean_brython-snake/ui/index.html

ocean_brython-snake/ui/styles.css

ocean_brython-snake/venv/.gitignore

ocean_brython-snake/venv/pyvenv.cfg

ocean_entrypoint.py

ocean_reif/.claude.json.backup

pyproject.toml

requirements.txt

scripts/mcp_trace.py

setup.sh

test_output.log

tests/__pycache__/test_cli_chat.cpython-313-pytest-8.4.1.pyc

tests/__pycache__/test_codex_e2e.cpython-313-pytest-8.4.1.pyc

tests/__pycache__/test_planner.cpython-313-pytest-8.4.1.pyc

tests/test_cli_chat.py

tests/test_codex_e2e.py

tests/test_planner.py

ui/config.js

ui/index.html

ui/styles.css

venv/.gitignore

venv/bin/Activate.ps1

venv/bin/activate

venv/bin/activate.csh

venv/bin/activate.fish

venv/bin/dotenv

venv/bin/email_validator

venv/bin/fastapi

venv/bin/httpx

venv/bin/markdown-it

venv/bin/ocean

venv/bin/pip

venv/bin/pip3

venv/bin/pip3.13

venv/bin/py.test

venv/bin/pygmentize

venv/bin/pytest

venv/bin/python

venv/bin/python3

venv/bin/python3.13

venv/bin/typer

venv/bin/uvicorn

venv/bin/watchfiles

venv/bin/websockets

venv/pyvenv.cfg

# backend

backend/__pycache__/app.cpython-313.pyc

backend/app.py

# ui

ui/config.js

ui/index.html

ui/styles.css

# devops

devops/deploy.yaml

# docs

docs/adr/0001-record-architecture-decisions.md

docs/api_design.md

docs/architecture.md

docs/backlog.json

docs/cli_design.md

docs/context_bundle.md

docs/context_summary.md

docs/deploy.md

docs/first_sprint.md

docs/personas.yaml

docs/plan.md

docs/prd.md

docs/project.json

docs/repo_scout/workflow.yaml

docs/roadmap.md

docs/search_context.md


## file samples (truncated)

### backend/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Ocean Project PRD — Web Tic-Tac-Toe", version="0.1.0")

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

# TODO: Add more endpoints based on project requirements
# Generated by OCEAN using Codex MCP


### ui/index.html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ocean Project PRD — Web Tic-Tac-Toe - OCEAN Generated</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🌊 Ocean Project PRD — Web Tic-Tac-Toe</h1>
            <p>Generated by OCEAN using Codex MCP</p>
        </header>
        
        <main>
            <section class="hero">
                <h2>Welcome to Ocean Project PRD — Web Tic-Tac-Toe</h2>
                <p>## Summary</p>
                <div class="goals">
                    <h3>Project Goals:</h3>
                    <ul>
                        <li>Single‑player Tic‑Tac‑Toe vs computer</li>
<li>Simple</li>
<li>responsive UI (HTML/CSS/JS)</li>
<li>Minimal backend with health check and scores API</li>
<li>Persist high scores locally (file or SQLite)</li>
<li>Clear instructions and quick start script</li>
                    </ul>
                </div>
            </section>
            
            <section class="features">
                <h3>Features</h3>
                <p>Application features will be implemented here...</p>
            </section>
        </main>
        
        <footer>
            <p>Built by OCEAN's AI engineering team 🚀</p>
        </footer>
    </div>
</body>
</html>

### ui/styles.css

/* Ocean Project PRD — Web Tic-Tac-Toe - Styles */
/* Generated by OCEAN using Codex MCP */

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

header {
    text-align: center;
    margin-bottom: 3rem;
}

header h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.hero {
    background: rgba(255,255,255,0.1);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
}

.goals ul {
    text-align: left;
    display: inline-block;
}

.features {
    background: rgba(255,255,255,0.1);
    padding: 2rem;
    border-radius: 15px;
}

footer {
    text-align: center;
    margin-top: 3rem;
    opacity: 0.8;
}

### docs/adr/0001-record-architecture-decisions.md

# 1. Record architecture decisions

Date: 2025-09-02

## Status

Accepted

## Context

We will document significant decisions as ADRs to keep a transparent history.

## Decision

Use markdown ADRs under `docs/adr/` with incrementing numbers and dates.

## Consequences

Pros: clear decision trail; easy reviews. Cons: minor overhead to maintain.



### docs/api_design.md

# Ocean Project PRD — Web Tic-Tac-Toe - API Design

## Endpoints
- GET `/` → Welcome payload
- GET `/healthz` → `{ ok: true, status: 'healthy' }`

## Future endpoints
- Add domain-specific APIs here

Generated by OCEAN (local fallback)


### docs/architecture.md

# Ocean Project PRD — Web Tic-Tac-Toe - Web Architecture

## Project Overview
- **Type**: Web Application
- **Goals**: Single‑player Tic‑Tac‑Toe vs computer, Simple, responsive UI (HTML/CSS/JS), Minimal backend with health check and scores API, Persist high scores locally (file or SQLite), Clear instructions and quick start script
- **Constraints**: Minimal dependencies, Work offline, no cloud services required

## Architecture Design
- **Frontend**: Static UI served from `ui/`
- **Backend**: FastAPI app in `backend/app.py`
- **Endpoints**: `/` (welcome), `/healthz` (health)
- **Deployment**: Containerized with Docker; CI via GitHub Actions

Generated by OCEAN (local fallback)


### docs/backlog.json

[
  {
    "title": "Design web application architecture",
    "description": "Create frontend/backend architecture and data flow",
    "owner": "Moroni",
    "files_touched": [
      "docs/architecture.md",
      "docs/api_design.md"
    ]
  },
  {
    "title": "Create web interface design",
    "description": "Design web-based user interface and user experience",
    "owner": "Edna",
    "files_touched": [
      "ui/index.html",
      "ui/styles.css",
      "docs/design_system.md"
    ]
  },
  {
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
    ]
  },
  {
    "title": "Prepare codegen context",
    "description": "Compress project context and write docs/context_summary.md",
    "owner": "Mario",
    "files_touched": [
      "docs/context_summary.md"
    ]
  },
  {
    "title": "Add CI workflow",
    "description": "Set up automated testing and quality checks",
    "owner": "Mario",
    "files_touched": [
      ".github/workflows/ci.yml"
    ]
  },
  {
    "title": "Create Dockerfile",
    "description": "Containerize application for deployment",
    "owner": "Mario",
    "files_touched": [
      "Dockerfile",
      ".dockerignore"
    ]
  },
  {
    "title": "Create deployment config",
    "description": "Set up deployment configuration for cloud platforms",
    "owner": "Mario",
    "files_touched": [
      "devops/deploy.yaml"
    ]
  },
  {
    "title": "Start local runtime",
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8006/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  }
]


### docs/cli_design.md

# Weather CLI - CLI Interface Design

## Design Principles
- **Simplicity**: Clear, intuitive commands
- **Consistency**: Uniform command structure
- **Feedback**: Clear response to user actions
- **Help**: Comprehensive help system

## Command Structure
```
weather_cli [command] [options]
```

## User Interaction Flow
1. **Startup**: Welcome message and available commands
2. **Command Input**: Clear prompts and validation
3. **Execution**: Progress feedback and results
4. **Error Handling**: Helpful error messages
5. **Completion**: Summary and next steps

## Terminal UX Patterns
- Color coding for different types of output
- Progress bars for long operations
- Clear separation between sections
- Consistent formatting

Generated by OCEAN using Codex MCP


### docs/context_bundle.md

## project.json

{
  "name": "Ocean Project PRD — Web Tic-Tac-Toe",
  "kind": "web",
  "description": "## Summary",
  "goals": [
    "Single‑player Tic‑Tac‑Toe vs computer",
    "Simple",
    "responsive UI (HTML/CSS/JS)",
    "Minimal backend with health check and scores API",
    "Persist high scores locally (file or SQLite)",
    "Clear instructions and quick start script"
  ],
  "constraints": [
    "Minimal dependencies",
    "Work offline",
    "no cloud services required"
  ],
  "createdAt": "2025-09-05T12:02:48.368256"
}



## backlog.json

[
  {
    "title": "Design web application architecture",
    "description": "Create frontend/backend architecture and data flow",
    "owner": "Moroni",
    "files_touched": [
      "docs/architecture.md",
      "docs/api_design.md"
    ]
  },
  {
    "title": "Create web interface design",
    "description": "Design web-based user interface and user experience",
    "owner": "Edna",
    "files_touched": [
      "ui/index.html",
      "ui/styles.css",
      "docs/design_system.md"
    ]
  },
  {
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
    ]
  },
  {
    "title": "Prepare codegen context",
    "description": "Compress project context and write docs/context_summary.md",
    "owner": "Mario",
    "files_touched": [
      "docs/context_summary.md"
    ]
  },
  {
    "title": "Add CI workflow",
    "description": "Set up automated testing and quality checks",
    "owner": "Mario",
    "files_touched": [
      ".github/workflows/ci.yml"
    ]
  },
  {
    "title": "Create Dockerfile",
    "description": "Containerize application for deployment",
    "owner": "Mario",
    "files_touched": [
      "Dockerfile",
      ".dockerignore"
    ]
  },
  {
    "title": "Create deployment config",
    "description": "Set up deployment configuration for cloud platforms",
    "owner": "Mario",
    "files_touched": [
      "devops/deploy.yaml"
    ]
  },
  {
    "title": "Start local runtime",
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8005/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  }
]



## plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)



## prd.md (truncated)

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
- 

### docs/context_summary.md

## project.json

{
  "name": "Ocean Project PRD — Web Tic-Tac-Toe",
  "kind": "web",
  "description": "## Summary",
  "goals": [
    "Single‑player Tic‑Tac‑Toe vs computer",
    "Simple",
    "responsive UI (HTML/CSS/JS)",
    "Minimal backend with health check and scores API",
    "Persist high scores locally (file or SQLite)",
    "Clear instructions and quick start script"
  ],
  "constraints": [
    "Minimal dependencies",
    "Work offline",
    "no cloud services required"
  ],
  "createdAt": "2025-09-05T13:04:32.896244"
}


## backlog.json

[
  {
    "title": "Design web application architecture",
    "description": "Create frontend/backend architecture and data flow",
    "owner": "Moroni",
    "files_touched": [
      "docs/architecture.md",
      "docs/api_design.md"
    ]
  },
  {
    "title": "Create web interface design",
    "description": "Design web-based user interface and user experience",
    "owner": "Edna",
    "files_touched": [
      "ui/index.html",
      "ui/styles.css",
      "docs/design_system.md"
    ]
  },
  {
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
    ]
  },
  {
    "title": "Prepare codegen context",
    "description": "Compress project context and write docs/context_summary.md",
    "owner": "Mario",
    "files_touched": [
      "docs/context_summary.md"
    ]
  },
  {
    "title": "Add CI workflow",
    "description": "Set up automated testing and quality checks",
    "owner": "Mario",
    "files_touched": [
      ".github/workflows/ci.yml"
    ]
  },
  {
    "title": "Create Dockerfile",
    "description": "Containerize application for deployment",
    "owner": "Mario",
    "files_touched": [
      "Dockerfile",
      ".dockerignore"
    ]
  },
  {
    "title": "Create deployment config",
    "description": "Set up deployment configuration for cloud platforms",
    "owner": "Mario",
    "files_touched": [
      "devops/deploy.yaml"
    ]
  },
  {
    "title": "Start local runtime",
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8005/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  }
]


## plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)


## prd.md (truncated)

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
- Fro

### docs/deploy.md

# Deployment (Stub)

This is a placeholder deployment guide. Replace placeholders with your chosen platform (Render, Railway, etc.).

- Build image: `docker build -t ocean:latest .`
- Run locally: `docker run -p 8000:8000 ocean:latest`
- Health check: `curl http://localhost:8000/healthz`
- Render: see `devops/render.yaml` and configure service.

Environment variables (examples):
- `PORT=8000`
- `ENV=production`

Use `ocean deploy --dry-run` to preview steps.



### docs/first_sprint.md

# First Sprint - OCEAN Generated App

## Quick Start

### Backend
```bash
# Install dependencies
pip install -e .
pip install fastapi[all] uvicorn pytest httpx

# Run backend
uvicorn backend.app:app --reload
```

### Frontend
```bash
# Serve UI (from project root)
python -m http.server -d ui 5173
```

### Testing
```bash
# Run tests
pytest

# Run specific test
pytest backend/tests/test_healthz.py -v
```

## What's Generated

- **Backend**: FastAPI app with `/healthz` endpoint
- **Frontend**: Responsive HTML with health check
- **Tests**: pytest suite for backend endpoints
- **CI/CD**: GitHub Actions workflow
- **Docker**: Containerization ready
- **Deploy**: Render deployment config

## Next Steps

1. Customize `backend/app.py` with your business logic
2. Update `ui/index.html` with your design
3. Add more tests in `backend/tests/`
4. Deploy with `ocean deploy --dry-run` to see the plan


### docs/personas.yaml

agents:
  Mario:
    emoji: "🍄"
    traits:
      - Pragmatic, resilient, production-first
      - Optimistic and energetic, fixes “clogs” fast
    diction:
      - "It’s-a me, Mario!", "Let’s-a go!", "Here we go!"
      - Simple exclamations: "Mamma mia!", "Wahoo!", "Woo-hoo!"
    avoid:
      - Overly technical explanations
      - Corporate jargon or long theory
    style:
      - Short, joyful bursts with exclamation
      - Warm, plainspoken; playful metaphors (pipes, plumbing)
    calibration:
      do: "Rollback, fix the pipeline, then andiamo! 🍄"
      dont: "We must consider implementing a comprehensive remediation strategy."
    context_hooks:
      deploy: "Frames deploys as fixing pipes or unblocking flows"
      ci_failure: "Treats errors as clogs to clear; upbeat urgency"
      infra: "Encourages resilience and retries"
    quotes:
      - "It’s-a me, Mario!"
      - "Let’s-a go!"
      - "Here we go!"
      - "Mamma mia!"
      - "Okey-dokey!"
      - "Wahoo!"
      - "Woo-hoo!"

  Q:
    emoji: "🔫"
    traits:
      - Dry wit, surgical precision, loves gadgets
      - Test-driven, obsessed with safety nets
    diction:
      - "Pay attention, 007."
      - Talks in terms of specs, prototypes, guardrails
    avoid:
      - Overconfidence without tests
      - Casual slang, imprecision
    style:
      - Polished, clipped sentences
      - Often embeds tiny demos/tests
    calibration:
      do: "Red → Green → Refactor. Guardrails in place."
      dont: "I think it probably works."
    context_hooks:
      backend: "Presents APIs like gadgets; emphasizes contracts"
      ci_failure: "Zeroes in on failing assertions"
      design_review: "Insists on specs and coverage before merge"
    quotes:
      - "Pay attention, 007."
      - "Never let them see you bleed. Always have an escape plan."
      - "There are only about six people in the world who could set up fail-safes like this… I invented them."
      - "I’ve always tried to teach you two things..."
      - "Please return it in one piece."
      - "I can do more damage on my laptop in my pajamas before my first cup of Earl Grey than you can do in a year."
      - "Wry gadget jokes after explosions (paraphrased)"

  Tony:
    emoji: "🚀"
    traits:
      - Brash, charismatic, experimental
      - Thrives in chaos, stress-tests boundaries
    diction:
      - "Sometimes you gotta run before you can walk."
      - Sarcasm, pop culture riffs, playful arrogance
    avoid:
      - Bureaucracy, excess caution
      - Dry formalism
    style:
      - Fast, witty banter
      - Crisp repro steps when bug-hunting
    calibration:
      do: "Edge cases tested. Broke on #2, fixed it. 🚀"
      dont: "We’ll table this for a six-month review."
    context_hooks:
      deploy: "Pushes bold moves, prototypes in prod"
      ci_failure: "Treats bugs like puzzles; playful fixes"
      design: "Suggests flashy shortcuts, hacks"
    quotes:
      - "Sometimes you’ve gotta run before you can walk."
      - "Don’t do anything I would do… and definitely don’t do anything I wouldn’t do."
      - "It’s not about how much we lost, it’s about how much we have left."
      - "Everyone wants a happy ending. Not everyone gets it."
      - "I am Iron Man."
      - "Genius, billionaire, playboy, philanthropist."
      - "I built this in a cave with scraps!"

  Moroni:
    emoji: "🕹️"
    traits:
      - Calm commander, strategic, principle-driven
      - Decomposes missions into phases
    diction:
      - "Acceptance criteria", "standards", "banners"
      - Scriptural cadence; invokes God, liberty, duty
    avoid:
      - Vagueness, improvisation without plan
      - Casual irreverence
    style:
      - Formal, structured; lists phases
      - Motivational, disciplined tone
    calibration:
      do: "Phase 1: gather resources. Phase 2: secure interfaces. 🕹️"
      dont: "Let’s just wing it and hope for the best."
    context_hooks:
      planning: "Frames goals as campaigns with standards"


### docs/plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)


### docs/prd.md

# 🌊 OCEAN - Multi-Agent Software Engineering Orchestrator

## Summary
# 🌊 OCEAN - Multi-Agent Software Engineering Orchestrator

## Goals
- testing enabled
- containerized
- fastapi backend
- static UI

## Constraints
- minimal dependencies

## Detected
- Kind: web
- Tech: Python/pyproject, requirements.txt, Dockerfile, GitHub Actions


### docs/project.json

{
  "name": "🌊 OCEAN - Multi-Agent Software Engineering Orchestrator",
  "kind": "web",
  "description": "## Summary",
  "goals": [
    "testing enabled",
    "containerized",
    "fastapi backend",
    "static UI"
  ],
  "constraints": [
    "minimal dependencies"
  ],
  "createdAt": "2025-09-05T19:56:28.239293"
}


### docs/repo_scout/workflow.yaml

# Ocean Agent Init — Repo-Scout Workflow

general:
  context: |
    All agents assume repo context exists with README.md and code folders.
    Each agent runs an initial `codex exec` pass scoped to its domain.
    Output = "findings + suggestions" → delivered back to Moroni.
    Moroni integrates and orchestrates next steps.

agents:
  Moroni:
    emoji: "🕹️"
    role: planning, orchestration
    kickoff: |
      Collect reports from all agents.
      Synthesize into architecture & roadmap.
      Approve/reject proposals, then assign phases.

  Q:
    emoji: "🔫"
    role: APIs, services, tests
    kickoff: |
      codex exec --scope backend --task "Audit backend files, propose 2 PRs."
      Send results to Moroni.

  Edna:
    emoji: "🍩"
    role: frontend, styles, UI docs
    kickoff: |
      codex exec --scope frontend --task "Review UI code, suggest 2 UX improvements."
      Send results to Moroni.

  Mario:
    emoji: "🍄"
    role: CI/CD, Docker, deploys
    kickoff: |
      codex exec --scope infra --task "Audit workflows/Docker, suggest 1 infra improvement."
      Send results to Moroni.

  Tony:
    emoji: "🚀"
    role: testing, stress, chaos
    kickoff: |
      codex exec --scope tests --task "Run tests, stress core loop, report issues."
      Send results to Moroni.



### docs/roadmap.md

# Roadmap (Initial)

- M1: Bootstrap CLI and logs
- M2: Clarification and project spec
- M3: Crew intros and backlog
- M4: Backend/UI/CI scaffolds
- M5: Tests and iteration loop
- M6: Deploy dry-run and docs



### docs/search_context.md

# Brave Search Context


## FastAPI best practices 2025
- [GitHub - zhanymkanov/fastapi-best-practices: FastAPI Best Practices and Conventions we used at our startup](https://github.com/zhanymkanov/fastapi-best-practices) — <strong>FastAPI</strong> <strong>Best</strong> <strong>Practices</strong> and Conventions we used at our startup - zhanymkanov/<strong>fastapi</strong>-<strong>best</strong>-<strong>practices</strong>
- [Structuring a FastAPI Project: Best Practices - DEV Community](https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6) — <strong>FastAPI</strong> is a powerful and efficient web framework for building APIs with Python. However, as projects...
- [FastAPI Best Practices: A Condensed Guide with Examples](https://developer-service.blog/fastapi-best-practices-a-condensed-guide-with-examples/) — <strong>FastAPI</strong> is a modern, high-performance web framework for building APIs with Python, based on standard Python type hints.
- [r/Python on Reddit: FastAPI Best Practices](https://www.reddit.com/r/Python/comments/wrt7om/fastapi_best_practices/) — 443 votes, 79 comments. Although <strong>FastAPI</strong> is a great framework with fantastic documentation, it&#x27;s not quite obvious how to build larger projects for…
- [python - What are the best practices for structuring a FastAPI project? - Stack Overflow](https://stackoverflow.com/questions/64943693/what-are-the-best-practices-for-structuring-a-fastapi-project) — The problem that I want to solve related the project setup: Good names of directories so that their purpose is clear. Keeping all project files (including virtualenv) in one place, so I can easily...



# Brave Search Context


## FastAPI best practices 2025
- [GitHub - zhanymkanov/fastapi-best-practices: FastAPI Best Practices and Conventions we used at our startup](https://github.com/zhanymkanov/fastapi-best-practices) — <strong>FastAPI</strong> <strong>Best</strong> <strong>Practices</strong> and Conventions we used at our startup - zhanymkanov/<strong>fastapi</strong>-<strong>best</strong>-<strong>practices</strong>
- [Structuring a FastAPI Project: Best Practices - DEV Community](https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6) — <strong>FastAPI</strong> is a powerful and efficient web framework for building APIs with Python. However, as projects...
- [FastAPI Best Practices: A Condensed Guide with Examples](https://developer-service.blog/fastapi-best-practices-a-condensed-guide-with-examples/) — <strong>FastAPI</strong> is a modern, high-performance web framework for building APIs with Python, based on standard Python type hints.
- [r/Python on Reddit: FastAPI Best Practices](https://www.reddit.com/r/Python/comments/wrt7om/fastapi_best_practices/) — 443 votes, 79 comments. Although <strong>FastAPI</strong> is a great framework with fantastic documentation, it&#x27;s not quite obvious how to build larger projects for…
- [python - What are the best practices for structuring a FastAPI project? - Stack Overflow](https://stackoverflow.com/questions/64943693/what-are-the-best-practices-for-structuring-a-fastapi-project) — The problem that I want to solve related the project setup: Good names of directories so that their purpose is clear. Keeping all project files (including virtualenv) in one place, so I can easily...

## HTML CSS landing page accessibility checklist
- [WebAIM: WebAIM's WCAG 2 Checklist](https://webaim.org/standards/wcag/checklist) — Images that do not convey content, ... as <strong>CSS</strong> backgrounds. All linked images have descriptive alternative text. Equivalent alternatives to complex images are provided in context or on a separate linked <strong>page</strong>. Form buttons have a descriptive value. Inputs have associated <strong>accessible</strong> ...
- [HTML: A good basis for accessibility - Learn web development | MDN](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML) — A great deal of web content can be made <strong>accessible</strong> just by making sure the correct Hypertext Markup Language elements are used for the correct purpose at all times. This article looks in detail at how <strong>HTML</strong> can be used to ensure maximum <strong>accessibility</strong>.
- [Easy Checks – A First Review of Web Accessibility | Web Accessibility Initiative (WAI) | W3C](https://www.w3.org/WAI/test-evaluate/preliminary/) — Open the web page you are checking. <strong>In the toolbar, select &quot;Images&quot;, then &quot;Remove Images&quot;.</strong> Or, with the keyboard: Ctrl+Alt+4, then arrow down to &quot;Remove Images&quot;. In the toolbar, select &quot;CSS&quot;, then &quot;Disable CSS&quot;.
- [Web Accessibility Checklist](https://www.webaccessibilitychecklist.com/) — <strong>Adding an HTML sitemap page (which links to every page on your website).</strong> Including a search function on every page. Providing a clear and consistent main navigation menu. ... Do not rely on hover states to convey information as this approach is not screen reader, keyboard or mobile accessible.
- [Accessibility | MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility) — <strong>Accessibility</strong> (often abbreviated to A11y — as in, &quot;a&quot;, then 11 characters, and then &quot;y&quot;) in web development means enabling as many people as possible to use websites, even when those people&#x27;s abilities are limited in some way.

