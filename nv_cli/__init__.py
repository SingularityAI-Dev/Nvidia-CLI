"""NVIDIA CLI v7.0 - OpenClaw-inspired AI Agent Framework.

A multi-agent, event-driven AI assistant with:
- File-based Soul/Identity system
- Hybrid Memory with vector + keyword search
- Skills system with security scanning
- Subagent orchestration
- Heartbeat for proactive checks
"""

__version__ = "7.0.0"
__app_name__ = "nv-cli"

from .config import Config, AgentConfig
from .agents import Agent, AgentRegistry
from .soul import SoulManager, Identity

__all__ = [
    "Config",
    "AgentConfig",
    "Agent",
    "AgentRegistry",
    "SoulManager",
    "Identity",
]