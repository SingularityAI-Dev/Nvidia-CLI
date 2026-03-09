"""Chat command implementation."""

import asyncio
import shlex
from typing import List

from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
from rich.prompt import Prompt
from openai import OpenAI
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, FuzzyWordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from .config import ConfigLoader
from .agents import ReActAgent
from .soul import SoulManager
from .skills import SkillManager

console = Console()

SLASH_COMMANDS = {
    "/init": "Initialize workspace",
    "/add": "Add file to context",
    "/drop": "Remove file from context",
    "/clear": "Clear context and history",
    "/skill": "Activate skill",
    "/skills": "List skills",
    "/mode": "Change permission mode",
    "/status": "Show status",
    "/compact": "Compress history",
    "/undo": "Remove last exchange",
    "/heartbeat": "Trigger heartbeat",
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


class SlashCommandCompleter(Completer):
    """Completer that only shows slash commands when text starts with '/'."""

    def __init__(self, commands: dict):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        # Only show completions if text starts with '/'
        if not text.startswith('/'):
            return
        # Filter commands based on what's typed after '/'
        word = text.split()[-1] if text.split() else text
        for cmd, desc in self.commands.items():
            if cmd.startswith(text):
                yield Completion(cmd, start_position=-len(text), display=cmd, display_meta=desc)


async def chat_command(agent_id: str, model: str, mode: str, skills: List[str]):
    """Start interactive chat."""
    config_loader = ConfigLoader()
    config = config_loader.load()

    # Find agent config
    agent_config = None
    for agent in config.agents:
        if agent.id == agent_id or agent.default:
            agent_config = agent
            break

    if not agent_config:
        console.print(f"[red]Agent {agent_id} not found[/red]")
        return

    # Initialize components
    agent_dir = config_loader.get_agent_dir(agent_config.id)
    soul_manager = SoulManager(agent_dir)
    soul_manager.ensure_files()

    skill_manager = SkillManager()

    # Setup OpenAI client
    from .utils import get_api_key
    api_key = get_api_key()
    if not api_key:
        return

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

    # Use model from config or override
    current_model = model or agent_config.model.primary

    # Setup permission mode
    from .config import PermissionMode
    if mode in ["ask", "accept_edits", "auto", "never"]:
        agent_config.permission_mode = PermissionMode(mode)

    # Create agent
    agent = ReActAgent(client, current_model, agent_config, soul_manager, skill_manager)
    agent.start()

# Print header
    console.print("""
[bold #76b900]╔═══════════════════════════════════════════╗
║ ███╗ ██╗██╗ ██╗██╗██████╗ ██╗ ║
║ ████╗ ██║██║ ██║██║██╔══██╗ ██║ ║
║ ██╔██╗ ██║██║ ██║██║██║ ██║ ██║ ║
║ ██║╚██╗██║╚██╗ ██╔╝██║██║ ██║ ██║ ║
║ ██║ ╚████║ ╚████╔╝ ██║██████╔╝ ██║ ║
║ ═══╚═╝  ╚═══╝  ╚═══╝ ╚═╝╚═════╝  ╚═╝══ ║
║              AI Agent v7.0                ║
╚═══════════════════════════════════════════╝[/bold #76b900]
""")
    console.print(f"[dim]Commands: /help | Mode: {agent_config.permission_mode.value} | Ctrl+C to exit[/dim]\n")

    # Setup prompt session with slash command completer
    session = PromptSession(
        completer=SlashCommandCompleter(SLASH_COMMANDS),
        style=MENU_STYLE
    )

    try:
        while True:
            # Build prompt
            label = f"<bold><green>You</green></bold>"
            if agent.context.active_skills:
                label += f" <dim>[{','.join(agent.context.active_skills)}]</dim>"

            user_input = await session.prompt_async(HTML(label + ": "))

            if not user_input.strip():
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                parts = shlex.split(user_input)
                cmd = parts[0].lower()
                args = parts[1:]

                if cmd == "/quit":
                    break
                elif cmd == "/help":
                    table = Panel(
                        "\n".join([f"[bold green]{c}[/bold green] - {d}" for c, d in SLASH_COMMANDS.items()]),
                        title="Commands"
                    )
                    console.print(table)
                    continue
                elif cmd == "/status":
                    import json
                    console.print(Panel(json.dumps(agent.get_status(), indent=2), title="Status"))
                    continue
                elif cmd == "/clear":
                    agent.context.file_context.clear()
                    agent.history.clear()
                    console.print("[yellow]Context cleared[/yellow]")
                    continue
                elif cmd == "/mode":
                    if args and args[0] in ["ask", "accept_edits", "auto", "never"]:
                        agent_config.permission_mode = PermissionMode(args[0])
                        console.print(f"[green]Mode: {agent_config.permission_mode.value}[/green]")
                    continue
                elif cmd == "/skill":
                    if args:
                        agent.context.active_skills.add(args[0])
                        console.print(f"[green]Activated {args[0]}[/green]")
                    else:
                        console.print(f"Active: {', '.join(agent.context.active_skills) or 'none'}")
                    continue
                elif cmd == "/add":
                    for pattern in args:
                        from pathlib import Path
                        import fnmatch
                        for p in Path(".").rglob("*"):
                            if fnmatch.fnmatch(p.name, pattern) or str(p) == pattern:
                                if p.is_file():
                                    content = p.read_text(encoding='utf-8', errors='replace')
                                    agent.context.file_context[str(p)] = content
                                    console.print(f"[dim]Added {p}[/dim]")
                    continue

            # Process user input
            try:
                await agent.run(user_input)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Session ended[/yellow]")
    finally:
        agent.stop()