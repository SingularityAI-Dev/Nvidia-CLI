"""Skill data models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path


@dataclass
class ToolDefinition:
    """Definition of a tool provided by a skill."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstallSpec:
    """Installation specification for a skill."""
    type: str = ""  # pip, npm, brew, download, etc
    package: str = ""
    url: Optional[str] = None


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    install: List[InstallSpec] = field(default_factory=list)
    tools: List[ToolDefinition] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)


@dataclass
class Skill:
    """A skill with its metadata and implementation."""
    metadata: SkillMetadata
    path: Path
    _tools: Dict[str, Callable] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if self._tools is None:
            self._tools = {}

    def register_tool(self, name: str, func: Callable):
        """Register a tool implementation."""
        self._tools[name] = func

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self._tools.get(name)