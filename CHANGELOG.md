# Changelog

All notable changes to the NVIDIA CLI project.

## [7.0.0] - 2026-03-09

### 🎉 Major Release - OpenClaw Integration

Complete refactor from single-file CLI to full agent framework.

### ✨ Features

#### Multi-Agent System
- **Agent Registry** - Manage multiple agents with `nv agent`
- **Agent Configurations** - Per-agent models, skills, memory settings
- **Subagent Orchestration** - Spawn parallel agents for complex tasks

#### Soul/Identity System (OpenClaw)
- **SOUL.md** - Core personality principles
- **IDENTITY.md** - Agent name, emoji, avatar
- **USER.md** - Human preferences and context
- **MEMORY.md** - Curated long-term memories
- **HEARTBEAT.md** - Periodic task definitions

#### Skills System
- **Auto-Discovery** - Scan directories for `SKILL.md` files
- **Security Scanner** - Detect dangerous patterns (eval, exec, etc.)
- **Multi-Installer** - Support pip, npm, brew, git

#### Memory System
- **Hybrid Search** - Combine vector + keyword (BM25)
- **SQLite Backend** - Persistent storage
- **Embedding Providers** - OpenAI, local (sentence-transformers)

#### Heartbeat System
- **Periodic Checks** - Task scheduling within agent context
- **Quiet Hours** - Respect user downtime
- **Batch Processing** - Group multiple checks

#### CLI Enhancements
- **Interactive Chat** - `nv chat` with prompt_toolkit
- **Slash Commands** - `/help`, `/add`, `/skill`, etc.
- **Subcommands:**
  - `nv agent list|create|delete`
  - `nv skill list|install|uninstall`
  - `nv memory add|search`
  - `nv heartbeat status`
  - `nv config get|edit`

### 🔧 Technical

#### Architecture
- Refactored from single-file (`nv.py`) to package (`nv_cli/`)
- Modular structure: config/, agents/, skills/, memory/, heartbeat/, soul/, tools/
- Modern packaging with pyproject.toml
- **OpenClaw Identity System** - ReActAgent now loads SOUL.md, IDENTITY.md, MEMORY.md, USER.md, HEARTBEAT.md, TOOLS.md, AGENTS.md into system prompt

#### Dependencies Added
- typer>=0.12.0
- rich>=13.0.0
- openai>=1.0.0
- prompt-toolkit>=3.0.0
- sentence-transformers>=2.0.0
- torch (via sentence-transformers)

### 🐛 Fixes
- Fixed slash command completer - only activates on `/`
- Fixed logo ASCII art spacing (user's original format)
- Updated wrapper script for internal SSD location
- Fixed `PermissionMode` export in config module
- Fixed asyncio conflict with prompt_toolkit by using `prompt_async()`

---

## [6.0.0] - 2026-03-07

### Original Monolithic Version
- Single-file CLI (`nv.py`)
- Basic ReAct agent
- File context with `/add`, `/init`
- Permission modes (ask/accept_edits/auto)
- Model switching (`/model`)

---

### 🔧 Repository Recovery (2026-03-09)
- **Repository Migration**: Moved from cadpal repo to dedicated https://github.com/SingularityAI-Dev/Nvidia-CLI
- **Module Fix**: Restored missing `memory/` module that was lost during extraction
- **Installation**: Verified `pip install -e .` works correctly
- **Functionality**: Confirmed `nv --help` and `nv agent list` work as expected

---

*Format based on [Keep a Changelog](https://keepachangelog.com/)*