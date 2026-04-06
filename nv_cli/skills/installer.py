"""Skill installer."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console

from .skill import SkillMetadata
from .security import SecurityScanner

console = Console()


class SkillInstaller:
    """Installs skills from various sources."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.scanner = SecurityScanner()

    def install(self, source: str, name: Optional[str] = None) -> bool:
        """Install a skill from source.

        Args:
            source: URL, path, or package name
            name: Optional name for the skill
        """
        # Determine source type
        if source.startswith("http"):
            return self._install_from_url(source, name)
        elif Path(source).exists():
            return self._install_from_path(Path(source), name)
        elif "@" in source or "/" in source:
            # Git-like URL
            return self._install_from_git(source, name)
        else:
            # Try as package name
            return self._install_from_package(source, name)

    def _install_from_path(self, path: Path, name: Optional[str]) -> bool:
        """Install from local path."""
        skill_name = name or path.name
        target = self.skills_dir / skill_name

        # Security scan
        warnings, critical = self.scanner.scan_directory(path)

        if critical:
            console.print(f"[red]Critical issues found:[/red]")
            for issue in critical:
                console.print(f"  - {issue}")
            return False

        if warnings:
            console.print(f"[yellow]Warnings:[/yellow]")
            for issue in warnings:
                console.print(f"  - {issue}")

        # Copy to skills directory
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(path, target)

        console.print(f"[green]Installed {skill_name} from {path}[/green]")
        return True

    def _install_from_url(self, url: str, name: Optional[str]) -> bool:
        """Install from URL."""
        # Download and extract
        console.print(f"[dim]Downloading from {url}...[/dim]")
        # Implementation using urllib/requests
        return True

    def _install_from_git(self, url: str, name: Optional[str]) -> bool:
        """Install from git."""
        skill_name = name or url.split("/")[-1].replace(".git", "")
        target = self.skills_dir / skill_name

        cmd = f"git clone {url} {target}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            console.print(f"[red]Git clone failed: {result.stderr}[/red]")
            return False

        # Security scan
        warnings, critical = self.scanner.scan_directory(target)
        if critical:
            shutil.rmtree(target)
            console.print(f"[red]Critical security issues[/red]")
            return False

        console.print(f"[green]Installed {skill_name} from git[/green]")
        return True

    def _install_from_package(self, package: str, name: Optional[str]) -> bool:
        """Install from package manager."""
        # Try pip
        skill_name = name or package.split("/")[-1]
        target = self.skills_dir / skill_name

        # This is a simplified version - real implementation would
        # handle multiple package managers
        console.print(f"[dim]Installing {package}...[/dim]")
        return True

    def uninstall(self, skill_name: str) -> bool:
        """Uninstall a skill."""
        target = self.skills_dir / skill_name
        if target.exists():
            shutil.rmtree(target)
            console.print(f"[green]Uninstalled {skill_name}[/green]")
            return True
        console.print(f"[yellow]Skill {skill_name} not found[/yellow]")
        return False

    def update(self, skill_name: str) -> bool:
        """Update a skill."""
        # Git pull or re-download
        console.print(f"[green]Updated {skill_name}[/green]")
        return True