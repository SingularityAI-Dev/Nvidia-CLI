"""Configuration classes for nv_cli."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum

class PermissionMode(Enum):
    ASK = "ask"
    ACCEPT_EDITS = "accept_edits"
    AUTO = "auto"
    NEVER = "never"

class SandboxMode(Enum):
    OFF = "off"
    NON_MAIN = "non_main"
    ALL = "all"

@dataclass
class ModelConfig:
    """Model configuration with fallbacks."""
    primary: str = "nvidia/deepseek-ai/deepseek-v3.2"
    fallbacks: List[str] = field(default_factory=list)
    temperature: float = 0.3
    max_tokens: int = 4096
    top_p: Optional[float] = None

@dataclass
class MemoryConfig:
    """Memory search configuration."""
    enabled: bool = True
    backend: str = "sqlite"  # sqlite, chroma
    embedding_provider: str = "openai"  # openai, local, nvidia
    embedding_model: Optional[str] = None
    chunk_size: int = 400
    chunk_overlap: int = 80
    max_results: int = 6
    min_score: float = 0.35
    use_hybrid: bool = True
    vector_weight: float = 0.7
    text_weight: float = 0.3
    cache_enabled: bool = True

@dataclass
class SubagentConfig:
    """Subagent spawning configuration."""
    allow_agents: List[str] = field(default_factory=list)
    model: Optional[str] = None
    timeout_seconds: int = 300

@dataclass
class HeartbeatConfig:
    """Heartbeat configuration."""
    enabled: bool = False
    interval_minutes: int = 60
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None
    batch_checks: bool = True

@dataclass
class SandboxConfig:
    """Sandbox configuration for skills."""
    mode: SandboxMode = SandboxMode.NON_MAIN
    docker_enabled: bool = False
    workspace_access: str = "ro"  # none, ro, rw

@dataclass
class AgentConfig:
    """Agent configuration."""
    id: str
    name: str = "Assistant"
    default: bool = False
    model: ModelConfig = field(default_factory=ModelConfig)
    skills: List[str] = field(default_factory=list)  # Allowlist, empty = all
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)
    subagents: SubagentConfig = field(default_factory=SubagentConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    permission_mode: PermissionMode = PermissionMode.ASK
    max_history: int = 20
    identity_file: str = "IDENTITY.md"
    soul_file: str = "SOUL.md"
    memory_file: str = "MEMORY.md"
    user_file: str = "USER.md"
    heartbeat_file: str = "HEARTBEAT.md"

@dataclass
class GatewayConfig:
    """Gateway configuration for multi-channel support."""
    enabled: bool = False
    host: str = "localhost"
    port: int = 8080
    auth_token: Optional[str] = None

@dataclass
class Config:
    """Main configuration."""
    version: str = "7.0.0"
    agents: List[AgentConfig] = field(default_factory=lambda: [
        AgentConfig(id="default", name="NVIDIA Assistant", default=True)
    ])
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    global_skills: List[str] = field(default_factory=list)
    tools_policy: Dict[str, Any] = field(default_factory=dict)
    logging_level: str = "INFO"