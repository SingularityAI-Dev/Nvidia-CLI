"""Soul and Identity management for agents."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List
import yaml
from .templates import DEFAULT_SOUL, DEFAULT_IDENTITY, DEFAULT_USER, DEFAULT_MEMORY, DEFAULT_HEARTBEAT, DEFAULT_TOOLS, DEFAULT_AGENTS, DEFAULT_BOOTSTRAP

@dataclass
class Identity:
    """Agent identity loaded from IDENTITY.md."""
    name: str = "NVIDIA Assistant"
    creature: str = "AI coding assistant"
    vibe: str = "Helpful, direct, efficient"
    emoji: str = ""
    avatar: str = ""

@dataclass
class UserProfile:
    """User profile loaded from USER.md."""
    name: str = ""
    pronouns: str = ""
    timezone: str = ""
    preferences: str = ""
    context: str = ""

@dataclass
class Soul:
    """Complete soul state loaded from all files."""
    identity: Identity = field(default_factory=Identity)
    user: UserProfile = field(default_factory=UserProfile)
    soul_text: str = ""
    memory_text: str = ""
    heartbeat_text: str = ""
    tools_text: str = ""
    agents_text: str = ""

class SoulManager:
    """Manages soul/identity files for an agent."""

    FILES = {
        "soul": "SOUL.md",
        "identity": "IDENTITY.md",
        "user": "USER.md",
        "memory": "MEMORY.md",
        "heartbeat": "HEARTBEAT.md",
        "tools": "TOOLS.md",
        "agents": "AGENTS.md",
        "bootstrap": "BOOTSTRAP.md",
    }

    def __init__(self, workspace_dir: Path):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.memory_dir = self.workspace / "memory"
        self.memory_dir.mkdir(exist_ok=True)

    def ensure_files(self):
        """Create default files if they don't exist."""
        defaults = {
            "SOUL.md": DEFAULT_SOUL,
            "IDENTITY.md": DEFAULT_IDENTITY,
            "USER.md": DEFAULT_USER,
            "MEMORY.md": DEFAULT_MEMORY,
            "HEARTBEAT.md": DEFAULT_HEARTBEAT,
            "TOOLS.md": DEFAULT_TOOLS,
            "AGENTS.md": DEFAULT_AGENTS,
            "BOOTSTRAP.md": DEFAULT_BOOTSTRAP,
        }
        for filename, content in defaults.items():
            filepath = self.workspace / filename
            if not filepath.exists():
                filepath.write_text(content)

    def load_soul(self) -> Soul:
        """Load complete soul state from files."""
        self.ensure_files()

        identity = self._load_identity()
        user = self._load_user()

        return Soul(
            identity=identity,
            user=user,
            soul_text=self._read_file("SOUL.md"),
            memory_text=self._read_file("MEMORY.md"),
            heartbeat_text=self._read_file("HEARTBEAT.md"),
            tools_text=self._read_file("TOOLS.md"),
            agents_text=self._read_file("AGENTS.md"),
        )

    def _load_identity(self) -> Identity:
        """Load identity from IDENTITY.md."""
        content = self._read_file("IDENTITY.md")
        data = self._parse_frontmatter(content)
        return Identity(
            name=data.get("name", "NVIDIA Assistant"),
            creature=data.get("creature", "AI coding assistant"),
            vibe=data.get("vibe", "Helpful, direct, efficient"),
            emoji=data.get("emoji", ""),
            avatar=data.get("avatar", ""),
        )

    def _load_user(self) -> UserProfile:
        """Load user profile from USER.md."""
        content = self._read_file("USER.md")
        data = self._parse_frontmatter(content)
        return UserProfile(
            name=data.get("name", ""),
            pronouns=data.get("pronouns", ""),
            timezone=data.get("timezone", ""),
            preferences=data.get("preferences", ""),
            context=data.get("context", ""),
        )

    def _read_file(self, filename: str) -> str:
        """Read a file from workspace."""
        filepath = self.workspace / filename
        if filepath.exists():
            return filepath.read_text()
        return ""

    def _parse_frontmatter(self, content: str) -> Dict:
        """Parse simple key: value from content."""
        data = {}
        for line in content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip("# ")
                value = value.strip().strip('"')
                if value:
                    data[key.lower()] = value
        return data

    def update_memory(self, new_memory: str):
        """Append to MEMORY.md."""
        filepath = self.workspace / "MEMORY.md"
        current = filepath.read_text() if filepath.exists() else ""
        updated = current + f"\n- {new_memory}"
        filepath.write_text(updated)

    def log_session(self, date: str, content: str):
        """Log session to daily memory file."""
        filepath = self.memory_dir / f"{date}.md"
        if filepath.exists():
            current = filepath.read_text()
        else:
            current = f"# Session Log - {date}\n\n"
        updated = current + f"\n{content}"
        filepath.write_text(updated)

    def get_system_prompt_additions(self) -> str:
        """Get text to add to system prompt."""
        soul = self.load_soul()
        parts = []

        if soul.identity.name:
            parts.append(f"Name: {soul.identity.name}")
        if soul.identity.creature:
            parts.append(f"You are a {soul.identity.creature}")
        if soul.soul_text:
            parts.append(f"\n### SOUL ###\n{soul.soul_text[:2000]}")
        if soul.memory_text:
            parts.append(f"\n### MEMORY ###\n{soul.memory_text[:1000]}")
        if soul.user.name:
            parts.append(f"\n### USER ###\nName: {soul.user.name}")

        return "\n".join(parts)