"""Ask command implementation."""

from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from openai import OpenAI

from .config import ConfigLoader
from .agents import ReActAgent
from .soul import SoulManager
from .skills import SkillManager

console = Console()


async def ask_command(query: str, model: str, agent_id: str):
    """One-shot query."""
    from .utils import get_api_key

    api_key = get_api_key()
    if not api_key:
        return

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

    config_loader = ConfigLoader()
    config = config_loader.load()

    # Find agent
    agent_config = None
    for agent in config.agents:
        if agent.id == agent_id or agent.default:
            agent_config = agent
            break

    if not agent_config:
        console.print(f"[red]Agent {agent_id} not found[/red]")
        return

    # Override model if specified
    current_model = model or agent_config.model.primary

    # Initialize
    agent_dir = config_loader.get_agent_dir(agent_config.id)
    soul_manager = SoulManager(agent_dir)
    skill_manager = SkillManager()

    # Create agent for one-shot
    agent = ReActAgent(client, current_model, agent_config, soul_manager, skill_manager)
    agent.start()

    # Run query
    await agent.run(query)
    agent.stop()