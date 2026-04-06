"""Agent registry for managing multiple agents."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import asdict

from ..config import Config, AgentConfig, ConfigLoader
from ..soul import SoulManager
from .agent import Agent, ReActAgent


class AgentRegistry:
    """Registry for managing multiple agents."""

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.agents: Dict[str, Agent] = {}
        self._load_config()

    def _load_config(self):
        """Load agents from config."""
        config = self.config_loader.load()
        for agent_config in config.agents:
            self._init_agent(agent_config)

    def _init_agent(self, config: AgentConfig):
        """Initialize an agent from config."""
        agent_dir = self.config_loader.get_agent_dir(config.id)
        soul_manager = SoulManager(agent_dir)
        agent = Agent(config.id, config, soul_manager)
        self.agents[config.id] = agent

    def get(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def get_default(self) -> Optional[Agent]:
        """Get the default agent."""
        for agent in self.agents.values():
            if agent.config.default:
                return agent
        return self.agents[list(self.agents.keys())[0]] if self.agents else None

    def list_agents(self) -> List[str]:
        """List all agent IDs."""
        return list(self.agents.keys())

    def start_agent(self, agent_id: str) -> bool:
        """Start an agent."""
        agent = self.agents.get(agent_id)
        if agent:
            agent.start()
            return True
        return False

    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent."""
        agent = self.agents.get(agent_id)
        if agent:
            agent.stop()
            return True
        return False

    def get_status(self) -> Dict:
        """Get status of all agents."""
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }