<p align="center">
  <img src="https://img.shields.io/badge/NVIDIA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Version-7.0.0-blue?style=for-the-badge" alt="Version 7.0.0">
</p>

<h1 align="center">NVIDIA CLI v7.0</h1>

<p align="center">
  <strong>An OpenClaw-inspired multi-agent AI framework for NVIDIA's AI endpoints.</strong><br>
  Build, manage, and orchestrate AI agents with persistent memory, installable skills, and a soul/identity system — all from your terminal.
</p>

<p align="center">
  <a href="#features">Features</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#usage">Usage</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#contributing">Contributing</a> &bull;
  <a href="#license">License</a>
</p>

---

## Features

### Multi-Agent System
Create and manage multiple AI agents, each with their own configuration, model preferences, and behavior. Spawn subagents for parallel task execution.

```bash
nv agent list              # List all agents
nv agent create mybot      # Create a new agent
nv agent delete mybot      # Remove an agent
```

### Soul / Identity System (OpenClaw)
Give your agents personality through file-based identity documents:

| File | Purpose |
|------|---------|
| `SOUL.md` | Core personality principles and values |
| `IDENTITY.md` | Agent name, emoji, avatar |
| `USER.md` | Human preferences and context |
| `MEMORY.md` | Curated long-term memories |
| `HEARTBEAT.md` | Periodic task definitions |

### Skills System
Discover, install, and manage agent skills with built-in security scanning.

```bash
nv skill list              # List installed skills
nv skill install <path>    # Install a skill (pip, npm, brew, git)
nv skill uninstall <name>  # Remove a skill
```

Skills are auto-discovered via `SKILL.md` files and scanned for dangerous patterns (`eval`, `exec`, `subprocess` abuse) before installation.

### Hybrid Memory
Persistent memory with hybrid search combining vector embeddings and keyword (BM25) matching.

```bash
nv memory add "Project uses FastAPI with PostgreSQL"
nv memory search "database setup"
```

- SQLite-backed persistent storage
- Embedding providers: OpenAI, local (sentence-transformers)
- Automatic context injection into conversations

### Heartbeat System
Schedule periodic tasks that run within your agent's context.

```bash
nv heartbeat status        # Check heartbeat task status
```

- Quiet hours support
- Batch processing for grouped checks

### Interactive Chat & One-Shot Queries
```bash
nv chat                    # Start interactive chat session
nv ask "Explain CUDA cores" # One-shot query
```

### In-Chat Slash Commands
| Command | Description |
|---------|-------------|
| `/init` | Analyze codebase, generate context file |
| `/add <file>` | Load a file into conversation context |
| `/clear` | Reset conversation and file context |
| `/model <name>` | Switch AI model |
| `/skill` | Manage skills within chat |
| `/help` | Show available commands |
| `/quit` | Exit with session summary |

### Available Models

| Alias | Model |
|-------|-------|
| `default` | `deepseek-ai/deepseek-v3.2` |
| `nano` | `nvidia/nemotron-nano-12b-v2-vl` |
| `llama70` | `nvidia/llama-3.1-nemotron-70b-instruct` |
| `llama8` | `meta/llama-3.1-8b-instruct` |

### Permission Modes

Control how the agent interacts with your system:

| Mode | Behavior |
|------|----------|
| `ask` | Always ask before any action (default) |
| `accept_edits` | Auto-accept file edits, ask for other actions |
| `auto` | Auto-approve safe operations |
| `never` | Dry-run mode — no actions executed |

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- An NVIDIA API key from [build.nvidia.com](https://build.nvidia.com/explore)

### Installation

```bash
# Clone the repository
git clone https://github.com/SingularityAI-Dev/Nvidia-CLI.git
cd Nvidia-CLI

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### Set Up Your API Key

```bash
# Option 1: Environment variable
export NVIDIA_API_KEY="nvapi-your-key-here"

# Option 2: .env file in project root
echo 'NVIDIA_API_KEY=nvapi-your-key-here' > .env

# Option 3: Let the CLI prompt you on first run
nv chat
```

The API key is stored in `~/.nv-cli-config/config.json` after first setup.

---

## Usage

### Interactive Chat

```bash
$ nv chat

 ███╗   ██╗██╗   ██╗
 ████╗  ██║██║   ██║    NVIDIA CLI v7.0
 ██╔██╗ ██║██║   ██║    AI Agent Framework
 ██║╚██╗██║╚██╗ ██╔╝
 ██║ ╚████║ ╚████╔╝
 ╚═╝  ╚═══╝  ╚═══╝

nv> /init
[*] Analyzing codebase...
[*] Context saved to .nv/NVIDIA.md

nv> How is authentication handled in this project?
```

### One-Shot Query

```bash
nv ask "What is the difference between CUDA and OpenCL?"
```

### Agent Management

```bash
# Create a specialized coding agent
nv agent create coder

# Configure it
nv config edit

# List all agents
nv agent list
```

### Working With Context

```bash
# In chat, load files for context-aware answers
nv> /add src/main.py
nv> /add requirements.txt
nv> What dependencies does this project need?
```

---

## Architecture

```
nv_cli/
├── __init__.py          # Package exports
├── __main__.py          # python -m nv_cli entry point
├── cli.py               # Main Typer CLI app & subcommands
├── cli_ask.py           # One-shot query command
├── cli_chat.py          # Interactive chat session
├── agents/
│   ├── agent.py         # ReActAgent — core agent loop
│   ├── registry.py      # Agent registry & management
│   └── subagent.py      # Subagent orchestration
├── config/
│   ├── config.py        # Configuration dataclasses
│   ├── loader.py        # Config file loading & migration
│   └── validation.py    # Config validation
├── heartbeat/
│   ├── heartbeat.py     # Heartbeat task manager
│   └── scheduler.py     # Task scheduling
├── memory/
│   ├── memory.py        # MemoryManager — CRUD operations
│   ├── embedding.py     # Embedding providers
│   └── search.py        # Hybrid search (vector + BM25)
├── skills/
│   ├── skill.py         # Skill dataclass
│   ├── manager.py       # SkillManager — discovery & loading
│   ├── installer.py     # Multi-installer (pip, npm, brew, git)
│   └── security.py      # Security scanner
├── soul/
│   ├── soul.py          # SoulManager — identity loading
│   └── templates.py     # Default SOUL.md / IDENTITY.md templates
├── tools/
│   ├── registry.py      # Tool registry & dispatch
│   └── implementations.py # Built-in tools (read, write, bash, etc.)
└── utils/
    └── ...              # Shared utilities
```

Additionally, `nv.py` at the repo root contains the legacy v6 monolithic CLI (retained for reference).

### Key Design Decisions

- **OpenAI-compatible SDK** — Uses NVIDIA's OpenAI-compatible endpoint (`integrate.api.nvidia.com`), so any model available on NVIDIA's platform works out of the box.
- **ReAct Agent Loop** — The agent follows the Reason + Act pattern: it thinks, selects a tool, executes it, observes the result, and repeats.
- **File-based Identity** — Inspired by [OpenClaw](https://github.com/openclaw), agent personality is defined through markdown files rather than hardcoded prompts.
- **Modular Package** — Each subsystem (agents, memory, skills, heartbeat, soul, tools) is an independent module with clean interfaces.

---

## Configuration

Configuration is stored in `~/.nv-cli-config/`:

```
~/.nv-cli-config/
├── config.json          # API key and global settings
├── session.json         # Current session state
├── memory/              # Persistent memory storage
└── skills/              # Installed skills
```

```bash
nv config get            # Show current configuration
nv config edit           # Edit configuration interactively
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Code style and conventions
- Submitting pull requests
- Reporting issues

### Quick Contribution Guide

```bash
# Fork and clone
git clone https://github.com/<your-username>/Nvidia-CLI.git
cd Nvidia-CLI

# Set up dev environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Create a branch
git checkout -b feature/your-feature

# Make changes, then submit a PR
```

---

## Roadmap

- [ ] Plugin marketplace for community skills
- [ ] Multi-agent collaboration workflows
- [ ] Web UI dashboard
- [ ] Voice input/output support
- [ ] RAG pipeline integration
- [ ] Tool-use function calling with structured outputs

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [NVIDIA AI Foundation](https://build.nvidia.com/) for providing the AI model endpoints
- [OpenClaw](https://github.com/openclaw) for the soul/identity system inspiration
- [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/) for the terminal experience
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) for interactive input

---

<p align="center">
  Built with NVIDIA AI &bull; <a href="https://github.com/SingularityAI-Dev/Nvidia-CLI">GitHub</a> &bull; <a href="https://github.com/SingularityAI-Dev/Nvidia-CLI/issues">Issues</a>
</p>
