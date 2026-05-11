# 🌊 OCEAN - Multi-Agent Software Engineering Orchestrator

OCEAN (OCEAN can engineer Asinine Nonrequirements) is a **CLI/TUI multi-agent orchestrator** that spins up a software engineering team on demand.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Install Globally (Optional)
```bash
# Create global symlink (requires sudo)
sudo ln -sf "$(pwd)/ocean" /usr/local/bin/ocean
```

### 3. Run OCEAN
```bash
# Start the full interactive experience
ocean

# Or run specific commands:
ocean --help          # Show all commands
ocean clarify         # Project clarification with Moroni
ocean crew            # Meet the OCEAN crew
ocean test            # Run tests
```

### 4. Start The React Control Room
```bash
npm install
ocean ui
```

Then open `http://127.0.0.1:5173/` for the chat-first React interface. The API runs on `http://127.0.0.1:7777/`.

## 🎯 What OCEAN Does

OCEAN is a **terminal-based orchestrator** that:

1. **🤖 Clarifies your vision** - Moroni asks questions to understand your project
2. **👥 Assembles your team** - Spins up specialized AI agents (Q, Edna, Mario)
3. **📋 Creates your plan** - Generates project backlog and execution plan
4. **🚀 Scaffolds your project** - Creates initial project structure and files

Ocean still has a terminal-first CLI, but it also ships a React control room for direct chat, file inspection, feedback capture, and job handoff.

## 🔧 Available Commands

| Command | Description |
|---------|-------------|
| `ocean` | **Main experience** - Full interactive flow (clarify → crew → plan) |
| `ocean clarify` | Project clarification with Moroni (Architect) |
| `ocean crew` | Meet the OCEAN crew and see their specialties |
| `ocean init` | Generate/refresh project scaffolds |
| `ocean test` | Run the test suite |
| `ocean deploy` | Show deployment plan (dry-run) |
| `ocean ui` | Start the React chat control room and local API |
| `ocean mcp-server` | Run Ocean as a stdio MCP server for Cursor/Codex |
| `ocean-mcp` | Direct MCP server entrypoint |

## External MCP Product Loop

Ocean can now guide a target codebase from the outside. Configure Cursor or another MCP client to launch `ocean-mcp`, or use the local React control room with `ocean ui`.

The control room is intentionally simple: one chat, a small five-person crew, and a file browser for context. File and doctrine changes happen through chat, for example:

```text
update VISION.md: Ocean stays simple: chat is the interface, files are context, and Cursor gets one job at a time.
append to TASKS.md: Add first-run Cursor setup smoke test.
Look at @ui/index.html and tell Cursor what to do next.
```

Each crew member is rendered with an emoji identity so the conversation is easy to scan:

- `Captain` 🧭
- `Edna` 🎨
- `Q` 🛠️
- `Mario` 🚢
- `Scrooge` 💰

Ocean does not ship a model. It keeps product doctrine, feedback, and task context, then uses the available brain:

- Cursor or Codex can reason over the returned `advisor_prompt`.
- Set `OCEAN_PM_ADVISOR_CMD='your-reasoning-cli --stdin'` to have Ocean call a local reasoning CLI.
- Set `OCEAN_PM_ADVISOR=codex` to have Ocean ask `codex exec` for Product Manager judgment in a read-only sandbox.

Ocean maintains product doctrine in the target repo:

- `VISION.md`
- `AUDIENCE.md`
- `PRODUCT_PRINCIPLES.md`
- `UX_RULES.md`
- `POSITIONING.md`
- `ROADMAP.md`
- `TASKS.md`
- `FEEDBACK.md`
- `DECISIONS.md`

The MCP server exposes:

- `ocean_turn` - record optional feedback and return the next highest-value instruction.
- `ocean_next_action` - rank candidate tasks by user value, setup friction reduced, trust increased, demo power, dependency value, and risk.
- `ocean_record_feedback` - turn reactions into durable doctrine and tasks.
- `ocean_bootstrap_doctrine` - create missing doctrine files without overwriting existing files.

Each turn, Ocean pulls bounded build context from the target repo, including git state, detected stack, key docs/manifests, test report, backlog, and file tree. It sends that context to the available reasoning brain, asks for strict JSON, parses the result, and returns `advisor_recommendation` plus coding-agent instructions.

The default crew is capped at five actors:

- `Captain`: product orchestration and scope.
- `Edna`: UX, onboarding, and product feel.
- `Q`: implementation.
- `Mario`: verification and shipping.
- `Scrooge`: impact, adoption, and money.

See `docs/mcp_cursor.md` for Cursor configuration.

## 🤖 The OCEAN Crew

OCEAN spins up a **Codex-powered software engineering team** with specialized agents:

### **Moroni** — Architect & Brain
- **Role:** Clarifies vision, orchestrates the team, creates project specifications
- **Capabilities:** Project planning, milestone definition, coordination
- **Deliverables:** Project specs, coordination plans, architectural decisions

### **Q** — Backend Engineer
- **Role:** Builds APIs, services, data models, and backend infrastructure
- **Capabilities:** FastAPI development, database design, API integration
- **Deliverables:** Backend services, data models, API endpoints

### **Edna** — Designer & UI/UX Engineer
- **Role:** Creates user interfaces, design systems, and user experience flows
- **Capabilities:** UI design, CSS/HTML, design tokens, user flows
- **Deliverables:** Frontend interfaces, design systems, user experience

### **Mario** — DevOps Engineer
- **Role:** Handles deployment, CI/CD, infrastructure, and cloud platforms
- **Capabilities:** Docker, CI/CD pipelines, cloud deployment, monitoring
- **Deliverables:** Deployment configs, CI workflows, live applications

## 🌟 CLI/TUI Features

### **Rich Terminal Experience**
- **Beautiful tables** - Project summaries, crew info, backlog display
- **Progress indicators** - Visual feedback during operations
- **Color-coded output** - Easy to read and navigate
- **Interactive prompts** - Guided project clarification

### **Session Management**
- **Automatic logging** - Every session saved to timestamped log files
- **Project persistence** - Saves and loads project specifications
- **Audit trail** - Track all agent interactions and decisions

### **Project Scaffolding**
- **Backend templates** - FastAPI, tests, CI workflows
- **Frontend placeholders** - HTML, CSS, design tokens
- **DevOps configs** - Docker, deployment, monitoring
- **Documentation** - Project specs, plans, backlogs

## 🏗️ Project Structure

```
ocean/
├── ocean/              # CLI application (core)
│   ├── cli.py         # Command interface
│   ├── agents.py      # Agent definitions
│   ├── models.py      # Data models
│   └── planner.py     # Task planning
├── docs/              # Documentation & specs
├── logs/              # Session logs
├── backend/           # Generated backend scaffolds
├── ui/                # Generated frontend scaffolds
├── devops/            # Generated deployment configs
├── tests/             # Generated test suites
├── .github/           # Generated CI/CD workflows
├── pyproject.toml     # Package configuration
└── .cursorrules       # Development rules
```

## 🧪 Testing

```bash
# Run all tests
ocean test

# Run specific test suites
pytest tests/
```

## 🚀 Deployment

### Show Deployment Plan
```bash
# Preview deployment steps
ocean deploy --dry-run

# Execute deployment (when implemented)
ocean deploy --no-dry-run
```

## 🔄 Development Workflow

1. **Start OCEAN:** `ocean` (interactive flow)
2. **Clarify vision:** Answer Moroni's questions
3. **Meet the crew:** See your AI team
4. **Get your plan:** Review backlog and tasks
5. **Generate scaffolds:** `ocean init` to create project files
6. **Iterate:** Run `ocean` again to refine

## 🐛 Troubleshooting

### Common Issues

**Command not found:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -e .
```

**Tests failing:**
```bash
# Check dependencies
pip install -e .
# Run specific test
pytest tests/ -v
```

**No project spec:**
```bash
# Run clarification first
ocean clarify
```

## 📚 Next Steps

- [ ] Add more agent capabilities
- [ ] Implement task execution
- [ ] Add database persistence
- [ ] Deploy to cloud platform
- [ ] Add authentication and user management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `ocean test`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

## 🔄 Recent Transformation

OCEAN has been **transformed from a web application back to its intended purpose**: a powerful CLI/TUI multi-agent orchestrator. 

**What was removed:**
- ❌ Web servers and APIs
- ❌ Browser-based UI
- ❌ Docker containers
- ❌ Complex deployment configs

**What remains:**
- ✅ **Rich CLI/TUI experience** with beautiful tables and progress bars
- ✅ **Multi-agent orchestration** - Moroni, Q, Edna, Mario
- ✅ **Project scaffolding** and planning
- ✅ **Session logging** and persistence
- ✅ **Clean, focused architecture**

OCEAN is now **exactly what it was meant to be**: a terminal-based orchestrator that spins up your AI-powered software engineering team! 🎯 
