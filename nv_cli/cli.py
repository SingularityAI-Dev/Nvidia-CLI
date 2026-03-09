"""Main CLI entry point for nv_cli."""

import asyncio
import os
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from openai import OpenAI

from .config import ConfigLoader, AgentConfig
from .agents import AgentRegistry, ReActAgent
from .soul import SoulManager
from .memory import MemoryManager
from .heartbeat import HeartbeatManager
from .skills import SkillManager

console = Console()

app = typer.Typer(
    name="nv",
    help="NVIDIA CLI v7.0 - OpenClaw-inspired AI Agent Framework",
    add_completion=False
)

# Sub-commands
agent_app = typer.Typer(name="agent", help="Manage agents")
skill_app = typer.Typer(name="skill", help="Manage skills")
memory_app = typer.Typer(name="memory", help="Manage memory")
heartbeat_app = typer.Typer(name="heartbeat", help="Manage heartbeat")
config_app = typer.Typer(name="config", help="Manage configuration")

def get_api_key() -> str:
    """Get NVIDIA API key."""
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("NVIDIA_API_KEY")

    if not key:
        console.print("[bold red]NVIDIA_API_KEY not set[/bold red]")
        if Confirm.ask("Open browser to get API key?", default=True):
            typer.launch("https://build.nvidia.com/explore")
        key = Prompt.ask("Enter API Key", password=True)
        if key:
            os.environ["NVIDIA_API_KEY"] = key

    return key


def print_logo():
    """Print CLI logo."""
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


@app.command()
def chat(
    agent: str = typer.Option("default", "--agent", "-a"),
    model: str = typer.Option("", "--model", "-m"),
    mode: str = typer.Option("ask", "--mode"),
    skill: List[str] = typer.Option([], "--skill", "-s"),
):
    """Start interactive chat with an agent."""
    from .cli_chat import chat_command
    asyncio.run(chat_command(agent, model, mode, skill))


@app.command()
def ask(
    prompt: List[str] = typer.Argument(...),
    model: str = typer.Option("", "--model", "-m"),
    agent: str = typer.Option("default", "--agent", "-a"),
):
    """One-shot query."""
    from .cli_ask import ask_command
    query = " ".join(prompt)
    asyncio.run(ask_command(query, model, agent))


@app.command()
def init(
    agent: str = typer.Option("default", "--agent", "-a"),
    force: bool = typer.Option(False, "--force"),
):
    """Initialize agent workspace."""
    config_loader = ConfigLoader()
    agent_dir = config_loader.get_agent_dir(agent)

    if not agent_dir.exists() or force:
        soul_manager = SoulManager(agent_dir)
        soul_manager.ensure_files()
        console.print(f"[green]Initialized workspace at {agent_dir}[/green]")
    else:
        console.print(f"[yellow]Workspace already exists at {agent_dir}[/yellow]")


@app.command()
def status(agent: str = typer.Option(None, "--agent", "-a")):
    """Show system status."""
    config_loader = ConfigLoader()
    registry = AgentRegistry(config_loader)

    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    agents = registry.list_agents()
    table.add_row("Agents", str(len(agents)), ", ".join(agents))

    # Check memory
    memory_dir = Path.home() / ".nv-cli-config" / "memory"
    table.add_row("Memory DB", "OK" if memory_dir.exists() else "Not initialized", str(memory_dir))

    # Check skills
    skills_dir = Path.home() / ".nv-cli-config" / "skills"
    skill_count = len(list(skills_dir.glob("*/SKILL.md"))) if skills_dir.exists() else 0
    table.add_row("Skills", str(skill_count), str(skills_dir))

    console.print(table)


# --- Agent Commands ---

@agent_app.command("list")
def agent_list():
    """List all agents."""
    config_loader = ConfigLoader()
    registry = AgentRegistry(config_loader)

    table = Table(title="Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Default", style="yellow")
    table.add_column("Model", style="dim")

    for agent_id in registry.list_agents():
        agent = registry.get(agent_id)
        if agent:
            table.add_row(
                agent_id,
                agent.config.name,
                "✓" if agent.config.default else "",
                agent.config.model.primary
            )

    console.print(table)


@agent_app.command("create")
def agent_create(
    agent_id: str = typer.Argument(...),
    name: str = typer.Option(None, "--name"),
    model: str = typer.Option(None, "--model"),
):
    """Create a new agent."""
    config_loader = ConfigLoader()
    config = config_loader.load()

    # Create agent config
    agent_config = AgentConfig(id=agent_id, name=name or agent_id)
    if model:
        agent_config.model.primary = model

    config.agents.append(agent_config)
    config_loader.save(config)

    # Initialize workspace
    agent_dir = config_loader.get_agent_dir(agent_id)
    soul_manager = SoulManager(agent_dir)
    soul_manager.ensure_files()

    console.print(f"[green]Created agent {agent_id}[/green]")
    console.print(f"[dim]Workspace: {agent_dir}[/dim]")


@agent_app.command("delete")
def agent_delete(
    agent_id: str = typer.Argument(...),
    force: bool = typer.Option(False, "--force"),
):
    """Delete an agent."""
    if not force:
        if not Confirm.ask(f"Delete agent {agent_id}?", default=False):
            return

    config_loader = ConfigLoader()
    config = config_loader.load()

    config.agents = [a for a in config.agents if a.id != agent_id]
    config_loader.save(config)

    console.print(f"[green]Deleted agent {agent_id}[/green]")


# --- Skill Commands ---

@skill_app.command("list")
def skill_list():
    """List installed skills."""
    skill_manager = SkillManager()
    skills = skill_manager.list_skills()

    table = Table(title="Skills")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Tools", style="dim")

    for skill in skills:
        table.add_row(
            skill.id,
            skill.name,
            skill.version,
            str(len(skill.tools))
        )

    console.print(table)


@skill_app.command("install")
def skill_install(
    source: str = typer.Argument(..., help="Path, URL, or package name"),
    name: Optional[str] = typer.Option(None, "--name"),
):
    """Install a skill."""
    from .skills import SkillInstaller
    skills_dir = Path.home() / ".nv-cli-config" / "skills"
    installer = SkillInstaller(skills_dir)

    if installer.install(source, name):
        console.print(f"[green]Installed skill from {source}[/green]")
    else:
        console.print(f"[red]Failed to install skill[/red]")


@skill_app.command("uninstall")
def skill_uninstall(name: str = typer.Argument(...)):
    """Uninstall a skill."""
    from .skills import SkillInstaller
    skills_dir = Path.home() / ".nv-cli-config" / "skills"
    installer = SkillInstaller(skills_dir)
    installer.uninstall(name)


# --- Memory Commands ---

@memory_app.command("add")
def memory_add(
    content: str = typer.Argument(...),
    category: str = typer.Option("general", "--category"),
    agent: str = typer.Option("default", "--agent"),
):
    """Add a memory."""
    config_loader = ConfigLoader()
    config = config_loader.load()

    memory_manager = MemoryManager(agent, config.agents[0].memory if config.agents else None)
    entry_id = memory_manager.add(content, category)
    console.print(f"[green]Added memory: {entry_id}[/green]")


@memory_app.command("search")
def memory_search(
    query: str = typer.Argument(...),
    agent: str = typer.Option("default", "--agent"),
    limit: int = typer.Option(5, "--limit"),
):
    """Search memories."""
    config_loader = ConfigLoader()
    config = config_loader.load()

    memory_manager = MemoryManager(agent, config.agents[0].memory if config.agents else None)
    results = memory_manager.search(query, limit)

    table = Table(title="Memory Search")
    table.add_column("ID", style="cyan")
    table.add_column("Content", style="white")
    table.add_column("Category", style="green")

    for result in results:
        content = result.content[:50] + "..." if len(result.content) > 50 else result.content
        table.add_row(result.id[:8], content, result.category)

    console.print(table)


# --- Heartbeat Commands ---

@heartbeat_app.command("status")
def heartbeat_status(agent: str = typer.Option("default", "--agent")):
    """Show heartbeat status."""
    config_loader = ConfigLoader()
    agent_dir = config_loader.get_agent_dir(agent)
    manager = HeartbeatManager(agent_dir)

    status = manager.get_status()

    console.print(Panel(f"[bold]Heartbeat Status[/bold]", border_style="blue"))
    console.print(f"Tasks: {status['tasks']}")
    console.print(f"Due: {status['due']}")

    if status['tasks_status']:
        table = Table(title="Tasks")
        table.add_column("Name", style="cyan")
        table.add_column("Due", style="yellow")

        for task in status['tasks_status']:
            due = "[red]Yes" if task['due'] else "[green]No"
            table.add_row(task['name'], due)

        console.print(table)


# --- Config Commands ---

@config_app.command("get")
def config_get(key: Optional[str] = typer.Argument(None)):
    """Get configuration."""
    config_loader = ConfigLoader()
    config = config_loader.load()

    console.print(config)


@config_app.command("edit")
def config_edit():
    """Edit configuration."""
    config_loader = ConfigLoader()
    config_file = config_loader.config_file

    editor = os.getenv("EDITOR", "nano")
    os.system(f"{editor} {config_file}")


# Add sub-commands
app.add_typer(agent_app)
app.add_typer(skill_app)
app.add_typer(memory_app)
app.add_typer(heartbeat_app)
app.add_typer(config_app)