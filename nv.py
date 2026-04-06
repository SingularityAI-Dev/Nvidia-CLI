#!/usr/bin/env python3
"""
NVIDIA CLI v6.0 - Claude Code-inspired AI Agent
A powerful coding assistant with skills, tools, hooks, and permissions.
"""

import os
import sys
import time
import json
import re
import subprocess
import shlex
import uuid
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.syntax import Syntax
from rich.tree import Tree
from rich.prompt import Prompt, Confirm
from openai import OpenAI
from dotenv import load_dotenv
import pathspec

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, FuzzyWordCompleter

# --- Configuration ---
APP_NAME = "nv"
VERSION = "6.0.0"
CONFIG_DIR = Path.home() / ".nv-cli-config"
CONFIG_FILE = CONFIG_DIR / "config.json"
MEMORY_DIR = CONFIG_DIR / "memory"
SKILLS_DIR = CONFIG_DIR / "skills"
SESSION_FILE = CONFIG_DIR / "session.json"
MODEL_CONFIG_FILE = Path.home() / ".nv-cli-model"
OLD_CONFIG_FILE = Path.home() / ".nv-cli"

# Migrate old config if needed
if OLD_CONFIG_FILE.exists() and OLD_CONFIG_FILE.is_file():
    old_key = OLD_CONFIG_FILE.read_text().strip()
    if old_key.startswith("nvapi-"):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = {"api_key": old_key}
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
        OLD_CONFIG_FILE.unlink()

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)
SKILLS_DIR.mkdir(exist_ok=True)

# --- Permission Modes ---
class PermissionMode(Enum):
    ASK = "ask"           # Always ask for permission (default)
    ACCEPT_EDITS = "accept_edits"  # Auto-accept file edits, ask for other actions
    AUTO = "auto"         # Auto-approve safe operations
    NEVER = "never"       # Never allow (dry-run mode)

# --- Tool Definitions ---
TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path to the file"},
                    "offset": {"type": "integer", "description": "Line number to start reading from"},
                    "limit": {"type": "integer", "description": "Number of lines to read"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path"},
                    "content": {"type": "string", "description": "Content to write"},
                    "append": {"type": "boolean", "description": "Append instead of overwrite"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a specific section of a file using search/replace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "old_string": {"type": "string", "description": "Text to find"},
                    "new_string": {"type": "string", "description": "Replacement text"}
                },
                "required": ["path", "old_string", "new_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds"},
                    "background": {"type": "boolean", "description": "Run in background"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "glob_search",
            "description": "Find files matching a glob pattern",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern like *.py or src/**/*.ts"},
                    "path": {"type": "string", "description": "Directory to search in"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Search for text patterns in file contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search for"},
                    "path": {"type": "string", "description": "Directory or file to search"},
                    "include": {"type": "string", "description": "File glob pattern to include"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List contents of a directory with file details",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                    "recursive": {"type": "boolean", "description": "List recursively"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results (1-10)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and parse content from a web page",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git",
            "description": "Run git commands",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Git subcommand (status, log, diff, etc.)"},
                    "args": {"type": "string", "description": "Additional arguments"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Ask the user a clarifying question with multiple choice",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to ask"},
                    "options": {"type": "array", "items": {"type": "string"}, "description": "Multiple choice options"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task",
            "description": "Spawn a subagent to complete a specific task",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Task description"},
                    "prompt": {"type": "string", "description": "Detailed instructions for the subagent"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Files to provide to the subagent"}
                },
                "required": ["description", "prompt"]
            }
        }
    }
]

tool_implementations: Dict[str, Callable] = {}

def tool(func: Callable) -> Callable:
    """Decorator to register a tool implementation."""
    tool_implementations[func.__name__] = func
    return func

@tool
def read_file(path: str, offset: int = 1, limit: int = 200) -> str:
    """Read file contents with line numbers."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return f"Error: File '{path}' not found"
    if not file_path.is_file():
        return f"Error: '{path}' is not a file"
    try:
        lines = file_path.read_text(encoding='utf-8', errors='replace').split('\n')
        start = max(0, offset - 1)
        end = min(len(lines), start + limit)
        selected = lines[start:end]
        result = f"File: {file_path} ({len(lines)} lines total)\n\n"
        result += '\n'.join([f"{i+start+1:4d}| {line}" for i, line in enumerate(selected)])
        return result
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def write_file(path: str, content: str, append: bool = False) -> str:
    """Write content to a file."""
    file_path = Path(path).expanduser()
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if append:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return f"Appended to {file_path}"
        else:
            file_path.write_text(content, encoding='utf-8')
            return f"Wrote {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"

@tool
def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit a specific section of a file."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return f"Error: File '{path}' not found"
    try:
        content = file_path.read_text(encoding='utf-8')
        if old_string not in content:
            # Try with normalized whitespace
            normalized_old = re.sub(r'\s+', ' ', old_string).strip()
            normalized_content = re.sub(r'\s+', ' ', content).strip()
            if normalized_old in normalized_content:
                return f"Error: The old_string exists but with different whitespace. Please match exactly."
            return f"Error: Could not find the text to replace in {path}"
        new_content = content.replace(old_string, new_string, 1)
        file_path.write_text(new_content, encoding='utf-8')
        lines_changed = new_content.count('\n') - content.count('\n') + 1
        return f"Edited {path} (replaced 1 occurrence)"
    except Exception as e:
        return f"Error editing file: {e}"

@tool
def execute_command(command: str, timeout: int = 60, background: bool = False) -> str:
    """Execute a shell command."""
    if background:
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Started in background: {command}"
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=timeout)
        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(f"[stderr] {result.stderr}")
        if result.returncode != 0:
            output.append(f"[exit code {result.returncode}]")
        return '\n'.join(output) if output else "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"

@tool
def glob_search(pattern: str, path: str = ".") -> str:
    """Find files matching a glob pattern."""
    try:
        search_path = Path(path).expanduser()
        results = []
        for p in search_path.rglob(pattern):
            if p.is_file():
                results.append(str(p.relative_to(search_path)))
        count = len(results)
        return f"Found {count} files:\n" + '\n'.join(results[:100]) if results else "No files found"
    except Exception as e:
        return f"Error: {e}"

@tool
def grep_search(pattern: str, path: str = ".", include: str = "*") -> str:
    """Search for text patterns in files."""
    results = []
    try:
        search_path = Path(path).expanduser()
        files_checked = 0
        for p in search_path.rglob(include):
            if p.is_file():
                files_checked += 1
                try:
                    content = p.read_text(encoding='utf-8', errors='ignore')
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    if matches:
                        results.append(f"\n{p}:")
                        for m in matches[:3]:
                            line_num = content[:m.start()].count('\n') + 1
                            context = content[max(0, m.start()-50):m.end()+50]
                            results.append(f"  Line {line_num}: ...{context}...")
                except:
                    pass
        return f"Searched {files_checked} files.\n" + '\n'.join(results[:50]) if results else f"No matches found (checked {files_checked} files)"
    except Exception as e:
        return f"Error: {e}"

@tool
def list_directory(path: str = ".", recursive: bool = False) -> str:
    """List directory contents."""
    try:
        dir_path = Path(path).expanduser()
        if not dir_path.exists():
            return f"Error: Path '{path}' not found"

        if recursive:
            tree = Tree(f"[bold]{dir_path}/[/bold]")
            def add_dir(t, current, depth=0):
                if depth > 3:
                    return
                for item in sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                    if item.name.startswith('.') and item.name not in ['.gitignore', '.env']:
                        continue
                    if item.is_dir():
                        if item.name not in ['__pycache__', 'node_modules', '.venv', 'venv']:
                            add_dir(t.add(f"[blue]{item.name}/[/blue]"), item, depth+1)
                    else:
                        t.add(item.name)
            add_dir(tree, dir_path)
            return str(tree)
        else:
            items = []
            for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                if item.is_dir():
                    items.append(f"[blue]{item.name}/[/blue]")
                else:
                    items.append(item.name)
            return '\n'.join(items) if items else "(empty)"
    except Exception as e:
        return f"Error: {e}"

@tool
def web_search(query: str, num_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    try:
        # Use duckduckgo-search if available
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=min(num_results, 10))
                output = [f"Web search results for: {query}\n"]
                for i, r in enumerate(results, 1):
                    output.append(f"{i}. {r['title']}\n   {r['href']}\n   {r['body'][:200]}...")
                return '\n'.join(output)
        except ImportError:
            return f"Web search requires: pip install duckduckgo-search\nQuery: {query}"
    except Exception as e:
        return f"Web search error: {e}"

@tool
def web_fetch(url: str) -> str:
    """Fetch content from a web page."""
    try:
        import urllib.request
        import urllib.error
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='replace')
            # Extract text from HTML (basic)
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            return f"Fetched from {url}:\n\n{text[:5000]}"
    except Exception as e:
        return f"Error fetching {url}: {e}"

@tool
def git(command: str, args: str = "") -> str:
    """Run git commands."""
    full_cmd = f"git {command} {args}".strip()
    return execute_command(full_cmd)

@tool
def ask_user(question: str, options: List[str] = None) -> str:
    """Ask the user a question."""
    console = Console()
    console.print(f"\n[bold yellow]? {question}[/bold yellow]")
    if options:
        for i, opt in enumerate(options, 1):
            console.print(f"  {i}. {opt}")
        choice = Prompt.ask("Select", choices=[str(i) for i in range(1, len(options)+1)])
        return f"{options[int(choice)-1]}"
    else:
        return Prompt.ask("Your answer")

@tool
def task(description: str, prompt: str, files: List[str] = None) -> str:
    """Spawn a subagent for a task."""
    console = Console()
    console.print(f"[dim]Subagent task: {description}[/dim]")
    # For now, return a summary
    return f"Subagent would complete: {description}\nWith prompt: {prompt[:100]}..."

# --- Skills System ---
@dataclass
class Skill:
    name: str
    description: str
    pattern: str
    prompt_addition: str
    triggers: List[str] = None

    def __post_init__(self):
        if self.triggers is None:
            self.triggers = [self.pattern]

SKILLS_REGISTRY: Dict[str, Skill] = {}

def register_skill(name: str, description: str, pattern: str, prompt_addition: str, triggers: List[str] = None):
    """Register a skill."""
    skill = Skill(name, description, pattern, prompt_addition, triggers)
    SKILLS_REGISTRY[name] = skill

def load_skills_from_dir(skills_dir: Path):
    """Load skills from SKILL.md files."""
    if not skills_dir.exists():
        return

    for skill_file in skills_dir.rglob("SKILL.md"):
        try:
            content = skill_file.read_text()
            # Parse YAML frontmatter
            if content.startswith('---'):
                _, frontmatter, body = content.split('---', 2)
                import yaml
                metadata = yaml.safe_load(frontmatter)

                name = metadata.get('name', skill_file.parent.name)
                register_skill(
                    name=name,
                    description=metadata.get('description', ''),
                    pattern=metadata.get('pattern', ''),
                    prompt_addition=body.strip(),
                    triggers=metadata.get('triggers', [])
                )
        except Exception as e:
            pass

# Register built-in skills
register_skill(
    "code-review",
    "Security-focused code review",
    r"review|code.?review|audit",
    """When reviewing code, check:
1. Security vulnerabilities (OWASP Top 10, injection attacks)
2. Error handling completeness
3. Performance implications (N+1 queries, memory leaks)
4. Resource cleanup (handles, connections)
5. Input validation at system boundaries
6. Authorization checks
Provide specific line-by-line feedback."""
)
register_skill(
    "refactor",
    "Refactor following best practices",
    r"refactor|rewrite|cleanup|improve",
    """When refactoring:
1. Preserve existing behavior - no functional changes
2. Make minimal changes - don't rewrite working code
3. Remove unused code completely, don't comment out
4. Don't add defensive code for impossible scenarios
5. Trust internal code - validate only at system boundaries
Use edit_file for surgical changes."""
)
register_skill(
    "test",
    "Write tests with proper coverage",
    r"test|spec|unit.?test|assert",
    """When writing tests:
1. One concept per test - don't chain assertions
2. Test behavior, not implementation
3. Use descriptive names (what behavior being tested)
4. Follow Arrange-Act-Assert pattern
5. Don't test framework code, only your code"""
)
register_skill(
    "debug",
    "Debug using scientific method",
    r"debug|fix.*bug|troubleshoot|issue",
    """When debugging:
1. Form hypothesis about root cause
2. Identify minimum reproduction case
3. Add targeted logging to test hypothesis
4. Gather evidence before fixing
5. Verify fix resolves root cause, not symptoms
Use tools to gather evidence systematically."""
)

# Load custom skills
load_skills_from_dir(SKILLS_DIR)

# --- Hooks System ---
Hook = Callable[[str, Dict, Any], None]
HOOKS: Dict[str, List[Hook]] = {
    "pre_tool_use": [],
    "post_tool_use": [],
    "session_start": [],
    "session_end": [],
    "user_prompt": []
}

def register_hook(event: str, hook: Hook):
    """Register a hook for an event."""
    if event in HOOKS:
        HOOKS[event].append(hook)

def trigger_hooks(event: str, tool_name: str, tool_input: Dict, context: Any) -> None:
    """Trigger all hooks for an event."""
    for hook in HOOKS.get(event, []):
        try:
            hook(tool_name, tool_input, context)
        except:
            pass

# --- Session Context ---
@dataclass
class SessionMetrics:
    start_time: float = field(default_factory=time.time)
    request_count: int = 0
    token_input: int = 0
    token_output: int = 0
    file_reads: int = 0
    file_writes: int = 0
    file_edits: int = 0
    commands_executed: int = 0
    web_searches: int = 0
    tools_used: Dict[str, int] = field(default_factory=dict)

class SessionContext:
    def __init__(self):
        self.file_context: Dict[str, str] = {}
        self.project_tree: str = ""
        self.allow_all = False
        self.permission_mode: PermissionMode = PermissionMode.ASK
        self.metrics = SessionMetrics()
        self.command_history: List[str] = []
        self.active_skills: Set[str] = set()
        self.last_tool_result: str = ""
        self.max_history = 20

        nv_dir = Path(".nv")
        self.context_file = nv_dir / "NVIDIA.md"
        if self.context_file.exists():
            self.project_tree = self.context_file.read_text()

    def request_permission(self, tool: str, args: Dict) -> bool:
        """Check if tool execution is allowed."""
        if self.permission_mode == PermissionMode.NEVER:
            return False
        if self.permission_mode == PermissionMode.AUTO:
            return True
        if self.permission_mode == PermissionMode.ACCEPT_EDITS and tool in ["write_file", "edit_file"]:
            return True
        if self.allow_all:
            return True

        console = Console()
        if tool == "execute_command":
            cmd = args.get("command", "")
            console.print(f"\n[bold yellow]? Execute:[/bold yellow] {cmd}")
        elif tool == "write_file":
            path = args.get("path", "")
            console.print(f"\n[bold yellow]? Write file:[/bold yellow] {path}")
        elif tool == "edit_file":
            path = args.get("path", "")
            console.print(f"\n[bold yellow]? Edit file:[/bold yellow] {path}")
        else:
            console.print(f"\n[bold yellow]? Use tool:[/bold yellow] {tool}")

        from rich.prompt import Confirm
        return Confirm.ask("Allow", default=False)

    def detect_skills(self, user_input: str) -> Set[str]:
        """Auto-detect relevant skills."""
        activated = set()
        for name, skill in SKILLS_REGISTRY.items():
            if re.search(skill.pattern, user_input, re.IGNORECASE):
                activated.add(name)
        return activated

    def get_status(self) -> Table:
        """Get session status."""
        table = Table(show_header=False, box=None)
        table.add_column(style="cyan bold", justify="right")
        table.add_column(style="white")

        elapsed = time.time() - self.metrics.start_time
        table.add_row("Duration", f"{int(elapsed//60)}m {int(elapsed%60)}s")
        table.add_row("Requests", str(self.metrics.request_count))
        table.add_row("Files", f"R:{self.metrics.file_reads} W:{self.metrics.file_writes} E:{self.metrics.file_edits}")
        table.add_row("Commands", str(self.metrics.commands_executed))
        table.add_row("Active Skills", ",".join(self.active_skills) if self.active_skills else "none")
        table.add_row("Permission", self.permission_mode.value)
        return table

# --- Re-Act Agent Loop ---
class ReActAgent:
    """ReAct agent that can reason and act using tools."""

    def __init__(self, client: OpenAI, model: str, context: SessionContext):
        self.client = client
        self.model = model
        self.context = context
        self.console = Console()
        self.history: List[Dict] = []

    def system_prompt(self) -> str:
        """Build system prompt with tools and context."""
        prompt = """You are an autonomous AI coding assistant. Help users write, edit, and understand code.

## Tools Available
You can use tools by calling them in your response:

```tool
read_file:{"path": "file.py"}
write_file:{"path": "file.py", "content": "..."}
edit_file:{"path": "file.py", "old_string": "...", "new_string": "..."}
execute_command:{"command": "ls -la"}
glob_search:{"pattern": "*.py"}
grep_search:{"pattern": "def main"}
list_directory:{"path": "."}
web_search:{"query": "your search"}
web_fetch:{"url": "https://..."}
git:{"command": "status"}
ask_user:{"question": "What format?"}
```

## Guidelines
1. Use tools proactively to understand the codebase
2. Make minimal, precise changes
3. Preserve existing behavior
4. Test changes before confirming completion
5. Ask for clarification if unclear

## Workflow
1. Plan: Understand the task and gather context
2. Act: Use tools to explore and modify
3. Observe: Review results
4. Iterate: Continue until done

Always provide clear explanations of what you're doing."""

        if self.context.active_skills:
            for skill_name in self.context.active_skills:
                if skill_name in SKILLS_REGISTRY:
                    prompt += f"\n\n### SKILL: {skill_name} ###\n{SKILLS_REGISTRY[skill_name].prompt_addition}"

        if self.context.file_context:
            prompt += "\n\n### ACTIVE FILES ###"
            for name, content in self.context.file_context.items():
                prompt += f"\nFile: {name}\n```\n{content[:2000]}\n```"

        return prompt

    def parse_tool_calls(self, text: str) -> List[Dict]:
        """Parse tool calls from model response."""
        calls = []
        # Match ```tool\nname:{"args"}\n```
        pattern = r'```(?:tool)?\s*\n?(\w+):(.*?)\n```'
        for match in re.finditer(pattern, text, re.DOTALL):
            tool_name = match.group(1).strip()
            args_text = match.group(2).strip()
            try:
                args = json.loads(args_text)
                calls.append({"name": tool_name, "arguments": args})
            except json.JSONDecodeError:
                # Try simple key=value parsing
                args = {}
                for line in args_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        args[key.strip()] = value.strip().strip('"').strip("'")
                calls.append({"name": tool_name, "arguments": args})
        return calls

    def run(self, user_input: str) -> str:
        """Run one turn of the ReAct loop."""
        # Detect skills
        detected = self.context.detect_skills(user_input)
        self.context.active_skills.update(detected)

        # Build messages
        messages = [{"role": "system", "content": self.system_prompt()}]
        messages.extend(self.history[-self.context.max_history:])
        messages.append({"role": "user", "content": user_input})

        # Stream response
        full_response = ""
        with Live(Spinner("dots", text="Thinking...", style="cyan"), transient=True):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=4096,
                    stream=True
                )
            except Exception as e:
                return f"Error: {e}"

        self.console.print(f"[bold cyan]NVIDIA:[/bold cyan]")
        with Live("", refresh_per_second=15) as live:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    live.update(Markdown(full_response))
        print()

        # Parse and execute tools
        tool_calls = self.parse_tool_calls(full_response)
        tool_results = []

        for call in tool_calls:
            tool_name = call["name"]
            args = call["arguments"]

            if tool_name not in tool_implementations:
                tool_results.append(f"{tool_name}: Tool not found")
                continue

            # Check permission
            if not self.context.request_permission(tool_name, args):
                tool_results.append(f"{tool_name}: Permission denied")
                continue

            # Trigger pre-hook
            trigger_hooks("pre_tool_use", tool_name, args, self.context)

            # Execute
            self.console.print(f"[dim]Running {tool_name}...[/dim]")
            result = tool_implementations[tool_name](**args)

            # Trigger post-hook
            trigger_hooks("post_tool_use", tool_name, args, self.context)

            # Update metrics
            if tool_name == "read_file":
                self.context.metrics.file_reads += 1
            elif tool_name == "write_file":
                self.context.metrics.file_writes += 1
            elif tool_name == "edit_file":
                self.context.metrics.file_edits += 1
            elif tool_name == "execute_command":
                self.context.metrics.commands_executed += 1
            elif tool_name == "web_search":
                self.context.metrics.web_searches += 1

            self.context.metrics.tools_used[tool_name] = self.context.metrics.tools_used.get(tool_name, 0) + 1

            # Show result
            self.console.print(Panel(result[:500], title=f"[dim]{tool_name}[/dim]", border_style="dim"))
            tool_results.append(f"{tool_name}: {result[:1000]}")

        # Update history
        self.history.append({"role": "user", "content": user_input})
        assistant_msg = full_response
        if tool_results:
            assistant_msg += "\n\nTool results:\n" + "\n".join(tool_results)
        self.history.append({"role": "assistant", "content": assistant_msg})

        self.context.metrics.request_count += 1

        return full_response

# --- UI Components ---
class InteractiveMenu:
    def __init__(self, options: List[str]):
        self.options = options
        self.selected_index = 0

    def run(self) -> Optional[str]:
        kb = KeyBindings()
        @kb.add("up")
        def _(event): self.selected_index = (self.selected_index - 1) % len(self.options)
        @kb.add("down")
        def _(event): self.selected_index = (self.selected_index + 1) % len(self.options)
        @kb.add("enter")
        def _(event): event.app.exit(result=self.options[self.selected_index])
        @kb.add("c-c")
        def _(event): event.app.exit(result=None)

        def get_text():
            result = []
            for i, opt in enumerate(self.options):
                if i == self.selected_index:
                    result.append(("class:selected", f"➜ {opt}\n"))
                else:
                    result.append(("class:unselected", f"  {opt}\n"))
            return result

        style = Style.from_dict({"selected": "bold #76b900", "unselected": "#888888"})
        layout = Layout(Window(FormattedTextControl(text=get_text), height=len(self.options)))
        return Application(layout=layout, key_bindings=kb, style=style, full_screen=False).run()

# --- Main CLI ---
console = Console()

SLASH_COMMANDS = {
    "/init": "Analyze project and create context",
    "/add": "Add file(s) to context (/add *.py)",
    "/drop": "Remove file(s) from context",
    "/glob": "Search files by pattern (/glob *.py)",
    "/grep": "Search file contents (/grep pattern)",
    "/clear": "Clear context and history",
    "/model": "Switch AI model",
    "/skill": "Activate/deactivate skills",
    "/skills": "List available skills",
    "/mode": "Change permission mode (ask/accept_edits/auto)",
    "/compact": "Compress conversation history",
    "/undo": "Remove last exchange",
    "/status": "Show session status",
    "/help": "Show help",
    "/quit": "Exit",
}

MENU_STYLE = Style.from_dict({
    "completion-menu": "bg:default",
    "completion-menu.completion": "fg:white bold bg:default",
    "completion-menu.meta.completion": "fg:white nobold bg:default",
    "completion-menu.completion.current": "fg:black bg:#76b900 bold",
    "completion-menu.meta.completion.current": "fg:black bg:#76b900 nobold",
})

def print_logo():
    console.print(Text("""
╔═══════════════════════════════════════════╗
║     ███╗   ██╗██╗   ██╗██╗██████╗ ██╗    ║
║     ████╗  ██║██║   ██║██║██╔══██╗██║    ║
║     ██╔██╗ ██║██║   ██║██║██║  ██║██║    ║
║     ██║╚██╗██║╚██╗ ██╔╝██║██║  ██║██║    ║
║     ██║ ╚████║ ╚████╔╝ ██║██████╔╝██║    ║
║  ═══╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚═════╝ ╚═╝══  ║
║              AI Agent v6.0                ║
╚═══════════════════════════════════════════╝
""", style="bold #76b900"))

def get_api_key() -> str:
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        load_dotenv()
        key = os.getenv("NVIDIA_API_KEY")
    if not key and CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
            key = config.get("api_key", "")
        except:
            pass
    if not key:
        print_logo()
        console.print(Panel("Authentication Required", style="bold red"))
        if typer.confirm("Open browser for NVIDIA API key?", default=True):
            typer.launch("https://build.nvidia.com/explore")
        key = Prompt.ask("[bold green]Paste API Key[/bold green]", password=True)
        if key.startswith("nvapi-"):
            CONFIG_FILE.write_text(json.dumps({"api_key": key}, indent=2))
            return key
        sys.exit(1)
    return key

MODELS = {
    "default": "deepseek-ai/deepseek-v3.2",
    "qwen3-coder": "deepseek-ai/deepseek-v3.2",
    "minimax": "deepseek-ai/deepseek-v3.2",
    "nano": "nvidia/nemotron-nano-12b-v2-vl",
    "deepseek": "deepseek-ai/deepseek-v3.2",
    "llama70": "nvidia/llama-3.1-nemotron-70b-instruct",
    "llama8": "meta/llama-3.1-8b-instruct",
}

app = typer.Typer(help=f"NVIDIA AI CLI Tool v{VERSION}", add_completion=False)

@app.command()
def chat(
    model: str = typer.Option("default", "--model", "-m"),
    skill: List[str] = typer.Option([], "--skill"),
    mode: str = typer.Option("ask", "--mode", help="Permission: ask/accept_edits/auto")
):
    """Interactive chat with ReAct agent."""
    api_key = get_api_key()
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

    current_model = MODELS.get(model, MODELS["default"])
    if MODEL_CONFIG_FILE.exists():
        stored = MODEL_CONFIG_FILE.read_text().strip()
        if stored in MODELS:
            current_model = MODELS[stored]

    context = SessionContext()
    if mode in ["ask", "accept_edits", "auto", "never"]:
        context.permission_mode = PermissionMode(mode)

    agent = ReActAgent(client, current_model, context)

    print_logo()
    console.print(f"[dim]Model: {model} | Mode: {context.permission_mode.value} | /help for commands | Ctrl+C to exit[/dim]\n")

    # Trigger session start hooks
    trigger_hooks("session_start", "", {}, context)

    session = PromptSession(
        completer=FuzzyWordCompleter(
            list(SLASH_COMMANDS.keys()),
            meta_dict=SLASH_COMMANDS,
            pattern=re.compile(r'([a-zA-Z0-9_/:-]+)')
        ),
        style=MENU_STYLE
    )

    try:
        while True:
            # Build prompt label
            label = "<bold><green>You</green></bold>"
            if context.active_skills:
                label += f" <dim>[{','.join(context.active_skills)}]</dim>"

            user_input = session.prompt(HTML(label + ": "))
            if not user_input.strip():
                continue

            # Trigger user prompt hooks
            trigger_hooks("user_prompt", "", {}, context)

            # Handle slash commands
            if user_input.startswith("/"):
                parts = shlex.split(user_input)
                cmd = parts[0].lower()
                args = parts[1:]

                if cmd == "/quit":
                    break
                elif cmd == "/help":
                    table = Table(show_header=False, box=None)
                    table.add_column(style="bold green", width=12)
                    table.add_column(style="white")
                    for c, desc in SLASH_COMMANDS.items():
                        table.add_row(c, desc)
                    console.print(Panel(table, title="Commands", border_style="dim"))
                    continue

                elif cmd == "/init":
                    nv_dir = Path(".nv")
                    nv_dir.mkdir(exist_ok=True)
                    files = []
                    for p in Path(".").rglob("*"):
                        if p.is_file() and not any(x.startswith('.') for x in p.parts):
                            files.append(str(p))
                    context.project_tree = "\n".join(files[:100])
                    console.print(f"[green]✓ Analyzed {len(files)} files[/green]")
                    continue

                elif cmd == "/add":
                    for pattern in args:
                        matched = False
                        for p in Path(".").rglob("*"):
                            if fnmatch.fnmatch(p.name, pattern) or str(p) == pattern:
                                if p.is_file():
                                    content = p.read_text(encoding='utf-8', errors='replace')
                                    context.file_context[str(p)] = content
                                    console.print(f"[dim]Added {p} ({len(content)//4} tokens)[/dim]")
                                    matched = True
                        if not matched and Path(pattern).exists():
                            p = Path(pattern)
                            content = p.read_text(encoding='utf-8', errors='replace')
                            context.file_context[str(p)] = content
                            console.print(f"[dim]Added {p} ({len(content)//4} tokens)[/dim]")
                    continue

                elif cmd == "/drop":
                    for f in args:
                        if f in context.file_context:
                            del context.file_context[f]
                            console.print(f"[dim]Dropped {f}[/dim]")
                    continue

                elif cmd == "/clear":
                    context.file_context.clear()
                    agent.history.clear()
                    console.print("[yellow]✓ Context cleared[/yellow]")
                    continue

                elif cmd == "/glob":
                    if args:
                        result = tool_implementations["glob_search"](pattern=args[0])
                        console.print(Panel(result, title="Glob Search", border_style="dim"))
                    continue

                elif cmd == "/grep":
                    if args:
                        result = tool_implementations["grep_search"](pattern=args[0])
                        console.print(Panel(result, title="Grep Search", border_style="dim"))
                    continue

                elif cmd == "/model":
                    if args and args[0] in MODELS:
                        MODEL_CONFIG_FILE.write_text(args[0])
                        console.print(f"[green]Switched to {args[0]}. Restart to apply.[/green]")
                    else:
                        console.print(f"Available: {', '.join(MODELS.keys())}")
                    continue

                elif cmd == "/skill":
                    if not args:
                        console.print("[bold]Active skills:[/bold]", ", ".join(context.active_skills) or "none")
                        console.print("\nUse /skill <name> to toggle:")
                        for name, s in SKILLS_REGISTRY.items():
                            status = "[green]●[/green]" if name in context.active_skills else "[dim]○[/dim]"
                            console.print(f"  {status} {name}: {s.description}")
                    else:
                        for s in args:
                            if s in context.active_skills:
                                context.active_skills.remove(s)
                                console.print(f"[yellow]Deactivated {s}[/yellow]")
                            elif s in SKILLS_REGISTRY:
                                context.active_skills.add(s)
                                console.print(f"[green]Activated {s}[/green]")
                    continue

                elif cmd == "/mode":
                    if args and args[0] in ["ask", "accept_edits", "auto", "never"]:
                        context.permission_mode = PermissionMode(args[0])
                        console.print(f"[green]Mode: {context.permission_mode.value}[/green]")
                    else:
                        console.print(f"Current: {context.permission_mode.value}. Options: ask, accept_edits, auto, never")
                    continue

                elif cmd == "/status":
                    console.print(Panel(context.get_status(), title="Status", border_style="blue"))
                    continue

                elif cmd == "/compact":
                    agent.history = agent.history[-agent.context.max_history:]
                    console.print("[yellow]History compacted[/yellow]")
                    continue

                elif cmd == "/undo":
                    if len(agent.history) >= 2:
                        agent.history = agent.history[:-2]
                        console.print("[yellow]Undone last exchange[/yellow]")
                    continue

            # Run agent
            agent.run(user_input)

    except KeyboardInterrupt:
        console.print("\n[yellow]Session ended[/yellow]")
    except EOFError:
        pass
    finally:
        trigger_hooks("session_end", "", {}, context)

@app.command()
def ask(prompt: List[str] = typer.Argument(...)):
    """One-shot query."""
    api_key = get_api_key()
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

    user_prompt = " ".join(prompt)
    try:
        stream = client.chat.completions.create(
            model=MODELS["default"],
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=4096,
            stream=True
        )
        with Live("", refresh_per_second=15) as live:
            full = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    live.update(Markdown(full))
        print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    app()
