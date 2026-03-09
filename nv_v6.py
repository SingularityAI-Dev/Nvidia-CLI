#!/usr/bin/env python3
"""
NVIDIA CLI v6.0 - Claude Code-inspired AI Agent
ReAct pattern with tools, skills, and permissions.
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
from typing import List, Dict, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from openai import OpenAI
from dotenv import load_dotenv

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

# Config
VERSION = "6.0.0"
CONFIG_DIR = Path.home() / ".nv-cli-config"
CONFIG_FILE = CONFIG_DIR / "config.json"
SKILLS_DIR = CONFIG_DIR / "skills"

# Ensure dirs exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SKILLS_DIR.mkdir(exist_ok=True)

console = Console()

# Permission modes
class PermissionMode(Enum):
    ASK = "ask"
    ACCEPT_EDITS = "accept_edits"
    AUTO = "auto"
    NEVER = "never"

# Tools
tool_implementations: Dict[str, Callable] = {}

def tool(func: Callable) -> Callable:
    tool_implementations[func.__name__] = func
    return func

@tool
def read_file(path: str, limit: int = 100) -> str:
    """Read a file."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return f"Error: {path} not found"
        lines = p.read_text().split('\n')[:limit]
        return '\n'.join(f"{i+1:3d}| {l}" for i, l in enumerate(lines))
    except Exception as e:
        return f"Error: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """Write to a file."""
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Wrote {p}"
    except Exception as e:
        return f"Error: {e}"

@tool
def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit part of a file."""
    try:
        p = Path(path).expanduser()
        text = p.read_text()
        if old_string not in text:
            return "Error: old_string not found"
        p.write_text(text.replace(old_string, new_string, 1))
        return f"Edited {p}"
    except Exception as e:
        return f"Error: {e}"

@tool
def execute_command(command: str) -> str:
    """Run a shell command."""
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        out = r.stdout or ""
        if r.stderr:
            out += "\n[stderr] " + r.stderr
        return out[:2000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"

@tool
def glob_search(pattern: str) -> str:
    """Find files matching pattern."""
    files = list(Path(".").rglob(pattern))
    return '\n'.join(str(f) for f in files[:50]) or "No files found"

@tool
def grep_search(pattern: str) -> str:
    """Search in files."""
    results = []
    for p in Path(".").rglob("*"):
        if p.is_file() and p.stat().st_size < 100000:
            try:
                text = p.read_text(errors='ignore')
                if pattern in text:
                    lines = [f"{i+1}|{l[:80]}" for i, l in enumerate(text.split('\n')) if pattern in l][:3]
                    results.append(f"{p}:\n" + '\n'.join(lines))
            except:
                pass
    return '\n'.join(results[:20]) or "No matches"

@tool
def list_directory(path: str = ".") -> str:
    """List directory."""
    p = Path(path).expanduser()
    items = []
    for item in sorted(p.iterdir())[:50]:
        items.append(item.name + "/" if item.is_dir() else item.name)
    return '\n'.join(items)

@tool
def git(command: str) -> str:
    """Run git."""
    return execute_command(f"git {command}")

# Skills
@dataclass
class Skill:
    name: str
    description: str
    pattern: str
    prompt_addition: str

SKILLS_REGISTRY: Dict[str, Skill] = {}

def register_skill(name: str, desc: str, pattern: str, addition: str):
    SKILLS_REGISTRY[name] = Skill(name, desc, pattern, addition)

register_skill("code-review", "Code review", r"review", "Check security, errors, performance")
register_skill("refactor", "Refactor", r"refactor", "Make minimal changes, preserve behavior")
register_skill("test", "Write tests", r"test", "Follow AAA pattern, test behavior")
register_skill("debug", "Debug", r"debug", "Use scientific method")

# Session
@dataclass
class SessionContext:
    file_context: Dict[str, str] = field(default_factory=dict)
    active_skills: Set[str] = field(default_factory=set)
    permission_mode: PermissionMode = PermissionMode.ASK
    allow_all: bool = False
    request_count: int = 0

    def request_permission(self, tool: str, args: Dict) -> bool:
        if self.permission_mode == PermissionMode.AUTO or self.allow_all:
            return True
        if self.permission_mode == PermissionMode.ACCEPT_EDITS and tool in ["write_file", "edit_file"]:
            return True
        if self.permission_mode == PermissionMode.NEVER:
            return False

        details = args.get("path") or args.get("command", "")[:50]
        return Confirm.ask(f"Allow {tool} on {details}?", default=False)

# Agent
class ReActAgent:
    def __init__(self, client: OpenAI, model: str, context: SessionContext):
        self.client = client
        self.model = model
        self.context = context
        self.history: List[Dict] = []

    def system_prompt(self) -> str:
        prompt = """You are an AI coding assistant. Use tools by calling:

```tool
read_file:{"path": "file.py"}
write_file:{"path": "file.py", "content": "..."}
edit_file:{"path": "file.py", "old_string": "...", "new_string": "..."}
execute_command:{"command": "ls"}
glob_search:{"pattern": "*.py"}
grep_search:{"pattern": "def main"}
list_directory:{"path": "."}
git:{"command": "status"}
```

Guidelines:
1. Use tools to understand the codebase
2. Make minimal, precise changes
3. Test before confirming
"""
        if self.context.active_skills:
            for name in self.context.active_skills:
                if name in SKILLS_REGISTRY:
                    prompt += f"\n[{name.upper()}] {SKILLS_REGISTRY[name].prompt_addition}"
        return prompt

    def parse_tools(self, text: str) -> List[Dict]:
        calls = []
        for m in re.finditer(r'```(?:tool)?\s*\n?(\w+):(.*?)\n```', text, re.DOTALL):
            try:
                calls.append({"name": m.group(1), "args": json.loads(m.group(2))})
            except:
                pass
        return calls

    def run(self, user_input: str):
        # Detect skills
        for name, skill in SKILLS_REGISTRY.items():
            if re.search(skill.pattern, user_input, re.I):
                self.context.active_skills.add(name)

        messages = [{"role": "system", "content": self.system_prompt()}]
        messages.extend(self.history[-10:])
        messages.append({"role": "user", "content": user_input})

        with Live(Spinner("dots", text="Thinking...", style="cyan"), transient=True):
            stream = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=4096, stream=True
            )

        console.print("[bold cyan]NVIDIA:[/bold cyan]")
        full = ""
        with Live("", refresh_per_second=15) as live:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    live.update(Markdown(full))
        print()

        # Execute tools
        tool_results = []
        for call in self.parse_tools(full):
            name, args = call["name"], call["args"]
            if name not in tool_implementations:
                continue
            if not self.context.request_permission(name, args):
                continue

            console.print(f"[dim]Running {name}...[/dim]")
            result = tool_implementations[name](**args)
            console.print(Panel(result[:500], title=name, border_style="dim"))
            tool_results.append(f"{name}: {result[:500]}")

        self.history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": full + "\n" + "\n".join(tool_results)}
        ])
        self.context.request_count += 1

# CLI
SLASH_COMMANDS = {
    "/init": "Analyze project",
    "/add": "Add file to context",
    "/drop": "Remove file",
    "/clear": "Clear context",
    "/model": "Switch model",
    "/skill": "Toggle skills",
    "/mode": "Permission mode (ask/accept_edits/auto)",
    "/status": "Show status",
    "/help": "Help",
    "/quit": "Exit",
}

def get_api_key():
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        load_dotenv()
        key = os.getenv("NVIDIA_API_KEY")
    if not key and CONFIG_FILE.exists():
        key = json.loads(CONFIG_FILE.read_text()).get("api_key")
    if not key:
        key = Prompt.ask("NVIDIA API key", password=True)
        if key.startswith("nvapi-"):
            CONFIG_FILE.write_text(json.dumps({"api_key": key}))
    return key

MODELS = {
    "default": "deepseek-ai/deepseek-v3.2",
    "nano": "nvidia/nemotron-nano-12b-v2-vl",
    "deepseek": "deepseek-ai/deepseek-v3.2",
    "llama70": "nvidia/llama-3.1-nemotron-70b-instruct",
}

app = typer.Typer()

@app.command()
def chat(model: str = "default", mode: str = "ask"):
    """Interactive chat."""
    api_key = get_api_key()
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    current = MODELS.get(model, MODELS["default"])

    ctx = SessionContext()
    if mode in [m.value for m in PermissionMode]:
        ctx.permission_mode = PermissionMode(mode)

    agent = ReActAgent(client, current, ctx)

    console.print(Text("NVIDIA CLI v6.0", style="bold #76b900"))
    console.print(f"[dim]Model: {model} | Mode: {mode} | /help for commands[/dim]\n")

    session = PromptSession(
        completer=FuzzyWordCompleter(list(SLASH_COMMANDS.keys()), meta_dict=SLASH_COMMANDS)
    )

    while True:
        try:
            user_input = session.prompt(HTML("<bold><green>You</green></bold>: "))
            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                parts = user_input.split()
                cmd = parts[0]
                args = parts[1:]

                if cmd == "/quit":
                    break

                elif cmd == "/add":
                    for f in args:
                        p = Path(f)
                        if p.exists():
                            ctx.file_context[f] = p.read_text()
                            console.print(f"[dim]Added {f}[/dim]")
                    continue

                elif cmd == "/drop":
                    for f in args:
                        ctx.file_context.pop(f, None)
                        console.print(f"[dim]Dropped {f}[/dim]")
                    continue

                elif cmd == "/clear":
                    ctx.file_context.clear()
                    agent.history.clear()
                    console.print("[yellow]Cleared[/yellow]")
                    continue

                elif cmd == "/skill":
                    if not args:
                        for name in SKILLS_REGISTRY:
                            status = "[green]●[/green]" if name in ctx.active_skills else "[dim]○[/dim]"
                            console.print(f"  {status} {name}")
                    else:
                        for s in args:
                            if s in ctx.active_skills:
                                ctx.active_skills.remove(s)
                            else:
                                ctx.active_skills.add(s)
                        console.print(f"Skills: {ctx.active_skills}")
                    continue

                elif cmd == "/mode":
                    if args and args[0] in [m.value for m in PermissionMode]:
                        ctx.permission_mode = PermissionMode(args[0])
                        console.print(f"[green]Mode: {ctx.permission_mode.value}[/green]")
                    continue

                elif cmd == "/status":
                    table = Table(show_header=False)
                    table.add_column(style="cyan")
                    table.add_column(style="white")
                    table.add_row("Requests", str(ctx.request_count))
                    table.add_row("Files", str(len(ctx.file_context)))
                    table.add_row("Skills", ",".join(ctx.active_skills) or "none")
                    table.add_row("Mode", ctx.permission_mode.value)
                    console.print(Panel(table, title="Status", border_style="blue"))
                    continue

                elif cmd == "/help":
                    for c, d in SLASH_COMMANDS.items():
                        console.print(f"  {c} - {d}")
                    continue

            agent.run(user_input)

        except KeyboardInterrupt:
            break

@app.command()
def ask(prompt: List[str] = typer.Argument(...)):
    """One-shot query."""
    api_key = get_api_key()
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    text = " ".join(prompt)

    try:
        stream = client.chat.completions.create(
            model=MODELS["default"],
            messages=[{"role": "user", "content": text}],
            max_tokens=4096,
            stream=True
        )
        with Live("", refresh_per_second=15) as live:
            full = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    live.update(Markdown(full))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    app()
