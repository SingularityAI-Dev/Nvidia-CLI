"""Agent system for nv_cli.

Multi-agent support with subagent orchestration.
"""

from .agent import Agent, ReActAgent
from .registry import AgentRegistry
from .subagent import SubagentRegistry, SubagentRunRecord

__all__ = [
    "Agent",
    "ReActAgent",
    "AgentRegistry",
    "SubagentRegistry",
    "SubagentRunRecord",
]