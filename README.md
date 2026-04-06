<p align="center">
  <img src="https://img.shields.io/badge/NVIDIA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Version-7.0.0-blue?style=for-the-badge" alt="Version 7.0.0">
  <img src="https://img.shields.io/badge/API-Free%20Tier-brightgreen?style=for-the-badge" alt="Free API Tier">
</p>

<h1 align="center">NVIDIA CLI</h1>

<p align="center">
  <strong>A Claude Code-style agentic coding assistant for your terminal — powered by NVIDIA's free AI endpoints.</strong>
</p>

<p align="center">
  No paid API keys. No subscriptions. Just run <code>nv chat</code>.
</p>

<br>

<p align="center">
  <img src="gifs/init_chat_demo.svg" alt="NVIDIA CLI demo — nv chat with /init" width="800">
</p>

<br>

<p align="center">
  <a href="#-why-nvidia-cli">Why NVIDIA CLI?</a> &bull;
  <a href="#-features">Features</a> &bull;
  <a href="#-quick-start">Quick Start</a> &bull;
  <a href="#-usage">Usage</a> &bull;
  <a href="#-architecture">Architecture</a> &bull;
  <a href="#-roadmap">Roadmap</a> &bull;
  <a href="#-contributing">Contributing</a>
</p>

---

## 💡 Why NVIDIA CLI?

Tools like Claude Code and Aider are powerful — but they require paid API subscriptions that add up fast.

**NVIDIA CLI gives you the same agentic coding experience using NVIDIA's free-tier AI endpoints.** If you have an NVIDIA developer account, you can run a full multi-agent coding assistant with persistent memory, installable skills, and file-based identity — completely free.

| | NVIDIA CLI | Claude Code | Aider |
|---|---|---|---|
| **API Cost** | ✅ Free tier available | 💰 Paid (Anthropic API) | 💰 Paid (OpenAI/Anthropic) |
| **Runs in terminal** | ✅ | ✅ | ✅ |
| **Persistent memory** | ✅ Hybrid vector + BM25 | ❌ | ❌ |
| **Installable skills** | ✅ With security scanning | ❌ | ❌ |
| **Agent identity/soul** | ✅ File-based | ❌ | ❌ |
| **Multi-agent support** | ✅ | ❌ | ❌ |
| **Self-hostable** | ✅ | ❌ | ✅ |

---

## ✨ Features

### 🤖 Multi-Agent System

Create and manage multiple AI agents, each with their own configuration, model preferences, and behaviour. Spawn subagents for parallel task execution.

<p align="center"><img src="gifs/agents_gif_demo.svg" alt="Multi-Agent System Demo" width="750"></p>

```bash
nv agent list              # List all agents
nv agent create mybot      # Create a new agent
nv agent delete mybot      # Remove an agent
```

---

### 👤 Soul / Identity System

Give your agents a persistent personality through file-based identity documents. The **Soul** acts as active middleware, injecting personality and context into every interaction — inspired by [OpenClaw](https://github.com/openclaw).

<p align="center"><img src="gifs/soul_identity_demo.svg" alt="Soul Identity Demo" width="750"></p>

| File | Purpose |
|------|---------|
| `SOUL.md` | Core personality principles and values |
| `IDENTITY.md` | Agent name, emoji, and avatar |
| `USER.md` | Human preferences and working style |
| `MEMORY.md` | Curated long-term memories |
| `HEARTBEAT.md` | Periodic background task definitions |

---

### 🛡️ Skills System with Security Scanning

Discover, install, and manage agent skills from any source. Every skill is automatically scanned for dangerous patterns before installation — safe to run inside automated agentic loops.

<p align="center"><img src="gifs/skills_security_demo.svg" alt="Skills Security Demo" width="750"></p>

```bash
nv skill list              # List installed skills
nv skill install <path>    # Install a skill (pip, npm, brew, or git)
nv skill uninstall <name>  # Remove a skill
```

> Skills are auto-discovered via `SKILL.md` files and scanned for `eval`, `exec`, and subprocess abuse before execution.

---

### 🧠 Hybrid Memory (Vector + BM25)

Persistent memory that actually finds what you need — combining semantic vector search with traditional keyword matching for best-of-both-worlds recall.

```bash
nv memory add "Project uses FastAPI with PostgreSQL"
nv memory search "database setup"
```

- **SQLite-backed** — no external database required
- **Embedding providers:** OpenAI or fully local via `sentence-transformers`
- **Automatic context injection** — relevant memories surface in every conversation

---

### 💓 Heartbeat System

Schedule periodic background tasks that run inside your agent's context — ideal for maintenance checks, data syncing, or regular reminders.

<p align="center"><img src="gifs/heartbeat_demo.svg" alt="Heartbeat Demo" width="750"></p>

```bash
nv heartbeat status        # Check all heartbeat task statuses
```

- Quiet hours support — won't interrupt you at 2am
- Batch processing for grouped checks

---

### 🔀 Permission Modes

Fine-grained control over how the agent interacts with your filesystem:

| Mode | Behaviour |
|------|-----------|
| `ask` | Always confirm before any action *(default, safest)* |
| `accept_edits` | Auto-accept file edits, confirm everything else |
| `auto` | Auto-approve safe operations |
| `never` | Full dry-run — no actions executed |

---

### 🧩 Available Models

All models run on NVIDIA's API. Free-tier access available at [build.nvidia.com](https://build.nvidia.com/explore).

| Alias | Model |
|-------|-------|
| `default` | `deepseek-ai/deepseek-v3.2` |
| `nano` | `nvidia/nemotron-nano-12b-v2-vl` |
| `llama70` | `nvidia/llama-3.1-nemotron-70b-instruct` |
| `llama8` | `meta/llama-3.1-8b-instruct` |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- A **free** NVIDIA API key from [build.nvidia.com](https://build.nvidia.com/explore)

### Installation

```bash
# Clone the repository
git clone https://github.com/SingularityAI-Dev/Nvidia-CLI.git
cd Nvidia-CLI

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e .
```

### Set Up Your API Key

```bash
# Option 1: Environment variable (recommended)
export NVIDIA_API_KEY="nvapi-your-key-here"

# Option 2: .env file
echo 'NVIDIA_API_KEY=nvapi-your-key-here' > .env

# Option 3: Just run nv chat — it will prompt you on first launch
nv chat
```

Your key is stored in `~/.nv-cli-config/config.json` after first setup. You're good to go.

---

## 📖 Usage

### Start a chat session

```bash
nv chat
```

On first run in a project, use `/init` to have the agent analyse your codebase and build a context map:

```
nv> /init
[*] Analysing codebase...
[*] Context saved to .nv/NVIDIA.md

nv> How is authentication handled in this project?
```

### One-shot queries

```bash
nv ask "What is the difference between CUDA and OpenCL?"
```

### In-chat slash commands

| Command | Description |
|---------|-------------|
| `/init` | Analyse codebase and generate a context file |
| `/add <file>` | Load a file into the current conversation |
| `/clear` | Reset conversation and file context |
| `/model <name>` | Switch AI model mid-session |
| `/skill` | Manage skills from within chat |
| `/help` | Show all available commands |
| `/quit` | Exit with a session summary |

### Agent management

```bash
nv agent create researcher   # Create a specialist agent
nv agent list                # See all your agents
nv config edit               # Edit agent configuration
```

---

## 🏗️ Architecture

<p align="center">
  <img src="gifs/nvidia-cli-architecture.svg" alt="NVIDIA CLI Architecture Diagram" width="800">
</p>

```
nv_cli/
├── agents/          # ReActAgent loop & subagent orchestration
├── config/          # Configuration dataclasses & validation
├── heartbeat/       # Background task manager & scheduler
├── memory/          # Hybrid search (vector embeddings + BM25)
├── skills/          # Multi-installer (pip/npm/brew/git) & security scanner
├── soul/            # File-based identity loading (OpenClaw-style)
├── tools/           # Built-in tool registry & implementations
└── utils/           # Shared utilities
```

**Key design decisions:**

- **OpenAI-compatible SDK** — Uses NVIDIA's OpenAI-compatible endpoint, so any model on the NVIDIA platform works out of the box
- **ReAct Agent Loop** — Think → select tool → execute → observe → repeat
- **File-based Identity** — Agent personality defined in markdown, not hardcoded prompts
- **Modular architecture** — Each subsystem is fully independent with clean interfaces

---

## 🗺️ Roadmap

- [ ] Plugin marketplace for community skills
- [ ] Multi-agent collaboration workflows
- [ ] Web UI dashboard
- [ ] Voice input/output support
- [ ] RAG pipeline integration
- [ ] Structured outputs with function calling

Have a feature request? [Open an issue](https://github.com/SingularityAI-Dev/Nvidia-CLI/issues) — contributions are very welcome.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

**Quick start for contributors:**

```bash
# Fork and clone
git clone https://github.com/<your-username>/Nvidia-CLI.git
cd Nvidia-CLI

# Set up dev environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Create a branch and submit a PR
git checkout -b feature/your-feature
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [NVIDIA AI Foundation](https://build.nvidia.com/) for the free AI model endpoints
- [OpenClaw](https://github.com/openclaw) for the soul/identity system inspiration
- [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/) for the terminal experience
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) for interactive input

---

<p align="center">
  If this project saved you money on API bills, consider giving it a ⭐ — it helps more than you'd think.
</p>

<p align="center">
  Built with ❤️ using NVIDIA AI &bull;
  <a href="https://github.com/SingularityAI-Dev/Nvidia-CLI">GitHub</a> &bull;
  <a href="https://github.com/SingularityAI-Dev/Nvidia-CLI/issues">Issues</a>
</p>
