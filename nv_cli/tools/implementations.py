"""Core tool implementations."""

import os
import subprocess
import textwrap
import fnmatch
import re
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def read_file(path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> str:
    """Read a file."""
    try:
        filepath = Path(path).expanduser().resolve()
        if not filepath.exists():
            return f"Error: File not found: {path}"

        content = filepath.read_text(encoding='utf-8', errors='replace')

        if offset and limit:
            lines = content.splitlines()
            content = "\n".join(lines[offset-1:offset-1+limit])
        elif offset:
            lines = content.splitlines()
            content = "\n".join(lines[offset-1:])
        elif limit:
            lines = content.splitlines()
            content = "\n".join(lines[:limit])

        return content
    except Exception as e:
        return f"Error reading {path}: {e}"


def write_file(path: str, content: str, force: bool = False) -> str:
    """Write a file."""
    try:
        filepath = Path(path).expanduser()
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if filepath.exists() and not force:
            return f"Error: File exists. Use edit_file to modify."

        filepath.write_text(content, encoding='utf-8')
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit a file."""
    try:
        filepath = Path(path).expanduser().resolve()
        if not filepath.exists():
            return f"Error: File not found: {path}"

        content = filepath.read_text(encoding='utf-8')

        if old_string not in content:
            return f"Error: String not found in {path}"

        content = content.replace(old_string, new_string, 1)
        filepath.write_text(content, encoding='utf-8')

        return f"Edited {path}"
    except Exception as e:
        return f"Error editing {path}: {e}"


def execute_command(command: str, timeout: int = 120) -> str:
    """Execute a shell command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr] {result.stderr}"
        return output[:2000]  # Truncate long outputs
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Error executing command: {e}"


def glob_search(pattern: str, root: str = ".") -> str:
    """Search files by pattern."""
    try:
        rootpath = Path(root).expanduser().resolve()
        matches = []
        for path in rootpath.rglob("*"):
            if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(str(path), pattern):
                matches.append(str(path.relative_to(rootpath)))
        return "\n".join(sorted(matches)[:100]) or "No matches found"
    except Exception as e:
        return f"Error searching: {e}"


def grep_search(pattern: str, path: Optional[str] = None) -> str:
    """Search file contents."""
    try:
        if path:
            dirpath = Path(path).expanduser().resolve()
        else:
            dirpath = Path(".").resolve()

        matches = []
        for root, dirs, files in os.walk(dirpath):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in files:
                if filename.startswith('.'):
                    continue

                filepath = Path(root) / filename
                try:
                    content = filepath.read_text(encoding='utf-8', errors='replace')
                    if re.search(pattern, content, re.IGNORECASE):
                        lines = [
                            f"{filepath.relative_to(dirpath)}:{i+1}: {line[:80]}"
                            for i, line in enumerate(content.splitlines())
                            if re.search(pattern, line, re.IGNORECASE)
                        ][:5]
                        matches.extend(lines)
                except Exception:
                    continue

        return "\n".join(matches[:50]) or "No matches found"
    except Exception as e:
        return f"Error searching: {e}"


def list_directory(path: str = ".") -> str:
    """List directory contents."""
    try:
        dirpath = Path(path).expanduser().resolve()
        if not dirpath.exists():
            return f"Error: Directory not found: {path}"

        entries = []
        for entry in sorted(dirpath.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            prefix = "📁" if entry.is_dir() else "📄"
            entries.append(f"{prefix} {entry.name}")

        return "\n".join(entries[:100]) or "Empty directory"
    except Exception as e:
        return f"Error listing {path}: {e}"


def web_search(query: str) -> str:
    """Search the web."""
    import urllib.request
    import urllib.parse
    import json

    try:
        # Using DuckDuckGo's API or a simple web search
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        return f"Search query prepared: {query}\n(Web search requires API integration)"
    except Exception as e:
        return f"Web search: {query} (no results)"


def web_fetch(url: str) -> str:
    """Fetch content from URL."""
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='replace')
            # Extract text content roughly
            text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:3000]
    except Exception as e:
        return f"Error fetching {url}: {e}"


def ask_user(question: str) -> str:
    """Ask the user for input."""
    return Prompt.ask(question)


def spawn_subagent(task: str, agent_id: str = "default", **kwargs) -> str:
    """Spawn a subagent for parallel work."""
    # This will be implemented with actual subagent spawning
    return f"Spawned subagent ({agent_id}) for task: {task}"