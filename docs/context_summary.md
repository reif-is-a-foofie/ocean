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
  "vision": "## Summary",
  "ai_identity": "Your coding partner on **🌊 OCEAN - Multi-Agent Software Engineering Orchestrator** — Ocean runs the crew and timing; you steer goals and say when we're done.",
  "createdAt": "2026-05-12T10:15:46.528184"
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
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
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
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8004/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  },
  {
    "title": "Run test suite and write report",
    "description": "Execute pytest (if present) and record a concise report",
    "owner": "Tony",
    "files_touched": [
      "docs/test_report.md"
    ]
  }
]



## plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)
- [Tony] Run test suite and write report — docs/test_report.md



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
- Tech: Python/pyproject, requirements.txt, Node/package.json, Dockerfile, GitHub Actions



## repository tree (depth=3)

# .

.cursor/rules/run-ocean.mdc

.cursorrules

.dockerignore

.env.example

.git/COMMIT_EDITMSG

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

.git/hooks/sendemail-validate.sample

.git/hooks/update.sample

.git/index

.git/info/exclude

.git/logs/HEAD

.git/packed-refs

.github/workflows/ci.yml

.github/workflows/personas-daily.yml

.gitignore

.ocean/actors.json

.ocean/chat.jsonl

.ocean/dev_ready.json

.ocean/jobs.json

.pytest_cache/.gitignore

.pytest_cache/CACHEDIR.TAG

.pytest_cache/README.md

.venv/bin/Activate.ps1

.venv/bin/activate

.venv/bin/activate.csh

.venv/bin/activate.fish

.venv/bin/fastapi

.venv/bin/httpx

.venv/bin/markdown-it

.venv/bin/ocean

.venv/bin/ocean-mcp

.venv/bin/pip

.venv/bin/pip3

.venv/bin/pip3.11

.venv/bin/py.test

.venv/bin/pygmentize

.venv/bin/pytest

.venv/bin/python

.venv/bin/python3

.venv/bin/python3.11

.venv/bin/typer

.venv/bin/uvicorn

.venv/pyvenv.cfg

AUDIENCE.md

CHANGELOG.md

CLEANUP-SUMMARY.md

DECISIONS.md

Dockerfile

FEEDBACK.md

POSITIONING.md

PRODUCT_PRINCIPLES.md

ROADMAP.md

TASKS.md

UX_RULES.md

VISION.md

backend/__pycache__/app.cpython-311.pyc

backend/app.py

bin/ocean.js

cli.py

cursor.json

devops/deploy.yaml

devops/regression.md

docs/adr/0001-record-architecture-decisions.md

docs/api_design.md

docs/architecture.md

docs/backlog.json

docs/cli_design.md

docs/context_bundle.md

docs/context_summary.md

docs/deploy.md

docs/first_sprint.md

docs/mcp_cursor.md

docs/ocean_prefs.json

docs/personas.yaml

docs/plan.md

docs/prd.md

docs/project.json

docs/repo_scout/workflow.yaml

docs/roadmap.md

docs/search_context.md

docs/test_report.md

docs/textual_tmux_pilot_scenarios.md

game.py

install-global.sh

logs/codex-edna-20260511-093117.log

logs/codex-edna-20260512-100816.log

logs/codex-edna-20260512-100856.log

logs/codex-edna-20260512-101014.log

logs/codex-last-edna-20260512-100816.txt

logs/codex-last-edna-20260512-100856.txt

logs/codex-last-edna-20260512-101014.txt

logs/codex-last-mario-20260512-101240.txt

logs/codex-last-mario-20260512-101307.txt

logs/codex-last-mario-20260512-101330.txt

logs/codex-last-mario-20260512-101415.txt

logs/codex-last-mario-20260512-101435.txt

logs/codex-last-mario-20260512-101457.txt

logs/codex-last-mario-20260512-101617.txt

logs/codex-last-mario-20260512-101637.txt

logs/codex-last-moroni-20260512-100637.txt

logs/codex-last-moroni-20260512-100711.txt

logs/codex-last-moroni-20260512-100830.txt

logs/codex-last-q-20260512-100759.txt

logs/codex-last-q-20260512-100840.txt

logs/codex-last-q-20260512-100958.txt

logs/codex-mario-20260511-093213.log

logs/codex-mario-20260511-093306.log

logs/codex-mario-20260511-093410.log

logs/codex-mario-20260512-101240.log

logs/codex-mario-20260512-101307.log

logs/codex-mario-20260512-101330.log

logs/codex-mario-20260512-101415.log

logs/codex-mario-20260512-101435.log

logs/codex-mario-20260512-101457.log

logs/codex-mario-20260512-101617.log

logs/codex-mario-20260512-101637.log

logs/codex-moroni-20260511-092924.log

logs/codex-moroni-20260512-100637.log

logs/codex-moroni-20260512-100711.log

logs/codex-moroni-20260512-100830.log

logs/codex-q-20260511-093023.log

logs/codex-q-20260512-100759.log

logs/codex-q-20260512-100840.log

logs/codex-q-20260512-100958.log

logs/codex-test-last.txt

logs/events-20250905-102830.jsonl

logs/events-20250905-110634.jsonl

logs/events-20250905-114922.jsonl

logs/events-20250905-115829.jsonl

logs/events-20250905-120433.jsonl

logs/events-20250905-122414.jsonl

logs/events-20250905-124816.jsonl

logs/events-20250905-130424.jsonl

logs/events-20250905-195554.jsonl

logs/events-20250905-195727.jsonl

logs/events-20250905-195814.jsonl

logs/events-20250905-195902.jsonl

logs/events-20250905-195949.jsonl

logs/events-20250905-200033.jsonl

logs/events-20250905-200120.jsonl

logs/events-20250905-200207.jsonl

logs/events-20250905-200255.jsonl

logs/events-20250905-200342.jsonl

logs/events-20250905-200430.jsonl

logs/events-20250905-200517.jsonl

logs/events-20250905-204210.jsonl

logs/events-20250905-204302.jsonl

logs/events-20250905-204353.jsonl

logs/events-20250905-204417.jsonl

logs/events-20250905-204445.jsonl

logs/events-20250905-204510.jsonl

logs/events-20250905-204539.jsonl

logs/events-20250905-204602.jsonl

logs/events-20250905-204630.jsonl

logs/events-20250905-204654.jsonl

logs/events-20250905-204722.jsonl

logs/events-20250905-204747.jsonl

logs/events-20250905-204815.jsonl

logs/events-20250905-204824.jsonl

logs/events-20250905-204840.jsonl

logs/events-20250905-204909.jsonl

logs/events-20250905-204919.jsonl

logs/events-20250905-204934.jsonl

logs/events-20250905-205004.jsonl

logs/events-20250905-205013.jsonl

logs/events-20250905-205027.jsonl

logs/events-20250905-205031.jsonl

logs/events-20250905-205057.jsonl

logs/events-20250905-205106.jsonl

logs/events-20250905-205122.jsonl

logs/events-20250905-205126.jsonl

logs/events-20250905-205133.jsonl

logs/events-20250905-205141.jsonl

logs/events-20250905-205144.jsonl

logs/events-20250905-205146.jsonl

logs/events-20250905-205150.jsonl

logs/events-20250905-205158.jsonl

logs/events-20250905-205202.jsonl

logs/events-20250905-205204.jsonl

logs/events-20250905-205208.jsonl

logs/events-20250905-205217.jsonl

logs/events-20250905-205220.jsonl

logs/events-20250905-205223.jsonl

logs/events-20250905-205227.jsonl

logs/events-20250905-205235.jsonl

logs/events-20250905-205237.jsonl

logs/events-20250905-205239.jsonl

logs/events-20250905-205242.jsonl

logs/events-20250905-205253.jsonl

logs/events-20250905-205254.jsonl

logs/events-20250905-205256.jsonl

logs/events-20250905-205258.jsonl

logs/events-20250905-205309.jsonl

logs/events-20250905-205312.jsonl

logs/events-20250905-205314.jsonl

logs/events-20250905-205316.jsonl

logs/events-20250905-205327.jsonl

logs/events-20250905-205330.jsonl

logs/events-20250905-205332.jsonl

logs/events-20250905-205334.jsonl

logs/events-20250905-205345.jsonl

logs/events-20250905-205347.jsonl

logs/events-20250905-205349.jsonl

logs/events-20250905-205352.jsonl

logs/events-20250905-205402.jsonl

logs/events-20250905-205405.jsonl

logs/events-20250905-205407.jsonl

logs/events-20250905-205410.jsonl

logs/events-20250905-205419.jsonl

logs/events-20250905-205422.jsonl

logs/events-20250905-205424.jsonl

logs/events-20250905-205427.jsonl

logs/events-20250905-205436.jsonl

logs/events-20250905-205439.jsonl

logs/events-20250905-205442.jsonl

logs/events-20250905-205444.jsonl

logs/events-20250905-205454.jsonl

logs/events-20250905-205456.jsonl

logs/events-20250905-205459.jsonl

logs/events-20250905-205501.jsonl

logs/events-20250905-205511.jsonl

logs/events-20250905-205514.jsonl

logs/events-20250905-205516.jsonl

logs/events-20250905-205519.jsonl

logs/events-20250905-205529.jsonl

logs/events-20250905-205533.jsonl

logs/events-20250905-205535.jsonl

logs/events-20250905-205537.jsonl

logs/events-20250905-205547.jsonl

logs/events-20250905-205552.jsonl

logs/events-20250905-205554.jsonl

logs/events-20250905-205556.jsonl

logs/events-20250905-205606.jsonl

logs/events-20250905-205612.jsonl

logs/events-20250905-205615.jsonl

logs/events-20250905-205617.jsonl

logs/events-20250905-205628.jsonl

logs/events-20250905-205637.jsonl

logs/events-20250905-205641.jsonl

logs/events-20250905-205643.jsonl

logs/events-20250905-205657.jsonl

logs/events-20250905-205705.jsonl

logs/events-20250905-205708.jsonl

logs/events-20250905-205711.jsonl

logs/events-20250905-205723.jsonl

logs/events-20250905-205728.jsonl

logs/events-20250905-205732.jsonl

logs/events-20250905-205735.jsonl

logs/events-20250905-205744.jsonl

logs/events-20250905-205750.jsonl

logs/events-20250905-205753.jsonl

logs/events-20250905-205755.jsonl

logs/events-20250905-205804.jsonl

logs/events-20250905-205810.jsonl

logs/events-20250905-205813.jsonl

logs/events-20250905-205814.jsonl

logs/events-20250905-205823.jsonl

logs/events-20250905-205829.jsonl

logs/events-20250905-205832.jsonl

logs/events-20250905-205834.jsonl

logs/events-20250905-205841.jsonl

logs/events-20250905-205847.jsonl

logs/events-20250905-205849.jsonl

logs/events-20250905-205852.jsonl

logs/events-20250905-205857.jsonl

logs/events-20250905-205904.jsonl

logs/events-20250905-205906.jsonl

logs/events-20250905-205909.jsonl

logs/events-20250905-205914.jsonl

logs/events-20250905-205921.jsonl

logs/events-20250905-205923.jsonl

logs/events-20250905-205926.jsonl

logs/events-20250905-205931.jsonl

logs/events-20250905-205937.jsonl

logs/events-20250905-205941.jsonl

logs/events-20250905-205954.jsonl

logs/events-20250905-205958.jsonl

logs/events-20250905-210006.jsonl

logs/events-20250905-210010.jsonl

logs/events-20250905-210014.jsonl

logs/events-20250905-210019.jsonl

logs/events-20250905-210027.jsonl

logs/events-20250905-210031.jsonl

logs/events-20250905-210038.jsonl

logs/events-20250905-210043.jsonl

logs/events-20250905-210051.jsonl

logs/events-20250905-210055.jsonl

logs/events-20250905-210101.jsonl

logs/events-20250905-210106.jsonl

logs/events-20250905-210114.jsonl

logs/events-20250905-210117.jsonl

logs/events-20250905-210121.jsonl

logs/events-20250905-210125.jsonl

logs/events-20250905-210133.jsonl

logs/events-20250905-210135.jsonl

logs/events-20250905-210139.jsonl

logs/events-20250905-210143.jsonl

logs/events-20250905-210150.jsonl

logs/events-20250905-210152.jsonl

logs/events-20250905-210157.jsonl

logs/events-20250905-210200.jsonl

logs/events-20250905-210207.jsonl

logs/events-20250905-210209.jsonl

logs/events-20250905-210213.jsonl

logs/events-20250905-210216.jsonl

logs/events-20250905-210224.jsonl

logs/events-20250905-210227.jsonl

logs/events-20250905-210230.jsonl

logs/events-20250905-210234.jsonl

logs/events-20250905-210241.jsonl

logs/events-20250905-210244.jsonl

logs/events-20250905-210248.jsonl

logs/events-20250905-210251.jsonl

logs/events-20250905-210258.jsonl

logs/events-20250905-210301.jsonl

logs/events-20250905-210306.jsonl

logs/events-20250905-210308.jsonl

logs/events-20250905-210315.jsonl

logs/events-20250905-210318.jsonl

logs/events-20250905-210323.jsonl

logs/events-20250905-210326.jsonl

logs/events-20250905-210333.jsonl

logs/events-20250905-210336.jsonl

logs/events-20250905-210341.jsonl

logs/events-20250905-210343.jsonl

logs/events-20250905-210351.jsonl

logs/events-20250905-210356.jsonl

logs/events-20250905-210402.jsonl

logs/events-20250905-210405.jsonl

logs/events-20250905-210413.jsonl

logs/events-20250905-210419.jsonl

logs/events-20250905-210426.jsonl

logs/events-20250905-210427.jsonl

logs/events-20250905-210435.jsonl

logs/events-20250905-210438.jsonl

logs/events-20250905-210445.jsonl

logs/events-20250905-210449.jsonl

logs/events-20250905-210456.jsonl

logs/events-20250905-210458.jsonl

logs/events-20250905-210508.jsonl

logs/events-20250905-210509.jsonl

logs/events-20250905-210513.jsonl

logs/events-20250905-210533.jsonl

logs/events-20250905-210538.jsonl

logs/events-20250905-210539.jsonl

logs/events-20250905-210545.jsonl

logs/events-20250905-210546.jsonl

logs/events-20250905-210551.jsonl

logs/events-20250905-210553.jsonl

logs/events-20250905-210559.jsonl

logs/events-20250905-210601.jsonl

logs/events-20250905-210608.jsonl

logs/events-20250905-210613.jsonl

logs/events-20250905-210617.jsonl

logs/events-20250905-210619.jsonl

logs/events-20250905-210628.jsonl

logs/events-20250905-210633.jsonl

logs/events-20250905-210637.jsonl

logs/events-20250905-210640.jsonl

logs/events-20250905-210644.jsonl

logs/events-20250905-210648.jsonl

logs/events-20250905-210652.jsonl

logs/events-20250905-210656.jsonl

logs/events-20250905-210659.jsonl

logs/events-20250905-210700.jsonl

logs/events-20250905-210707.jsonl

logs/events-20250905-210711.jsonl

logs/events-20250905-210713.jsonl

logs/events-20250905-210715.jsonl

logs/events-20250905-210721.jsonl

logs/events-20250905-210725.jsonl

logs/events-20250905-210729.jsonl

logs/events-20250905-210731.jsonl

logs/events-20250905-210736.jsonl

logs/events-20250905-210741.jsonl

logs/events-20250905-210744.jsonl

logs/events-20250905-210746.jsonl

logs/events-20250905-210750.jsonl

logs/events-20250905-210756.jsonl

logs/events-20250905-210759.jsonl

logs/events-20250905-210800.jsonl

logs/events-20250905-210806.jsonl

logs/events-20250905-210810.jsonl

logs/events-20250905-210814.jsonl

logs/events-20250905-210816.jsonl

logs/events-20250905-210822.jsonl

logs/events-20250905-210826.jsonl

logs/events-20250905-210832.jsonl

logs/events-20250905-210834.jsonl

logs/events-20250905-210841.jsonl

logs/events-20250905-210846.jsonl

logs/events-20250905-210853.jsonl

logs/events-20250905-210902.jsonl

logs/events-20250905-210907.jsonl

logs/events-20250905-210912.jsonl

logs/events-20250905-210913.jsonl

logs/events-20250905-210922.jsonl

logs/events-20250905-210924.jsonl

logs/events-20250905-210928.jsonl

logs/events-20250905-210940.jsonl

logs/events-20250905-210945.jsonl

logs/events-20250905-210947.jsonl

logs/events-20250905-210948.jsonl

logs/events-20250905-210953.jsonl

logs/events-20250905-210959.jsonl

logs/events-20250905-211002.jsonl

logs/events-20250905-211004.jsonl

logs/events-20250905-211007.jsonl

logs/events-20250905-211012.jsonl

logs/events-20250905-211016.jsonl

logs/events-20250905-211019.jsonl

logs/events-20250905-211022.jsonl

logs/events-20250905-211030.jsonl

logs/events-20250905-211032.jsonl

logs/events-20250905-211035.jsonl

logs/events-20250905-211038.jsonl

logs/events-20250905-211047.jsonl

logs/events-20250905-211050.jsonl

logs/events-20250905-211056.jsonl

logs/events-20250905-211057.jsonl

logs/events-20250905-211104.jsonl

logs/events-20250905-211107.jsonl

logs/events-20250905-211111.jsonl

logs/events-20250905-211113.jsonl

logs/events-20250905-211118.jsonl

logs/events-20250905-211120.jsonl

logs/events-20250905-211125.jsonl

logs/events-20250905-211129.jsonl

logs/events-20250905-211131.jsonl

logs/events-20250905-211133.jsonl

logs/events-20250905-211138.jsonl

logs/events-20250905-211142.jsonl

logs/events-20250905-211143.jsonl

logs/events-20250905-211147.jsonl

logs/events-20250905-211153.jsonl

logs/events-20250905-211156.jsonl

logs/events-20250905-211202.jsonl

logs/events-20250905-211208.jsonl

logs/events-20250905-211212.jsonl

logs/events-20250905-211219.jsonl

logs/events-20250905-211223.jsonl

logs/events-20250905-211228.jsonl

logs/events-20250905-211234.jsonl

logs/events-20250905-211238.jsonl

logs/events-20250905-211245.jsonl

logs/events-20250905-211248.jsonl

logs/events-20250905-211253.jsonl

logs/events-20250905-211254.jsonl

logs/events-20250905-211259.jsonl

logs/events-20250905-211302.jsonl

logs/events-20250905-211306.jsonl

logs/events-20250905-211308.jsonl

logs/events-20250905-211312.jsonl

logs/events-20250905-211316.jsonl

logs/events-20250905-211325.jsonl

logs/events-20250905-211331.jsonl

logs/events-20250905-211337.jsonl

logs/events-20250905-211348.jsonl

logs/events-20250905-211349.jsonl

logs/events-20250905-211356.jsonl

logs/events-20250905-211400.jsonl

logs/events-20250905-211414.jsonl

logs/events-20250905-211415.jsonl

logs/events-20250905-211422.jsonl

logs/events-20250905-211427.jsonl

logs/events-20250905-211441.jsonl

logs/events-20250905-211447.jsonl

logs/events-20250905-211450.jsonl

logs/events-20250905-211502.jsonl

logs/events-20250905-211506.jsonl

logs/events-20250905-211510.jsonl

logs/events-20250905-211520.jsonl

logs/events-20250905-211521.jsonl

logs/events-20250905-211538.jsonl

logs/events-20250905-211541.jsonl

logs/events-20250905-211552.jsonl

logs/events-20250905-211557.jsonl

logs/events-20250905-211559.jsonl

logs/events-20250905-211600.jsonl

logs/events-20250905-211613.jsonl

logs/events-20250905-211618.jsonl

logs/events-20250905-211622.jsonl

logs/events-20250905-211625.jsonl

logs/events-20250905-211638.jsonl

logs/events-20250905-211642.jsonl

logs/events-20250905-211647.jsonl

logs/events-20250905-211648.jsonl

logs/events-20250905-211659.jsonl

logs/events-20250905-211703.jsonl

logs/events-20250905-211709.jsonl

logs/events-20250905-211719.jsonl

logs/events-20250905-211722.jsonl

logs/events-20250905-211728.jsonl

logs/events-20250905-211729.jsonl

logs/events-20250905-211739.jsonl

logs/events-20250905-211742.jsonl

logs/events-20250905-211747.jsonl

logs/events-20250905-211750.jsonl

logs/events-20250905-211759.jsonl

logs/events-20250905-211803.jsonl

logs/events-20250905-211807.jsonl

logs/events-20250905-211810.jsonl

logs/events-20250905-211816.jsonl

logs/events-20250905-211822.jsonl

logs/events-20250905-211825.jsonl

logs/events-20250905-211828.jsonl

logs/events-20250905-211833.jsonl

logs/events-20250905-211838.jsonl

logs/events-20250905-211842.jsonl

logs/events-20250905-211845.jsonl

logs/events-20250905-211849.jsonl

logs/events-20250905-211855.jsonl

logs/events-20250905-211858.jsonl

logs/events-20250905-211900.jsonl

logs/events-20250905-211904.jsonl

logs/events-20250905-211911.jsonl

logs/events-20250905-211913.jsonl

logs/events-20250905-211914.jsonl

logs/events-20250905-211930.jsonl

logs/events-20260511-092719.jsonl

logs/events-20260511-121548.jsonl

logs/events-20260511-121620.jsonl

logs/events-20260511-121624.jsonl

logs/events-20260511-121928.jsonl

logs/events-20260511-121956.jsonl

logs/events-20260511-122028.jsonl

logs/events-20260511-122030.jsonl

logs/events-20260511-122034.jsonl

logs/events-20260511-122120.jsonl

logs/events-20260511-122121.jsonl

logs/events-20260511-122125.jsonl

logs/events-20260511-122138.jsonl

logs/events-20260511-122144.jsonl

logs/events-20260511-122217.jsonl

logs/events-20260511-122333.jsonl

logs/events-20260511-122334.jsonl

logs/events-20260511-124120.jsonl

logs/events-20260511-124121.jsonl

logs/events-20260511-124338.jsonl

logs/events-20260511-124339.jsonl

logs/events-20260511-124513.jsonl

logs/events-20260511-124747.jsonl

logs/events-20260511-125038.jsonl

logs/events-20260511-125039.jsonl

logs/events-20260511-130148.jsonl

logs/events-20260511-130345.jsonl

logs/events-20260511-130346.jsonl

logs/events-20260511-135548.jsonl

logs/events-20260511-135549.jsonl

logs/events-20260511-140309.jsonl

logs/events-20260511-140311.jsonl

logs/events-20260511-142819.jsonl

logs/events-20260511-142820.jsonl

logs/events-20260511-143139.jsonl

logs/events-20260511-143140.jsonl

logs/events-20260511-143542.jsonl

logs/events-20260511-143543.jsonl

logs/events-20260511-144233.jsonl

logs/events-20260511-144234.jsonl

logs/events-20260511-145219.jsonl

logs/events-20260511-145220.jsonl

logs/events-20260511-145221.jsonl

logs/events-20260511-145349.jsonl

logs/events-20260511-145350.jsonl

logs/events-20260511-150708.jsonl

logs/events-20260511-151046.jsonl

logs/events-20260511-151047.jsonl

logs/events-20260511-151118.jsonl

logs/events-20260511-151119.jsonl

logs/events-20260511-152018.jsonl

logs/events-20260511-152109.jsonl

logs/events-20260511-214141.jsonl

logs/events-20260511-214147.jsonl

logs/events-20260511-214148.jsonl

logs/events-20260511-214158.jsonl

logs/events-20260511-214207.jsonl

logs/events-20260511-214209.jsonl

logs/events-20260511-214214.jsonl

logs/events-20260511-214216.jsonl

logs/events-20260511-222821.jsonl

logs/events-20260511-222822.jsonl

logs/events-20260512-091250.jsonl

logs/events-20260512-091251.jsonl

logs/events-20260512-091308.jsonl

logs/events-20260512-091309.jsonl

logs/events-20260512-093545.jsonl

logs/events-20260512-093550.jsonl

logs/events-20260512-093552.jsonl

logs/events-20260512-093927.jsonl

logs/events-20260512-093928.jsonl

logs/events-20260512-100158.jsonl

logs/events-20260512-100159.jsonl

logs/events-20260512-100301.jsonl

logs/events-20260512-100303.jsonl

logs/events-20260512-100615.jsonl

logs/events-20260512-100654.jsonl

logs/events-20260512-100745.jsonl

logs/events-20260512-100808.jsonl

logs/events-20260512-100846.jsonl

logs/events-20260512-100847.jsonl

logs/events-20260512-101413.jsonl

logs/events-20260512-101415.jsonl

logs/events-20260512-101428.jsonl

logs/events-20260512-101429.jsonl

logs/events-20260512-101524.jsonl

logs/events-20260512-101527.jsonl

logs/events-20260512-101542.jsonl

logs/events-20260512-101546.jsonl

logs/mcp-edna.log

logs/mcp-mario.log

logs/mcp-moroni.log

logs/mcp-q.log

logs/mcp-tony.log

logs/ocean-loop-detached.log

logs/root-venv-install.log

logs/runtime-backend-20260510-212146.log

logs/runtime-backend-20260510-212156.log

logs/runtime-backend-20260510-212205.log

logs/runtime-backend-20260510-212215.log

logs/runtime-backend-20260510-212224.log

logs/runtime-backend-20260510-212233.log

logs/runtime-backend-20260510-212243.log

logs/runtime-backend-20260510-212252.log

logs/runtime-backend-20260510-212302.log

logs/runtime-backend-20260510-212312.log

logs/runtime-backend-20260510-212321.log

logs/runtime-backend-20260510-212331.log

logs/runtime-backend-20260510-212340.log

logs/runtime-backend-20260510-212350.log

logs/runtime-backend-20260510-212359.log

logs/runtime-backend-20260510-212409.log

logs/runtime-backend-20260510-212418.log

logs/runtime-backend-20260510-212428.log

logs/runtime-backend-20260510-212437.log

logs/runtime-backend-20260510-212447.log

logs/runtime-backend-20260510-212456.log

logs/runtime-backend-20260510-212506.log

logs/runtime-backend-20260510-212515.log

logs/runtime-backend-20260510-212525.log

logs/runtime-backend-20260510-212534.log

logs/runtime-backend-20260510-212544.log

logs/runtime-backend-20260510-212553.log

logs/runtime-backend-20260510-212607.log

logs/runtime-backend-20260510-212617.log

logs/runtime-backend-20260510-212626.log

logs/runtime-backend-20260510-212636.log

logs/runtime-backend-20260510-212645.log

logs/runtime-backend-20260510-212655.log

logs/runtime-backend-20260510-212704.log

logs/runtime-backend-20260510-212713.log

logs/runtime-backend-20260510-212723.log

logs/runtime-backend-20260510-212732.log

logs/runtime-backend-20260510-212742.log

logs/runtime-backend-20260510-212751.log

logs/runtime-backend-20260510-213729.log

logs/runtime-backend-20260510-213740.log

logs/runtime-backend-20260511-075328.log

logs/runtime-backend-20260511-075339.log

logs/runtime-backend-20260511-075351.log

logs/runtime-backend-20260511-075402.log

logs/runtime-backend-20260511-075414.log

logs/runtime-backend-20260511-075426.log

logs/runtime-backend-20260511-075436.log

logs/runtime-backend-20260511-075447.log

logs/runtime-backend-20260511-075723.log

logs/runtime-backend-20260511-075724.log

logs/runtime-backend-20260511-075725.log

logs/runtime-backend-20260511-075727.log

logs/runtime-backend-20260511-075729.log

logs/runtime-backend-20260511-075731.log

logs/runtime-backend-20260511-075732.log

logs/runtime-backend-20260511-075734.log

logs/runtime-backend-20260511-075736.log

logs/runtime-backend-20260511-075738.log

logs/runtime-backend-20260511-075739.log

logs/runtime-backend-20260511-075741.log

logs/runtime-backend-20260511-093458.log

logs/runtime-backend-20260511-122029.log

logs/runtime-backend-20260511-122120.log

logs/runtime-backend-20260511-214205.log

logs/runtime-backend-20260512-101411.log

logs/runtime-backend-20260512-101521.log

logs/runtime-ui-20260510-212146.log

logs/runtime-ui-20260510-212156.log

logs/runtime-ui-20260510-212205.log

logs/runtime-ui-20260510-212215.log

logs/runtime-ui-20260510-212224.log

logs/runtime-ui-20260510-212233.log

logs/runtime-ui-20260510-212243.log

logs/runtime-ui-20260510-212252.log

logs/runtime-ui-20260510-212302.log

logs/runtime-ui-20260510-212312.log

logs/runtime-ui-20260510-212321.log

logs/runtime-ui-20260510-212331.log

logs/runtime-ui-20260510-212340.log

logs/runtime-ui-20260510-212350.log

logs/runtime-ui-20260510-212359.log

logs/runtime-ui-20260510-212409.log

logs/runtime-ui-20260510-212418.log

logs/runtime-ui-20260510-212428.log

logs/runtime-ui-20260510-212437.log

logs/runtime-ui-20260510-212447.log

logs/runtime-ui-20260510-212456.log

logs/runtime-ui-20260510-212506.log

logs/runtime-ui-20260510-212515.log

logs/runtime-ui-20260510-212525.log

logs/runtime-ui-20260510-212534.log

logs/runtime-ui-20260510-212544.log

logs/runtime-ui-20260510-212553.log

logs/runtime-ui-20260510-212607.log

logs/runtime-ui-20260510-212617.log

logs/runtime-ui-20260510-212626.log

logs/runtime-ui-20260510-212636.log

logs/runtime-ui-20260510-212645.log

logs/runtime-ui-20260510-212655.log

logs/runtime-ui-20260510-212704.log

logs/runtime-ui-20260510-212713.log

logs/runtime-ui-20260510-212723.log

logs/runtime-ui-20260510-212732.log

logs/runtime-ui-20260510-212742.log

logs/runtime-ui-20260510-212751.log

logs/runtime-ui-20260510-213729.log

logs/runtime-ui-20260510-213740.log

logs/runtime-ui-20260511-075328.log

logs/runtime-ui-20260511-075339.log

logs/runtime-ui-20260511-075351.log

logs/runtime-ui-20260511-075402.log

logs/runtime-ui-20260511-075414.log

logs/runtime-ui-20260511-075426.log

logs/runtime-ui-20260511-075436.log

logs/runtime-ui-20260511-075447.log

logs/runtime-ui-20260511-075723.log

logs/runtime-ui-20260511-075724.log

logs/runtime-ui-20260511-075725.log

logs/runtime-ui-20260511-075727.log

logs/runtime-ui-20260511-075729.log

logs/runtime-ui-20260511-075731.log

logs/runtime-ui-20260511-075732.log

logs/runtime-ui-20260511-075734.log

logs/runtime-ui-20260511-075736.log

logs/runtime-ui-20260511-075738.log

logs/runtime-ui-20260511-075739.log

logs/runtime-ui-20260511-075741.log

logs/runtime-ui-20260511-093458.log

logs/runtime-ui-20260511-122029.log

logs/runtime-ui-20260511-122120.log

logs/runtime-ui-20260511-214205.log

logs/runtime-ui-20260512-101411.log

logs/runtime-ui-20260512-101521.log

logs/session-20250902-140754.log

logs/session-20250902-140757.log

logs/session-20260510-212122.log

logs/session-20260510-212146.log

logs/session-20260510-212156.log

logs/session-20260510-212205.log

logs/session-20260510-212215.log

logs/session-20260510-212224.log

logs/session-20260510-212234.log

logs/session-20260510-212243.log

logs/session-20260510-212253.log

logs/session-20260510-212303.log

logs/session-20260510-212312.log

logs/session-20260510-212322.log

logs/session-20260510-212331.log

logs/session-20260510-212341.log

logs/session-20260510-212350.log

logs/session-20260510-212400.log

logs/session-20260510-212409.log

logs/session-20260510-212419.log

logs/session-20260510-212428.log

logs/session-20260510-212438.log

logs/session-20260510-212447.log

logs/session-20260510-212457.log

logs/session-20260510-212506.log

logs/session-20260510-212516.log

logs/session-20260510-212525.log

logs/session-20260510-212535.log

logs/session-20260510-212544.log

logs/session-20260510-212554.log

logs/session-20260510-212608.log

logs/session-20260510-212617.log

logs/session-20260510-212627.log

logs/session-20260510-212636.log

logs/session-20260510-212646.log

logs/session-20260510-212655.log

logs/session-20260510-212704.log

logs/session-20260510-212714.log

logs/session-20260510-212723.log

logs/session-20260510-212733.log

logs/session-20260510-212742.log

logs/session-20260510-212752.log

logs/session-20260510-213730.log

logs/session-20260510-213740.log

logs/session-20260511-075316.log

logs/session-20260511-075329.log

logs/session-20260511-075341.log

logs/session-20260511-075352.log

logs/session-20260511-075403.log

logs/session-20260511-075415.log

logs/session-20260511-075427.log

logs/session-20260511-075437.log

logs/session-20260511-075448.log

logs/session-20260511-075722.log

logs/session-20260511-075724.log

logs/session-20260511-075725.log

logs/session-20260511-075727.log

logs/session-20260511-075729.log

logs/session-20260511-075730.log

logs/session-20260511-075732.log

logs/session-20260511-075734.log

logs/session-20260511-075736.log

logs/session-20260511-075737.log

logs/session-20260511-075739.log

logs/session-20260511-075741.log

logs/session-20260511-075743.log

logs/session-20260511-075746.log

logs/session-20260511-075816.log

logs/session-20260511-080105.log

logs/session-20260511-080407.log

logs/session-20260511-080707.log

logs/session-20260511-080758.log

logs/session-20260511-080948.log

logs/session-20260511-081705.log

logs/session-20260511-081734.log

logs/session-20260511-091351.log

logs/session-20260511-091607.log

logs/session-20260511-091741.log

logs/session-20260511-091834.log

logs/session-20260511-092105.log

logs/session-20260511-092307.log

logs/session-20260511-092407.log

logs/session-20260511-092658.log

logs/session-20260511-092719.log

logs/session-20260511-093025.log

logs/session-20260511-093510.log

logs/session-20260511-093512.log

logs/session-20260511-100119.log

logs/session-20260511-114831.log

logs/session-20260511-115233.log

logs/session-20260511-115247.log

logs/session-20260511-115604.log

logs/session-20260511-115619.log

logs/session-20260511-121548.log

logs/session-20260511-121620.log

logs/session-20260511-121624.log

logs/session-20260511-121928.log

logs/session-20260511-121956.log

logs/session-20260511-122028.log

logs/session-20260511-122030.log

logs/session-20260511-122034.log

logs/session-20260511-122120.log

logs/session-20260511-122121.log

logs/session-20260511-122125.log

logs/session-20260511-122138.log

logs/session-20260511-122144.log

logs/session-20260511-122217.log

logs/session-20260511-122333.log

logs/session-20260511-122334.log

logs/session-20260511-124120.log

logs/session-20260511-124121.log

logs/session-20260511-124338.log

logs/session-20260511-124339.log

logs/session-20260511-125038.log

logs/session-20260511-125039.log

logs/session-20260511-130148.log

logs/session-20260511-130345.log

logs/session-20260511-130346.log

logs/session-20260511-135548.log

logs/session-20260511-135549.log

logs/session-20260511-140309.log

logs/session-20260511-140311.log

logs/session-20260511-142819.log

logs/session-20260511-142820.log

logs/session-20260511-143139.log

logs/session-20260511-143140.log

logs/session-20260511-143542.log

logs/session-20260511-143543.log

logs/session-20260511-144233.log

logs/session-20260511-144234.log

logs/session-20260511-145219.log

logs/session-20260511-145220.log

logs/session-20260511-145221.log

logs/session-20260511-145349.log

logs/session-20260511-145350.log

logs/session-20260511-150708.log

logs/session-20260511-151046.log

logs/session-20260511-151047.log

logs/session-20260511-151118.log

logs/session-20260511-151119.log

logs/session-20260511-152018.log

logs/session-20260511-152109.log

logs/session-20260511-214141.log

logs/session-20260511-214147.log

logs/session-20260511-214148.log

logs/session-20260511-214158.log

logs/session-20260511-214207.log

logs/session-20260511-214209.log

logs/session-20260511-214214.log

logs/session-20260511-214216.log

logs/session-20260511-222821.log

logs/session-20260511-222822.log

logs/session-20260512-091250.log

logs/session-20260512-091251.log

logs/session-20260512-091308.log

logs/session-20260512-091309.log

logs/session-20260512-093545.log

logs/session-20260512-093550.log

logs/session-20260512-093552.log

logs/session-20260512-093927.log

logs/session-20260512-093928.log

logs/session-20260512-100158.log

logs/session-20260512-100159.log

logs/session-20260512-100301.log

logs/session-20260512-100303.log

logs/session-20260512-100615.log

logs/session-20260512-100654.log

logs/session-20260512-100745.log

logs/session-20260512-100808.log

logs/session-20260512-100846.log

logs/session-20260512-100847.log

logs/session-20260512-101413.log

logs/session-20260512-101415.log

logs/session-20260512-101428.log

logs/session-20260512-101429.log

logs/session-20260512-101524.log

logs/session-20260512-101527.log

logs/session-20260512-101542.log

logs/session-20260512-101546.log

main.py

node_modules/.bin/baseline-browser-mapping

node_modules/.bin/browserslist

node_modules/.bin/esbuild

node_modules/.bin/jsesc

node_modules/.bin/json5

node_modules/.bin/nanoid

node_modules/.bin/parser

node_modules/.bin/rollup

node_modules/.bin/semver

node_modules/.bin/tsc

node_modules/.bin/tsserver

node_modules/.bin/update-browserslist-db

node_modules/.bin/vite

node_modules/.package-lock.json

node_modules/aria-hidden/LICENSE

node_modules/aria-hidden/README.md

node_modules/aria-hidden/package.json

node_modules/assistant-cloud/LICENSE

node_modules/assistant-cloud/package.json

node_modules/assistant-stream/LICENSE

node_modules/assistant-stream/package.json

node_modules/baseline-browser-mapping/LICENSE.txt

node_modules/baseline-browser-mapping/README.md

node_modules/baseline-browser-mapping/package.json

node_modules/browserslist/LICENSE

node_modules/browserslist/README.md

node_modules/browserslist/browser.js

node_modules/browserslist/cli.js

node_modules/browserslist/error.d.ts

node_modules/browserslist/error.js

node_modules/browserslist/index.d.ts

node_modules/browserslist/index.js

node_modules/browserslist/node.js

node_modules/browserslist/package.json

node_modules/browserslist/parse.js

node_modules/caniuse-lite/LICENSE

node_modules/caniuse-lite/README.md

node_modules/caniuse-lite/package.json

node_modules/convert-source-map/LICENSE

node_modules/convert-source-map/README.md

node_modules/convert-source-map/index.js

node_modules/convert-source-map/package.json

node_modules/csstype/LICENSE

node_modules/csstype/README.md

node_modules/csstype/index.d.ts

node_modules/csstype/index.js.flow

node_modules/csstype/package.json

node_modules/debug/LICENSE

node_modules/debug/README.md

node_modules/debug/package.json

node_modules/detect-node-es/LICENSE

node_modules/detect-node-es/Readme.md

node_modules/detect-node-es/package.json

node_modules/electron-to-chromium/LICENSE

node_modules/electron-to-chromium/README.md

node_modules/electron-to-chromium/chromium-versions.js

node_modules/electron-to-chromium/chromium-versions.json

node_modules/electron-to-chromium/full-chromium-versions.js

node_modules/electron-to-chromium/full-chromium-versions.json

node_modules/electron-to-chromium/full-versions.js

node_modules/electron-to-chromium/full-versions.json

node_modules/electron-to-chromium/index.js

node_modules/electron-to-chromium/package.json

node_modules/electron-to-chromium/versions.js

node_modules/electron-to-chromium/versions.json

node_modules/esbuild/LICENSE.md

node_modules/esbuild/README.md

node_modules/esbuild/install.js

node_modules/esbuild/package.json

node_modules/escalade/index.d.mts

node_modules/escalade/index.d.ts

node_modules/escalade/license

node_modules/escalade/package.json

node_modules/escalade/readme.md

node_modules/fdir/LICENSE

node_modules/fdir/README.md

node_modules/fdir/package.json

node_modules/fsevents/LICENSE

node_modules/fsevents/README.md

node_modules/fsevents/fsevents.d.ts

node_modules/fsevents/fsevents.js

node_modules/fsevents/fsevents.node

node_modules/fsevents/package.json

node_modules/gensync/LICENSE

node_modules/gensync/README.md

node_modules/gensync/index.js

node_modules/gensync/index.js.flow

node_modules/gensync/package.json

node_modules/get-nonce/CHANGELOG.md

node_modules/get-nonce/LICENSE

node_modules/get-nonce/README.md

node_modules/get-nonce/package.json

node_modules/js-tokens/CHANGELOG.md

node_modules/js-tokens/LICENSE

node_modules/js-tokens/README.md

node_modules/js-tokens/index.js

node_modules/js-tokens/package.json

node_modules/jsesc/LICENSE-MIT.txt

node_modules/jsesc/README.md

node_modules/jsesc/jsesc.js

node_modules/jsesc/package.json

node_modules/json5/LICENSE.md

node_modules/json5/README.md

node_modules/json5/package.json

node_modules/lru-cache/LICENSE

node_modules/lru-cache/README.md

node_modules/lru-cache/index.js

node_modules/lru-cache/package.json

node_modules/lucide-react/LICENSE

node_modules/lucide-react/README.md

node_modules/lucide-react/package.json

node_modules/ms/index.js

node_modules/ms/license.md

node_modules/ms/package.json

node_modules/ms/readme.md

node_modules/nanoid/LICENSE

node_modules/nanoid/README.md

node_modules/nanoid/index.browser.js

node_modules/nanoid/index.d.ts

node_modules/nanoid/index.js

node_modules/nanoid/nanoid.js

node_modules/nanoid/package.json

node_modules/node-releases/LICENSE

node_modules/node-releases/README.md

node_modules/node-releases/package.json

node_modules/picocolors/LICENSE

node_modules/picocolors/README.md

node_modules/picocolors/package.json

node_modules/picocolors/picocolors.browser.js

node_modules/picocolors/picocolors.d.ts

node_modules/picocolors/picocolors.js

node_modules/picocolors/types.d.ts

node_modules/picomatch/LICENSE

node_modules/picomatch/README.md

node_modules/picomatch/index.js

node_modules/picomatch/package.json

node_modules/picomatch/posix.js

node_modules/postcss/LICENSE

node_modules/postcss/README.md

node_modules/postcss/package.json

node_modules/react/LICENSE

node_modules/react/README.md

node_modules/react/compiler-runtime.js

node_modules/react/index.js

node_modules/react/jsx-dev-runtime.js

node_modules/react/jsx-dev-runtime.react-server.js

node_modules/react/jsx-runtime.js

node_modules/react/jsx-runtime.react-server.js

node_modules/react/package.json

node_modules/react/react.react-server.js

node_modules/react-dom/LICENSE

node_modules/react-dom/README.md

node_modules/react-dom/client.js

node_modules/react-dom/client.react-server.js

node_modules/react-dom/index.js

node_modules/react-dom/package.json

node_modules/react-dom/profiling.js

node_modules/react-dom/profiling.react-server.js

node_modules/react-dom/react-dom.react-server.js

node_modules/react-dom/server.browser.js

node_modules/react-dom/server.bun.js

node_modules/react-dom/server.edge.js

node_modules/react-dom/server.js

node_modules/react-dom/server.node.js

node_modules/react-dom/server.react-server.js

node_modules/react-dom/static.browser.js

node_modules/react-dom/static.edge.js

node_modules/react-dom/static.js

node_modules/react-dom/static.node.js

node_modules/react-dom/static.react-server.js

node_modules/react-dom/test-utils.js

node_modules/react-refresh/LICENSE

node_modules/react-refresh/README.md

node_modules/react-refresh/babel.js

node_modules/react-refresh/package.json

node_modules/react-refresh/runtime.js

node_modules/react-remove-scroll/LICENSE

node_modules/react-remove-scroll/README.md

node_modules/react-remove-scroll/package.json

node_modules/react-remove-scroll-bar/README.md

node_modules/react-remove-scroll-bar/package.json

node_modules/react-style-singleton/LICENSE

node_modules/react-style-singleton/README.md

node_modules/react-style-singleton/package.json

node_modules/react-textarea-autosize/LICENSE

node_modules/react-textarea-autosize/README.md

node_modules/react-textarea-autosize/package.json

node_modules/rollup/LICENSE.md

node_modules/rollup/README.md

node_modules/rollup/package.json

node_modules/scheduler/LICENSE

node_modules/scheduler/README.md

node_modules/scheduler/index.js

node_modules/scheduler/index.native.js

node_modules/scheduler/package.json

node_modules/scheduler/unstable_mock.js

node_modules/scheduler/unstable_post_task.js

node_modules/secure-json-parse/.airtap.yml

node_modules/secure-json-parse/.gitattributes

node_modules/secure-json-parse/LICENSE

node_modules/secure-json-parse/README.md

node_modules/secure-json-parse/eslint.config.js

node_modules/secure-json-parse/index.js

node_modules/secure-json-parse/package.json

node_modules/semver/LICENSE

node_modules/semver/README.md

node_modules/semver/package.json

node_modules/semver/range.bnf

node_modules/semver/semver.js

node_modules/source-map-js/LICENSE

node_modules/source-map-js/README.md

node_modules/source-map-js/package.json

node_modules/source-map-js/source-map.d.ts

node_modules/source-map-js/source-map.js

node_modules/tinyglobby/LICENSE

node_modules/tinyglobby/README.md

node_modules/tinyglobby/package.json

node_modules/tslib/CopyrightNotice.txt

node_modules/tslib/LICENSE.txt

node_modules/tslib/README.md

node_modules/tslib/SECURITY.md

node_modules/tslib/package.json

node_modules/tslib/tslib.d.ts

node_modules/tslib/tslib.es6.html

node_modules/tslib/tslib.es6.js

node_modules/tslib/tslib.es6.mjs

node_modules/tslib/tslib.html

node_modules/tslib/tslib.js

node_modules/typescript/LICENSE.txt

node_modules/typescript/README.md

node_modules/typescript/SECURITY.md

node_modules/typescript/ThirdPartyNoticeText.txt

node_modules/typescript/package.json

node_modules/update-browserslist-db/LICENSE

node_modules/update-browserslist-db/README.md

node_modules/update-browserslist-db/check-npm-version.js

node_modules/update-browserslist-db/cli.js

node_modules/update-browserslist-db/index.d.ts

node_modules/update-browserslist-db/index.js

node_modules/update-browserslist-db/package.json

node_modules/update-browserslist-db/utils.js

node_modules/use-callback-ref/LICENSE

node_modules/use-callback-ref/README.md

node_modules/use-callback-ref/package.json

node_modules/use-composed-ref/README.md

node_modules/use-composed-ref/package.json

node_modules/use-isomorphic-layout-effect/LICENSE

node_modules/use-isomorphic-layout-effect/README.md

node_modules/use-isomorphic-layout-effect/package.json

node_modules/use-latest/LICENSE

node_modules/use-latest/README.md

node_modules/use-latest/package.json

node_modules/use-sidecar/LICENSE

node_modules/use-sidecar/README.md

node_modules/use-sidecar/package.json

node_modules/vite/LICENSE.md

node_modules/vite/README.md

node_modules/vite/client.d.ts

node_modules/vite/index.cjs

node_modules/vite/index.d.cts

node_modules/vite/package.json

node_modules/yallist/LICENSE

node_modules/yallist/README.md

node_modules/yallist/iterator.js

node_modules/yallist/package.json

node_modules/yallist/yallist.js

node_modules/zod/LICENSE

node_modules/zod/README.md

node_modules/zod/index.cjs

node_modules/zod/index.d.cts

node_modules/zod/index.d.ts

node_modules/zod/index.js

node_modules/zod/package.json

node_modules/zustand/LICENSE

node_modules/zustand/README.md

node_modules/zustand/index.d.ts

node_modules/zustand/index.js

node_modules/zustand/middleware.d.ts

node_modules/zustand/middleware.js

node_modules/zustand/package.json

node_modules/zustand/react.d.ts

node_modules/zustand/react.js

node_modules/zustand/shallow.d.ts

node_modules/zustand/shallow.js

node_modules/zustand/traditional.d.ts

node_modules/zustand/traditional.js

node_modules/zustand/ts_version_4.5_and_above_is_required.d.ts

node_modules/zustand/vanilla.d.ts

node_modules/zustand/vanilla.js

ocean/__init__.py

ocean/__main__.py

ocean/__pycache__/__init__.cpython-311.pyc

ocean/__pycache__/__init__.cpython-313.pyc

ocean/__pycache__/__main__.cpython-311.pyc

ocean/__pycache__/actors.cpython-311.pyc

ocean/__pycache__/advisor.cpython-311.pyc

ocean/__pycache__/agents.cpython-311.pyc

ocean/__pycache__/agents.cpython-313.pyc

ocean/__pycache__/backends.cpython-311.pyc

ocean/__pycache__/brave_search.cpython-311.pyc

ocean/__pycache__/cli.cpython-311.pyc

ocean/__pycache__/cli.cpython-313.pyc

ocean/__pycache__/codex_client.cpython-311.pyc

ocean/__pycache__/codex_exec.cpython-311.pyc

ocean/__pycache__/codex_wrap.cpython-311.pyc

ocean/__pycache__/context.cpython-311.pyc

ocean/__pycache__/crewai_adapter.cpython-311.pyc

ocean/__pycache__/dotenv_merge.cpython-311.pyc

ocean/__pycache__/events_emit.cpython-311.pyc

ocean/__pycache__/feed.cpython-311.pyc

ocean/__pycache__/jobs.cpython-311.pyc

ocean/__pycache__/launcher.cpython-311.pyc

ocean/__pycache__/mcp.cpython-311.pyc

ocean/__pycache__/mcp_client.cpython-311.pyc

ocean/__pycache__/mcp_server.cpython-311.pyc

ocean/__pycache__/models.cpython-311.pyc

ocean/__pycache__/models.cpython-313.pyc

ocean/__pycache__/persona.cpython-311.pyc

ocean/__pycache__/personas.cpython-311.pyc

ocean/__pycache__/planner.cpython-311.pyc

ocean/__pycache__/planner.cpython-313.pyc

ocean/__pycache__/product_chat.cpython-311.pyc

ocean/__pycache__/product_loop.cpython-311.pyc

ocean/__pycache__/pty_harness.cpython-311.pyc

ocean/__pycache__/requirements.cpython-311.pyc

ocean/__pycache__/setup_flow.cpython-311.pyc

ocean/__pycache__/token_budget.cpython-311.pyc

ocean/__pycache__/tui_fallback.cpython-311.pyc

ocean/actors.py

ocean/advisor.py

ocean/agents.py

ocean/backends.py

ocean/brave_search.py

ocean/cli.py

ocean/codex_client.py

ocean/codex_exec.py

ocean/codex_wrap.py

ocean/context.py

ocean/core/__init__.py

ocean/core/agents.py

ocean/core/events.py

ocean/core/onboarding.py

ocean/core/orchestrator.py

ocean/core/project_spec.py

ocean/core/state.py

ocean/core/tasks.py

ocean/crewai_adapter.py

ocean/dotenv_merge.py

ocean/events_emit.py

ocean/feed.py

ocean/jobs.py

ocean/launcher.py

ocean/mcp.py

ocean/mcp_client.py

ocean/mcp_server.py

ocean/models.py

ocean/persona.py

ocean/personas.py

ocean/planner.py

ocean/product_chat.py

ocean/product_loop.py

ocean/pty_harness.py

ocean/requirements.py

ocean/runtime/__init__.py

ocean/runtime/cycle.py

ocean/runtime/inbox.py

ocean/runtime/paths.py

ocean/runtime/state.py

ocean/runtime/status.py

ocean/setup_flow.py

ocean/testing/__init__.py

ocean/testing/real_scenarios.py

ocean/testing/scenarios.py

ocean/testing/tmux_scenario_run.py

ocean/token_budget.py

ocean/tools/__init__.py

ocean/tools/deploy.py

ocean/tools/design_system.py

ocean/tools/v0_cli.py

ocean/ui/__init__.py

ocean/ui/app.py

ocean-cli

ocean.egg-info/PKG-INFO

ocean.egg-info/SOURCES.txt

ocean.egg-info/dependency_links.txt

ocean.egg-info/entry_points.txt

ocean.egg-info/requires.txt

ocean.egg-info/top_level.txt

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

ocean_brython-snake/logs/codex-last-edna-20250905-215932.txt

ocean_brython-snake/logs/codex-last-mario-20250905-215951.txt

ocean_brython-snake/logs/codex-last-mario-20250905-220001.txt

ocean_brython-snake/logs/codex-last-mario-20250905-220010.txt

ocean_brython-snake/logs/codex-last-moroni-20250905-215807.txt

ocean_brython-snake/logs/codex-last-q-20250905-215917.txt

ocean_brython-snake/logs/codex-test-last.txt

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

ocean_brython-snake/logs/events-20250905-195815.jsonl

ocean_brython-snake/logs/events-20250905-200442.jsonl

ocean_brython-snake/logs/events-20250905-211056.jsonl

ocean_brython-snake/logs/events-20250905-215433.jsonl

ocean_brython-snake/snake.js

ocean_brython-snake/snake.py

ocean_brython-snake/ui/index.html

ocean_brython-snake/ui/styles.css

ocean_entrypoint.py

ocean_reify/.claude.json.backup

ocean_reify/docs/backlog.json

ocean_reify/docs/ocean_prefs.json

ocean_reify/docs/plan.md

ocean_reify/docs/prd.md

ocean_reify/docs/project.json

ocean_reify/logs/events-20260511-125414.jsonl

ocean_reify/logs/root-venv-install.log

ocean_reify/logs/session-20260511-125414.log

ocean_reify/rainbow_bridge_canal.py

ocean_reify/venv/pyvenv.cfg

package-lock.json

package.json

projects/ocean---multi-agent-software-engineering-orchestrator/.dockerignore

projects/ocean---multi-agent-software-engineering-orchestrator/.env

projects/ocean---multi-agent-software-engineering-orchestrator/Dockerfile

projects/ocean---multi-agent-software-engineering-orchestrator/README.md

projects/ocean---multi-agent-software-engineering-orchestrator/docker-compose.yml

projects/ocean---multi-agent-software-engineering-orchestrator/run.sh

projects/ocean---multi-agent-software-engineering-orchestrator/state.json

pyproject.toml

readme.md

requirements.txt

scripts/check_personas_skills.py

scripts/mcp_stdio_smoke.py

scripts/mcp_talk.py

scripts/mcp_trace.py

scripts/npm-postinstall.mjs

scripts/ocean

scripts/ocean-terminal-interactive.sh

scripts/ocean-terminal-smoke.sh

scripts/regression.sh

scripts/tmux_ocean_scenario.sh

setup.sh

tests/__pycache__/test_backends.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_cli_chat.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_cli_chat.cpython-311.pyc

tests/__pycache__/test_cli_chat.cpython-313-pytest-8.4.1.pyc

tests/__pycache__/test_codex_e2e.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_codex_e2e.cpython-311.pyc

tests/__pycache__/test_control_room.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_core_onboarding.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_launcher.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_mcp_stdio.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_module_invoke.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_ocean_entry_smoke.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_onboarding.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_planner.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_planner.cpython-311.pyc

tests/__pycache__/test_planner.cpython-313-pytest-8.4.1.pyc

tests/__pycache__/test_product_loop.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_product_loop.cpython-311.pyc

tests/__pycache__/test_pty_harness.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_runtime_cycle.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_setup_flow.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_subprocess_flows.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_textual_ocean_pilot.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_token_budget.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_tui_regression.cpython-311-pytest-9.0.3.pyc

tests/__pycache__/test_tui_smoke.cpython-311-pytest-9.0.3.pyc

tests/test_backends.py

tests/test_cli_chat.py

tests/test_codex_e2e.py

tests/test_control_room.py

tests/test_core_onboarding.py

tests/test_launcher.py

tests/test_mcp_stdio.py

tests/test_module_invoke.py

tests/test_ocean_entry_smoke.py

tests/test_onboarding.py

tests/test_planner.py

tests/test_product_loop.py

tests/test_pty_harness.py

tests/test_runtime_cycle.py

tests/test_setup_flow.py

tests/test_subprocess_flows.py

tests/test_textual_ocean_pilot.py

tests/test_textual_real_scenarios.py

tests/test_token_budget.py

tests/test_tui_smoke.py

tsconfig.json

tsconfig.tsbuildinfo

ui/config.js

ui/dist/index.html

ui/index.html

ui/src/main.tsx

ui/src/types.ts

ui/styles.css

venv/bin/Activate.ps1

venv/bin/activate

venv/bin/activate.csh

venv/bin/activate.fish

venv/bin/fastapi

venv/bin/httpx

venv/bin/markdown-it

venv/bin/ocean

venv/bin/ocean-mcp

venv/bin/pip

venv/bin/pip3

venv/bin/pip3.11

venv/bin/py.test

venv/bin/pygmentize

venv/bin/pytest

venv/bin/python

venv/bin/python3

venv/bin/python3.11

venv/bin/typer

venv/bin/uvicorn

venv/bin/wheel

venv/pyvenv.cfg

vite.config.ts

# backend

backend/__pycache__/app.cpython-311.pyc

backend/app.py

# ui

ui/config.js

ui/dist/index.html

ui/index.html

ui/src/main.tsx

ui/src/types.ts

ui/styles.css

# devops

devops/deploy.yaml

devops/regression.md

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

docs/mcp_cursor.md

docs/ocean_prefs.json

docs/personas.yaml

docs/plan.md

docs/prd.md

docs/project.json

docs/repo_scout/workflow.yaml

docs/roadmap.md

docs/search_context.md

docs/test_report.md

docs/textual_tmux_pilot_scenarios.md


## file samples (truncated)

### backend/app.py

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


### ui/dist/assets/index-BKJ8Rgd1.css

:root{--bg: #f5f7f8;--panel: #ffffff;--ink: #1d282c;--muted: #65747a;--line: #d9e2e5;--accent: #0f766e;--accent-2: #b88718;--dark: #182225;--shadow: 0 8px 28px rgba(29, 40, 44, .08)}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;letter-spacing:0}button,input,textarea{font:inherit}button{border:0;border-radius:6px;min-height:38px;padding:9px 13px;background:var(--accent);color:#fff;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px}button:hover{background:#115e59}button:disabled{cursor:not-allowed;opacity:.55}button.ghost{background:#eef3f3;color:var(--ink);border:1px solid var(--line)}button.ghost:hover{background:#e3ebeb}button.secondary{background:#263438}button.secondary:hover{background:#33454a}input,textarea{width:100%;border:1px solid var(--line);border-radius:6px;padding:9px 10px;color:var(--ink);background:#fff}textarea{resize:vertical}input:focus,textarea:focus{outline:2px solid rgba(15,118,110,.18);border-color:var(--accent)}code{padding:2px 5px;border-radius:4px;background:#edf3f4;color:#315d66}.shell{display:grid;grid-template-columns:360px minmax(0,1fr);min-height:100vh}.side{background:var(--dark);color:#fff;padding:20px;display:grid;grid-template-rows:auto auto minmax(230px,auto) minmax(0,1fr);gap:18px}.brand{display:flex;align-items:center;gap:12px}.mark{width:42px;height:42px;border-radius:8px;display:grid;place-items:center;background:#e4b94b;color:#111;font-weight:800}.brand h1,.brand p,.section-head h2,.actor h3,.chat-head h2,.chat-head p{margin:0}.emoji{margin-right:6px}.brand h1{font-size:22px}.brand p,.repo-field span,.section-head span{color:#9fb0b5;font-size:13px}.repo-field{display:grid;gap:7px}.side-section{display:grid;gap:10px;min-height:0}.section-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.section-head h2,.section-head h3{font-size:15px}.actor-list{display:grid;gap:10px;overflow:auto;padding-right:2px}.actor{background:#ffffff12;border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:12px;display:grid;gap:9px}.actor-top{display:flex;justify-content:space-between;gap:10px}.actor h3{font-size:15px}.actor p{margin:3px 0 0;color:#9fb0b5;font-size:12px;line-height:1.35}.filter{background:#ffffff14;color:#fff;border-color:#ffffff29}.filter::placeholder{color:#9fb0b5}.files-section{overflow:hidden}.file-list{overflow:auto;display:grid;gap:4px;padding-right:2px}.file-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;text-align:left;background:transparent;color:#d8e5e8;border:1px solid transparent;padding:7px 8px;min-height:32px}.file-row:hover{background:#ffffff14;border-color:#ffffff1a}.file-row span{display:flex;align-items:center;gap:6px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.file-row small{color:#9fb0b5}.chat{min-width:0;padding:22px;display:grid;grid-template-rows:auto minmax(0,1fr) auto auto;gap:14px}.chat-head{display:flex;justify-content:space-between;gap:18px}.chat-head h2{font-size:26px}.chat-head p{color:var(--muted);margin-top:5px}.runtime{display:flex;align-items:center;gap:8px;color:var(--muted)}.dot{width:9px;height:9px;border-radius:50%;background:#b84d4d}.dot.ok{background:#37a169}.messages{min-height:0;overflow:auto;display:grid;align-content:start;gap:14px;padding-right:4px}.chat-intro{display:grid;gap:4px;padding:14px 16px;border-radius:8px;background:linear-gradient(135deg,#eef6f5,#f8f7f0);border:1px solid var(--line)}.chat-intro span{text-transform:uppercase;letter-spacing:0;font-size:11px;color:var(--accent);font-weight:700}.chat-intro p{margin:0;color:var(--muted);line-height:1.45}.empty{border:1px dashed var(--line);border-radius:8px;padding:18px;color:var(--muted);background:var(--panel)}.msg{display:grid;gap:8px}.meta{color:var(--muted);font-size:12px}.bubble{border:1px solid var(--line);border-radius:8px;padding:12px;background:v

### ui/dist/index.html

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Ocean</title>
    <script type="module" crossorigin src="/assets/index-DtFq_LSk.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-BKJ8Rgd1.css">
  </head>
  <body>
    <div id="root"></div>
    <script>
      window.API_BASE = window.API_BASE || "";
    </script>
  </body>
</html>


### ui/index.html

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta
      name="description"
      content="OCEAN is a multi-agent software engineering orchestrator for planning, assigning, verifying, and shipping work with a FastAPI backend and static UI."
    />
    <title>OCEAN - Multi-Agent Software Engineering Orchestrator</title>
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to content</a>

    <header class="site-header" aria-label="Primary navigation">
      <nav class="nav-shell">
        <a class="brand" href="#top" aria-label="OCEAN home">
          <span class="brand-mark" aria-hidden="true">O</span>
          <span>
            <strong>OCEAN</strong>
            <small>Multi-Agent Orchestrator</small>
          </span>
        </a>
        <div class="nav-links" aria-label="Page sections">
          <a href="#system">System</a>
          <a href="#stack">Stack</a>
          <a href="#handoff">Handoff</a>
        </div>
      </nav>
    </header>

    <main id="main">
      <section id="top" class="hero section-band">
        <div class="hero-shell">
          <div class="hero-copy">
            <p class="eyebrow">Testing enabled. Containerized. FastAPI backed.</p>
            <h1>OCEAN runs the crew. You steer the build.</h1>
            <p class="lead">
              A sharp control surface for multi-agent software engineering: product intent, backlog ownership, codegen context, runtime status, and verification in one disciplined loop.
            </p>
            <div class="hero-actions" aria-label="Primary actions">
              <a class="button primary" href="#handoff">Start the handoff</a>
              <a class="button secondary" href="#system">Inspect the system</a>
            </div>
          </div>

          <figure class="orchestration-board" aria-label="OCEAN orchestration board preview">
            <div class="board-topline">
              <span>Live Project</span>
              <strong>Ready</strong>
            </div>
            <div class="board-grid">
              <div class="board-card captain">
                <span class="node-dot"></span>
                <strong>Captain</strong>
                <p>Ranks the next valuable move.</p>
              </div>
              <div class="board-card q">
                <span class="node-dot"></span>
                <strong>Q</strong>
                <p>Locks API contracts and tests.</p>
              </div>
              <div class="board-card edna">
                <span class="node-dot"></span>
                <strong>Edna</strong>
                <p>Shapes the static interface.</p>
              </div>
              <div class="board-card mario">
                <span class="node-dot"></span>
                <strong>Mario</strong>
                <p>Ships CI, Docker, deploys.</p>
              </div>
            </div>
            <div class="pipeline" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </figure>
        </div>
      </section>

      <section id="system" class="section-band system-section">
        <div class="content-shell">
          <div class="section-heading">
            <p class="eyebrow">System discipline</p>
            <h2>One control plane for planning, execution, and proof.</h2>
          </div>
          <div class="feature-grid">
            <article class="feature-card">
              <span class="feature-kicker">01</span>
              <h3>Backlog with owners</h3>
              <p>Each task has a named agent, touched files, acceptance criteria, and a clean handoff path.</p>
            </article>
            <article class="feature-card">
              <span class="feature-kicker">02</span>
              <h3>File-first context</h3>
              <p>Project state stays reviewable i

### ui/styles.css

:root {
  color-scheme: light;
  --color-ink: #172126;
  --color-muted: #52636a;
  --color-soft: #eef4f4;
  --color-surface: #ffffff;
  --color-surface-strong: #f8fbfb;
  --color-line: #d4e0e2;
  --color-dark: #111b20;
  --color-dark-2: #1d2b31;
  --color-teal: #0f766e;
  --color-teal-strong: #115e59;
  --color-gold: #b88718;
  --color-coral: #b84d4d;
  --color-focus: #f2b84b;
  --shadow-soft: 0 18px 50px rgba(17, 27, 32, 0.12);
  --shadow-tight: 0 10px 28px rgba(17, 27, 32, 0.1);
  --radius-sm: 6px;
  --radius-md: 8px;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;
  --space-8: 4rem;
  --space-9: 6rem;
  --font-body: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --content: 1160px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  background: var(--color-soft);
  color: var(--color-ink);
  font-family: var(--font-body);
  line-height: 1.5;
  letter-spacing: 0;
}

body::before {
  position: fixed;
  inset: 0;
  z-index: -1;
  content: "";
  background:
    linear-gradient(90deg, rgba(17, 27, 32, 0.04) 1px, transparent 1px),
    linear-gradient(rgba(17, 27, 32, 0.04) 1px, transparent 1px),
    var(--color-soft);
  background-size: 44px 44px;
}

a {
  color: inherit;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
  text-underline-offset: 0.22em;
}

a:focus-visible,
button:focus-visible {
  outline: 3px solid var(--color-focus);
  outline-offset: 4px;
}

.skip-link {
  position: fixed;
  top: var(--space-4);
  left: var(--space-4);
  z-index: 20;
  transform: translateY(-160%);
  border-radius: var(--radius-sm);
  background: var(--color-dark);
  color: #ffffff;
  padding: var(--space-3) var(--space-4);
  font-weight: 800;
}

.skip-link:focus {
  transform: translateY(0);
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid rgba(212, 224, 226, 0.84);
  background: rgba(248, 251, 251, 0.92);
  backdrop-filter: blur(14px);
}

.nav-shell,
.content-shell,
.hero-shell {
  width: min(100% - 2rem, var(--content));
  margin-inline: auto;
}

.nav-shell {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 48px;
}

.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: var(--color-gold);
  color: #111111;
  font-weight: 900;
  box-shadow: var(--shadow-tight);
}

.brand strong,
.brand small {
  display: block;
}

.brand strong {
  font-size: 1rem;
  line-height: 1.1;
}

.brand small {
  margin-top: 0.15rem;
  color: var(--color-muted);
  font-size: 0.78rem;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: clamp(var(--space-3), 2vw, var(--space-6));
  color: var(--color-muted);
  font-size: 0.94rem;
  font-weight: 750;
}

.section-band {
  padding-block: var(--space-9);
}

.hero {
  min-height: calc(100vh - 72px);
  display: grid;
  align-items: center;
  background:
    linear-gradient(120deg, rgba(17, 27, 32, 0.96), rgba(22, 45, 49, 0.9)),
    var(--color-dark);
  color: #ffffff;
}

.hero-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.82fr);
  align-items: center;
  gap: clamp(var(--space-6), 7vw, var(--space-9));
}

.hero-copy {
  max-width: 720px;
}

.eyebrow {
  margin: 0 0 var(--space-3);
  color: var(--color-gold);
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1,
h2,
h3 {
  line-height: 1.05;
  letter-spacing: 0;
}

h1 {
  margin-bottom: var(--space-5);
  max-width: 820px;
  font-size: clamp(3rem, 8vw, 6.7rem);
}

h2 {
  margin-bottom: var(--space-4);
  font-size: clamp(2rem, 4vw, 3.75rem);
}

h3 {
  

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

# 🌊 OCEAN - Multi-Agent Software Engineering Orchestrator - Architecture

## Mission

OCEAN is a web-based orchestration control room for multi-agent software engineering. It keeps product intent, agent responsibilities, backlog execution, runtime status, and verification feedback in one clear operating surface.

The standard is simple: file-first context, a small FastAPI backend, a static browser UI, reliable tests, and a containerized runtime that can be moved without ceremony.

## Goals

- Testing enabled with a repeatable pytest suite and CI checks.
- Containerized so the same application can run locally or in deployment.
- FastAPI backend for health, state, planning, chat, and orchestration endpoints.
- Static UI for the control room experience.
- Minimal dependencies and explicit operational boundaries.

## Constraints

- Prefer the Python standard library and existing project dependencies before adding packages.
- Keep the backend deployable as a single FastAPI application.
- Keep the UI static and build-output friendly.
- Avoid database requirements for the core loop until a later milestone proves the need.
- Preserve durable project state in plain files so decisions remain reviewable.

## System Shape

```text
User / Browser
      |
      v
Static UI: ui/ or ui/dist/
      |
      v
FastAPI Backend: backend/app.py
      |
      v
Ocean Core Modules: ocean/*
      |
      v
Project Files: docs/*, .ocean/*, doctrine markdown, logs/*
```

## Architecture Principles

### File-First State

OCEAN treats the repository as the source of truth. Project context, backlog, plans, doctrine, chat history, and job records are stored in files that can be reviewed, diffed, committed, and recovered.

Primary state locations:

- `docs/project.json` for project identity, goals, constraints, and vision.
- `docs/backlog.json` for planned work.
- `docs/plan.md` for visible execution sequencing.
- `docs/context_summary.md` for compressed codegen context.
- `.ocean/actors.json` for crew definitions.
- `.ocean/jobs.json` for generated jobs.
- `.ocean/chat.jsonl` for chat history.
- Doctrine files such as `VISION.md`, `TASKS.md`, `FEEDBACK.md`, and `DECISIONS.md`.

### Small Control Plane

The FastAPI backend should coordinate the system, not become a general application platform. Its job is to expose bounded operations over project state and orchestration workflows.

Core responsibilities:

- Serve the static UI.
- Report runtime health.
- Read project context and doctrine.
- Manage actors and jobs.
- Accept chat turns and product feedback.
- Produce scoped handoff prompts for coding agents.

### Static Command Surface

The UI is the operator console. It should help the user see the mission, crew, files, chat, and next action without hiding important state behind opaque services.

Expected interface areas:

- Project identity and runtime health.
- Crew and actor coverage.
- Chat-first feedback loop.
- Relevant file inspection.
- Job planning and handoff prompts.
- Test and readiness summaries.

## Runtime Components

### FastAPI Backend

Anchor module: `backend/app.py`

Expected endpoint groups:

- Health: `GET /healthz`
- Root or app shell: `GET /`
- State: project, actors, coverage, doctrine, and runtime summary.
- Chat: record user turns, feedback, and test notes.
- Jobs: generate and list scoped work items.
- Files: read bounded project files safely under the project root.

Backend standards:

- Validate request and response shapes with typed models where useful.
- Resolve paths safely under the intended project root.
- Return clear HTTP errors for missing files, invalid input, or unsafe paths.
- Keep endpoint names aligned with product workflow.
- Cover new behavior with focused pytest tests.

### Static UI

Source location: `ui/`

Build output: `ui/dist/`

The UI may run in two modes:

- Development: Vite or a lightweight static dev server.
- Production: compiled static assets served by FastAPI or a static host.

UI standards:

- Priorit

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
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
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
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8004/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  },
  {
    "title": "Run test suite and write report",
    "description": "Execute pytest (if present) and record a concise report",
    "owner": "Tony",
    "files_touched": [
      "docs/test_report.md"
    ]
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
  "vision": "## Summary",
  "ai_identity": "Your coding partner on **🌊 OCEAN - Multi-Agent Software Engineering Orchestrator** — Ocean runs the crew and timing; you steer goals and say when we're done.",
  "createdAt": "2026-05-12T10:15:46.528184"
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
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
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
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8004/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  },
  {
    "title": "Run test suite and write report",
    "description": "Execute pytest (if present) and record a concise report",
    "owner": "Tony",
    "files_touched": [
      "docs/test_report.md"
    ]
  }
]



## plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)
- [Tony] Run test suite and write report — docs/test_report.md



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
- Tech: Python/pyproject, requirements.txt, Node/package.json, Dockerfile, GitHub Actions



## repository tree (depth=3)

# .

.cursor/rules/run-ocean.mdc

.cursorrules

.dockerignore

.env.example

.git/COMMIT_EDITMSG

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

.git

### docs/context_summary.md

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
  "vision": "## Summary",
  "ai_identity": "Your coding partner on **🌊 OCEAN - Multi-Agent Software Engineering Orchestrator** — Ocean runs the crew and timing; you steer goals and say when we're done.",
  "createdAt": "2026-05-12T10:15:46.528184"
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
    "title": "Create web backend",
    "description": "Implement FastAPI backend with endpoints",
    "owner": "Q",
    "files_touched": [
      "backend/app.py",
      "backend/models.py"
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
    "description": "Launch local backend (and UI if present) and print URL | URLs: http://127.0.0.1:8004/healthz | http://127.0.0.1:5173",
    "owner": "Mario",
    "files_touched": []
  },
  {
    "title": "Run test suite and write report",
    "description": "Execute pytest (if present) and record a concise report",
    "owner": "Tony",
    "files_touched": [
      "docs/test_report.md"
    ]
  }
]



## plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)
- [Tony] Run test suite and write report — docs/test_report.md



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
- Tech: Python/pyproject, requirements.txt, Node/package.json, Dockerfile, GitHub Actions



## repository tree (depth=3)

# .

.cursor/rules/run-ocean.mdc

.cursorrules

.dockerignore

.env.example

.git/COMMIT_EDITMSG

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

.git

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


### docs/mcp_cursor.md

# Ocean MCP for Cursor

Ocean can run outside a target codebase as a stdio MCP server. Cursor or another coding agent can call it each turn for product guidance, feedback capture, and task ranking.

The local Web UI is chat-first. Keep orchestration simple: one chat, a five-person crew, and filesystem context. Users can mention files with `@path` and update doctrine through chat:

```text
update VISION.md: Ocean stays simple: chat is the interface, files are context, and Cursor gets one job at a time.
append to TASKS.md: Verify first-run Cursor setup.
```

The default crew is capped at five actors: Captain, Edna, Q, Mario, and Scrooge.

Ocean does not ship an LLM. It keeps durable product context and asks the available brain to reason over it.

## Install

From the Ocean repo:

```bash
pip install -e .
```

This exposes:

```bash
ocean-mcp
ocean mcp-server
python -m ocean.mcp_server
```

## Cursor Configuration

Add Ocean to Cursor's MCP config:

```json
{
  "mcpServers": {
    "ocean": {
      "command": "ocean-mcp",
      "args": []
    }
  }
}
```

If the console cannot find `ocean-mcp`, use the explicit Python module form:

```json
{
  "mcpServers": {
    "ocean": {
      "command": "python",
      "args": ["-m", "ocean.mcp_server"]
    }
  }
}
```

## Turn Workflow

At the start of a coding turn, call `ocean_turn` with:

```json
{
  "project_root": "/absolute/path/to/target/repo",
  "user_turn": "Latest user request",
  "test_results": "Optional test summary",
  "candidate_tasks": ["Optional task A", "Optional task B"],
  "use_advisor": true
}
```

If no external advisor is configured, the response still includes `advisor_prompt`. Cursor's own model can read that prompt and produce the product-manager judgment. That is the default model-agnostic path.

## Optional Reasoning CLI

To let Ocean ask a reasoning engine directly, configure one of these environment variables before launching the MCP server:

```bash
export OCEAN_PM_ADVISOR_CMD='your-reasoning-cli --stdin'
```

Ocean sends the Product Manager prompt on stdin and reads stdout as advice.

For Codex:

```bash
export OCEAN_PM_ADVISOR=codex
```

Ocean then calls `codex exec` in a read-only sandbox and folds the answer into `ocean_turn`. This keeps Ocean open-source and model-agnostic while still using whatever brain the user already has installed.

After Reif reacts to a build or test, call the same tool with `feedback`, or call `ocean_record_feedback` directly:

```json
{
  "project_root": "/absolute/path/to/target/repo",
  "feedback": "This feels too technical. Explain it like a smart assistant, not a terminal.",
  "test_context": "Onboarding flow tested locally."
}
```

Ocean will maintain these files in the target repo:

- `VISION.md`
- `AUDIENCE.md`
- `PRODUCT_PRINCIPLES.md`
- `UX_RULES.md`
- `POSITIONING.md`
- `ROADMAP.md`
- `TASKS.md`
- `FEEDBACK.md`
- `DECISIONS.md`

## Available Tools

- `ocean_turn`: record optional feedback and return the next highest-value instruction.
- `ocean_next_action`: rank tasks and return the smallest valuable next move.
- `ocean_record_feedback`: append feedback and update doctrine.
- `ocean_bootstrap_doctrine`: create missing doctrine files without overwriting existing files.

## Orchestration Jobs

Chat and `/api/jobs/plan` turn product intent into discrete Cursor-ready jobs. Each job includes:

- owner persona
- lifecycle phase
- objective
- context
- instructions
- acceptance criteria
- verification
- handoff notes
- a copyable Cursor prompt

This is the core division of labor: Cursor, Claude, and Codex write code well; Ocean drives the software-development team process around them without becoming a second full coding UI.

## How Ocean Knows What To Build

Ocean does not guess from doctrine alone. For each turn it pulls a bounded build context from the target repo:

- current git branch, status, and recent commits
- detected stack from manifests and config files
- important files such as `README.md`, `pyproject.toml`, `packag

### docs/ocean_prefs.json

{
  "codegen_backend": "codex"
}


### docs/personas.yaml

agents:
  Mario:
    emoji: "🍄"
    skills:
      - GitHub Actions, Dockerfiles, Compose orchestration
      - CI/CD wiring, rollout & rollback drills
      - Render/Railway-style deploy stubs & env hygiene
      - Monitoring hooks, health checks, local staging
    traits:
      - Pragmatic, resilient, production-first
      - Optimistic and energetic, fixes “clogs” fast
    diction:
      - "It’s-a me, Mario!"
      - "Let’s-a go!"
      - "Here we go!"
      - 'Simple exclamations: "Mamma mia!", "Wahoo!", "Woo-hoo!"'
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
    emoji: "🔧"
    traits:
      - Dry wit, surgical precision, loves gadgets
      - Test-driven, obsessed with safety nets
    skills:
      - Python backends (FastAPI, services, integrations)
      - Data models, API contracts, test-driven loops
      - pytest, guardrails, fail-safe defaults
      - Codex MCP implementation passes
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
    emoji: "🧪"
    skills:
      - Exploratory & stress-path testing against new builds
      - pytest harnesses, shell probes, reproducible bugs
      - Telemetry reads, flaky-test triage
      - docs/test_report.md narratives for the crew
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
      do: "Edge cases tested. Broke on #2, fixed it. 🧪"
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
      - "I b

### docs/plan.md

# Initial Plan

## Backlog

- [Moroni] Design web application architecture — docs/architecture.md, docs/api_design.md
- [Q] Create web backend — backend/app.py, backend/models.py
- [Edna] Create web interface design — ui/index.html, ui/styles.css, docs/design_system.md
- [Mario] Prepare codegen context — docs/context_summary.md
- [Mario] Add CI workflow — .github/workflows/ci.yml
- [Mario] Create Dockerfile — Dockerfile, .dockerignore
- [Mario] Create deployment config — devops/deploy.yaml
- [Mario] Start local runtime — (tbd)
- [Tony] Run test suite and write report — docs/test_report.md


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
- Tech: Python/pyproject, requirements.txt, Node/package.json, Dockerfile, GitHub Actions


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
  "vision": "## Summary",
  "ai_identity": "Your coding partner on **🌊 OCEAN - Multi-Agent Software Engineering Orchestrator** — Ocean runs the crew and timing; you steer goals and say when we're done.",
  "createdAt": "2026-05-12T10:15:46.528184"
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

## HTML CSS landing page accessibility checklist
- [WebAIM: WebAIM's WCAG 2 Checklist](https://webaim.org/standards/wcag/checklist) — Images that do not convey content, ... as <strong>CSS</strong> backgrounds. All linked images have descriptive alternative text. Equivalent alternatives to complex images are provided in context or on a separate linked <strong>page</strong>. Form buttons have a descriptive value. Inputs have associated <strong>accessible</strong> ...
- [HTML: A good basis for accessibility - Learn web development | MDN](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML) — A great deal of web content can be made <strong>accessible</strong> just by making sure the correct Hypertext Markup Language elements are used for the correct purpose at all times. This article looks in detail at how <strong>HTML</strong> can be used to ensure maximum <strong>accessibility</strong>.
- [Easy Checks – A First Review of Web Accessibility | Web Accessibility Initiative (WAI) | W3C](https://www.w3.org/WAI/test-evaluate/preliminary/) — Open the web page you are checking. <strong>In the toolbar, select &quot;Images&quot;, then &quot;Remove Images&quot;.</strong> Or, with the keyboard: Ctrl+Alt+4, then arrow down to &quot;Remove Images&quot;. In the toolbar, select &quot;CSS&quot;, then &quot;Disable CSS&quot;.
- [Web Accessibility Checklist](https://www.webaccessibilitychecklist.com/) — <strong>Adding an HTML sitemap page (which links to every page on your website).</strong> Including a search function on every page. Providing a clear and consistent main navigation menu. ... Do not rely on hover states to convey information as this approach is not screen reader, keyboard or mobile accessible.
- [Accessibility | MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility) — <strong>Accessibility</strong> (often abbreviated to A11y — as in, &quot;a&quot;, then 11 characters, and then &quot;y&quot;) in web development means enabling as many people as possible to use websites, even when those people&#x27;s abilities are limited in some way.


### docs/test_report.md

# Test Report

Generated: 2026-05-12T10:15:21.868816

## Pytest Output

````
..............sFFFF.................................................     [100%]
=================================== FAILURES ===================================
____________________ test_control_room_state_jobs_and_chat _____________________

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-171/test_control_room_state_jobs_a0')

    def test_control_room_state_jobs_and_chat(tmp_path):
        client = TestClient(app)
    
        state = client.get("/api/state", params={"project_root": str(tmp_path)}).json()
>       assert state["coverage"]["gaps"] == []
               ^^^^^^^^^^^^^^^^^
E       KeyError: 'coverage'

tests/test_control_room.py:10: KeyError
____________________________ test_filesystem_routes ____________________________

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-171/test_filesystem_routes0')

    def test_filesystem_routes(tmp_path):
        client = TestClient(app)
        (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")
    
        files = client.get("/api/files", params={"project_root": str(tmp_path)}).json()
>       assert {"path": "README.md", "size": 8} in files["files"]
                                                   ^^^^^^^^^^^^^^
E       KeyError: 'files'

tests/test_control_room.py:45: KeyError
_____________________ test_chat_can_update_doctrine_files ______________________

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-171/test_chat_can_update_doctrine_0')

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

tmp_path = PosixPath('/private/var/folders/cr/23hzng994jg6rtwz24dpf_xm0000gn/T/pytest-of-reify/pytest-171/test_chat_saves_screenshot_as_0')

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


### docs/textual_tmux_pilot_scenarios.md

# Textual + Pilot + tmux: real-life test scenarios

Ocean’s Textual shell runs **Moroni-style onboarding** (five answers) then writes **`docs/project.json`**. After that you can queue **`task add …`** lines the same way you would in a real session.

This doc ties together:

1. **Scenario catalogue** — `ocean/testing/real_scenarios.py` (`TextualProductScenario`).
2. **Textual Pilot** — in-process tests in `tests/test_textual_real_scenarios.py` (fast CI).
3. **tmux** — `python -m ocean.testing.tmux_scenario_run <id>` (real pseudo-TTY, closer to how you run `ocean` in iTerm).

> These scenarios prove **spec capture + task queueing** in the Textual shell. They do **not** compile or ship a full game build; codegen still flows through **`ocean chat`** / Codex / your editor.

## Scenario IDs

| ID | Intent |
|----|--------|
| `tic_tac_toe_localhost` | Browser tic-tac-toe on localhost; three follow-up tasks (board, win detection, dev server docs). |
| `paddle_wars_keen` | Keen-style paddle arena; three follow-up tasks (paddle/ball, bricks/HUD, pause/restart). |
| `cli_devtools_scratch` | Small **cli** utility; one follow-up task. |

## Pilot (pytest)

```bash
pytest tests/test_textual_real_scenarios.py -q --tb=short
```

Parametrized over every scenario in `SCENARIOS`.

## tmux (manual or optional CI)

From the **repository root** (venv with `ocean` installed):

```bash
python -m ocean.testing.tmux_scenario_run tic_tac_toe_localhost
python -m ocean.testing.tmux_scenario_run paddle_wars_keen
```

Or the thin wrapper:

```bash
bash scripts/tmux_ocean_scenario.sh paddle_wars_keen
```

Requirements: **`tmux`** on `PATH`, **`./venv/bin/ocean`** executable.

The driver creates a **temporary workspace**, starts **`ocean`** inside tmux (so stdin/stdout are TTYs), **types each line** with pauses, then checks **`docs/project.json`** on disk.

## Adding a scenario

1. Append a new `TextualProductScenario(...)` to `ocean/testing/real_scenarios.py` and register it in `SCENARIOS`.
2. Keep **`onboarding_lines` ASCII-only** and avoid embedded quotes (tmux `send-keys` passes each Python `str` as one argument — spaces are fine).
3. Run Pilot + tmux smoke for the new id.

## Failure triage

Use `ocean.testing.scenarios.pilot_failure_report(...)` from a failing Pilot test to capture **`export_state()`**, recent feed lines, and a traceback for agents.

