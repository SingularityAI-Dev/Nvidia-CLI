# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **NVIDIA CLI v2.0** - a Python CLI tool for interacting with NVIDIA's AI models through their API. It's a single-file application (`nv.py`) that provides both one-shot queries and interactive chat sessions with context awareness.

## Development Commands

### Install/Update the CLI
```bash
pip install -e .        # Install in editable mode
pip install -e . --force-reinstall   # Force reinstall after major changes
```

### Run Without Installing
```bash
python nv.py chat       # Start chat mode
python nv.py ask "hi"   # One-shot query
```

### Linting and Type Checking
```bash
python -m py_compile nv.py              # Syntax check
python -m mypy nv.py --ignore-missing-imports  # Type check (if mypy installed)
```

### Clean Cache
```bash
rm -rf __pycache__ nv_cli.egg-info/*.pyc
```

## Architecture

### Single-File Structure
The application is intentionally monolithic in `nv.py` (~364 lines) with these sections:
- **Lines 1-34**: Imports and external dependencies
- **Lines 35-70**: Configuration constants (MODELS, SLASH_COMMANDS, MENU_STYLE)
- **Lines 75-106**: InteractiveMenu class using prompt_toolkit
- **Lines 109-147**: Visual output functions (logo, log_step)
- **Lines 150-250**: SessionContext class - the core state management
- **Lines 252-283**: Utility functions (bash extraction, command execution, streaming)
- **Lines 285-360**: Application commands (ask, chat) using Typer

### Key Components

**SessionContext** (lines 177-251)
- `file_context`: Dict of loaded file contents for prompt injection
- `project_tree`: Generated file listing from `/init` command
- `request_permission()`: Interactive prompt for shell command execution
- `generate_system_prompt()`: Injects file context into system prompts

**Model Configuration** (lines 41-49)
```python
MODELS = {
    "default": "deepseek-ai/deepseek-v3.2",
    "qwen3-coder": "deepseek-ai/deepseek-v3.2",
    "minimax": "deepseek-ai/deepseek-v3.2",
    "nano": "nvidia/nemotron-nano-12b-v2-vl",
    "deepseek": "deepseek-ai/deepseek-v3.2",
    "llama70": "nvidia/llama-3.1-nemotron-70b-instruct",
    "llama8": "meta/llama-3.1-8b-instruct",
}
```

**Interactive Chat Flow** (lines 297-361)
1. Initialize prompt_toolkit session with WordCompleter
2. Parse slash commands (`/init`, `/add`, `/clear`, `/model`, `/quit`, `/help`)
3. Inject context via `context_manager.generate_system_prompt()`
4. Stream response using OpenAI SDK with Rich Live display
5. Extract and prompt for bash command execution

### Dependencies
From `setup.py`:
- `typer` - CLI framework
- `rich` - Terminal styling and live display
- `openai` - API client (uses NVIDIA's OpenAI-compatible endpoint)
- `python-dotenv` - Environment loading
- `pathspec` - Gitignore pattern matching
- `prompt_toolkit` - Interactive input with autocomplete

## Authentication Priority

1. `NVIDIA_API_KEY` environment variable
2. `.env` file in current directory
3. `~/.nv-cli` global config file (auto-created on first run)
4. Interactive prompt (opens browser to build.nvidia.com)

## In-Chat Slash Commands

- `/init` - Analyze codebase, generate `.nv/NVIDIA.md` context
- `/add <file>` - Load specific file into conversation context
- `/clear` - Reset conversation and file context
- `/model <name>` - Switch AI model (stored in `~/.nv-cli-model`)
- `/help` - Show available commands
- `/quit` - Exit with session summary

## Context System

- `/init` respects `.gitignore` patterns using `pathspec`
- Always ignores: `.git`, `__pycache__`, `venv`, `node_modules`, `.nv`, `.venv`
- Context loaded automatically if `.nv/NVIDIA.md` exists
- Files added with `/add` are included in system prompts with token estimates

## Visual Design System

Brand color: **NVIDIA green (#76b900)**
- Logo ASCII art
- Command autocomplete selection highlighting
- Success messages and spinners
- Prompt Toolkit style dict: `MENU_STYLE`
