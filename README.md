# NVIDIA CLI v7.0

OpenClaw-inspired multi-agent AI framework for NVIDIA.

## Features

- **Multi-Agent System** - Run multiple AI agents with different configurations
- **Soul/Identity System** - File-based personality via SOUL.md, IDENTITY.md
- **Skills System** - Installable skills with security scanning
- **Hybrid Memory** - Vector + keyword search with embeddings
- **Subagent Orchestration** - Parallel task execution
- **Heartbeat System** - Periodic task checking

## Install

```bash
pip install -e .
```

## Usage

```bash
nv agent list          # List agents
nv agent create mybot  # Create new agent
nv chat               # Interactive chat
nv ask "hello"        # One-shot query
```

## License

MIT