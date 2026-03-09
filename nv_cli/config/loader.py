"""Configuration loader with file-based config."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .config import Config, AgentConfig, ModelConfig, MemoryConfig, SandboxConfig, SubagentConfig, HeartbeatConfig, GatewayConfig
from .validation import validate_config

CONFIG_DIR = Path.home() / ".nv-cli-config"
CONFIG_FILE = CONFIG_DIR / "config.json"

class ConfigLoader:
    """Loads and manages configuration from files."""

    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure config directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "agents").mkdir(exist_ok=True)
        (self.config_dir / "skills").mkdir(exist_ok=True)
        (self.config_dir / "memory").mkdir(exist_ok=True)
        (self.config_dir / "logs").mkdir(exist_ok=True)

    def load(self) -> Config:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                return self._from_dict(data)
            except Exception:
                return self._create_default()
        return self._create_default()

    def save(self, config: Config):
        """Save configuration to file."""
        data = self._to_dict(config)
        self.config_file.write_text(json.dumps(data, indent=2))

    def _create_default(self) -> Config:
        """Create default configuration."""
        config = Config()
        self.save(config)
        return config

    def _from_dict(self, data: Dict[str, Any]) -> Config:
        """Create Config from dictionary."""
        agents_data = data.get("agents", [])
        agents = []
        for agent_data in agents_data:
            model_data = agent_data.get("model", {})
            memory_data = agent_data.get("memory", {})
            heartbeat_data = agent_data.get("heartbeat", {})
            subagent_data = agent_data.get("subagents", {})
            sandbox_data = agent_data.get("sandbox", {})

            agent = AgentConfig(
                id=agent_data.get("id", "default"),
                name=agent_data.get("name", "Assistant"),
                default=agent_data.get("default", False),
                model=ModelConfig(
                    primary=model_data.get("primary", "nvidia/deepseek-ai/deepseek-v3.2"),
                    fallbacks=model_data.get("fallbacks", []),
                    temperature=model_data.get("temperature", 0.3),
                    max_tokens=model_data.get("max_tokens", 4096),
                ),
                memory=MemoryConfig(
                    enabled=memory_data.get("enabled", True),
                    backend=memory_data.get("backend", "sqlite"),
                    embedding_provider=memory_data.get("embedding_provider", "openai"),
                ),
                heartbeat=HeartbeatConfig(
                    enabled=heartbeat_data.get("enabled", False),
                    interval_minutes=heartbeat_data.get("interval_minutes", 60),
                ),
                skills=agent_data.get("skills", []),
            )
            agents.append(agent)

        return Config(agents=agents)

    def _to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "version": config.version,
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "default": agent.default,
                    "model": {
                        "primary": agent.model.primary,
                        "fallbacks": agent.model.fallbacks,
                        "temperature": agent.model.temperature,
                        "max_tokens": agent.model.max_tokens,
                    },
                    "memory": {
                        "enabled": agent.memory.enabled,
                        "backend": agent.memory.backend,
                        "embedding_provider": agent.memory.embedding_provider,
                    },
                    "skills": agent.skills,
                }
                for agent in config.agents
            ],
        }

    def get_agent_dir(self, agent_id: str) -> Path:
        """Get the configuration directory for an agent."""
        return self.config_dir / "agents" / agent_id