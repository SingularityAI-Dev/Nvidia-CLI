"""Skill manager for loading and managing skills."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .skill import Skill, SkillMetadata, ToolDefinition, InstallSpec


class SkillManager:
    """Manages loaded skills."""

    def __init__(self, skills_dir: Optional[Path] = None):
        if skills_dir is None:
            skills_dir = Path.home() / ".nv-cli-config" / "skills"
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills: Dict[str, Skill] = {}
        self._load_builtin_skills()

    def _load_builtin_skills(self):
        """Load built-in skills."""
        # Will be populated as skills are discovered
        pass

    def discover_skills(self, search_path: Optional[Path] = None) -> List[SkillMetadata]:
        """Discover skills by scanning for SKILL.md files."""
        search_path = search_path or self.skills_dir
        discovered = []

        for root, dirs, files in search_path.walk():
            if "SKILL.md" in files:
                skill_md = root / "SKILL.md"
                try:
                    metadata = self._parse_skill_md(skill_md)
                    discovered.append(metadata)
                except Exception as e:
                    print(f"Error parsing {skill_md}: {e}")

        return discovered

    def _parse_skill_md(self, path: Path) -> SkillMetadata:
        """Parse a SKILL.md file."""
        content = path.read_text()

        # Simple YAML-like parsing
        data = {"id": path.parent.name, "name": "", "description": "", "tools": []}

        # Parse frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        data[key.strip()] = value.strip().strip('"')

        # Parse tools section
        tools_section = re.search(r'## Tools\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if tools_section:
            tools_text = tools_section.group(1)
            for match in re.finditer(r'- \*\*(.*?)\*\*', tools_text):
                data["tools"].append({"name": match.group(1), "description": ""})

        return SkillMetadata(
            id=data.get("id", path.parent.name),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tools=[ToolDefinition(**t) for t in data.get("tools", [])]
        )

    def load_skill(self, skill_path: Path) -> Optional[Skill]:
        """Load a skill from path."""
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return None

        metadata = self._parse_skill_md(skill_md)
        skill = Skill(metadata=metadata, path=skill_path)
        self._skills[metadata.id] = skill
        return skill

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a loaded skill."""
        return self._skills.get(skill_id)

    def get_active_skills(self, allowlist: List[str] = None) -> List[Skill]:
        """Get skills that should be active."""
        if not allowlist:
            return list(self._skills.values())
        return [s for s in self._skills.values() if s.metadata.id in allowlist]

    def list_skills(self) -> List[SkillMetadata]:
        """List all loaded skill metadata."""
        return [s.metadata for s in self._skills.values()]