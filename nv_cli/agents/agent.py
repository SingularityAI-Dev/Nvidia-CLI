"""Main Agent implementation using ReAct pattern."""

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Set
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.text import Text
from openai import OpenAI

from ..config import AgentConfig
from ..soul import SoulManager
from ..skills import SkillManager
from ..tools import ToolRegistry


@dataclass
class SessionMetrics:
    """Metrics for a session."""
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


@dataclass
class SessionContext:
    """Context for an agent session."""
    file_context: Dict[str, str] = field(default_factory=dict)
    project_tree: str = ""
    allow_all: bool = False
    active_skills: Set[str] = field(default_factory=set)
    last_tool_result: str = ""
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    command_history: List[str] = field(default_factory=list)
    max_history: int = 20

    def __post_init__(self):
        self.nv_dir = Path(".nv")
        self.context_file = self.nv_dir / "NVIDIA.md"
        if self.context_file.exists():
            self.project_tree = self.context_file.read_text()


class Agent:
    """Base agent class."""

    def __init__(self, agent_id: str, config: AgentConfig, soul_manager: SoulManager):
        self.agent_id = agent_id
        self.config = config
        self.soul = soul_manager
        self.metrics = SessionMetrics()
        self.console = Console()
        self.is_running = False

    def start(self):
        """Start the agent."""
        self.is_running = True
        self.metrics = SessionMetrics()

    def stop(self):
        """Stop the agent."""
        self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "status": "running" if self.is_running else "stopped",
            "uptime": time.time() - self.metrics.start_time,
            "requests": self.metrics.request_count,
            "tools_used": self.metrics.tools_used,
        }


class ReActAgent(Agent):
    """ReAct (Reasoning + Acting) agent implementation."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        config: AgentConfig,
        soul_manager: SoulManager,
        skill_manager: Optional[SkillManager] = None,
    ):
        super().__init__(config.id, config, soul_manager)
        self.client = client
        self.model = model
        self.config = config
        self.soul = soul_manager
        self.skills = skill_manager or SkillManager()
        self.context = SessionContext()
        self.history: List[Dict] = []
        self.console = Console()

    def system_prompt(self) -> str:
        """Build system prompt with OpenClaw identity."""
        soul = self.soul.load_soul()

        # Build comprehensive identity preamble
        identity_parts = []

        # Agent workspace location
        agent_dir = self.soul.workspace
        identity_parts.append(f"## Your Identity Files Location\nYour identity files are stored at: {agent_dir}")

        # IDENTITY
        if soul.identity.name:
            identity_parts.append(f"\n# You are: {soul.identity.name}")
        if soul.identity.creature:
            identity_parts.append(f"## Creature Type: {soul.identity.creature}")
        if soul.identity.vibe:
            identity_parts.append(f"## Vibe: {soul.identity.vibe}")

        # SOUL - Core principles and boundaries
        if soul.soul_text:
            identity_parts.append(f"\n## Your Soul (Core Principles)\n{soul.soul_text}")

        # MEMORY - Important context
        if soul.memory_text:
            identity_parts.append(f"\n## Memories\n{soul.memory_text[:1500]}")

        # USER - Who you're talking to
        if soul.user.name:
            identity_parts.append(f"\n## User\nName: {soul.user.name}")
            if soul.user.preferences:
                identity_parts.append(f"Preferences: {soul.user.preferences}")

        # AGENTS - Subagent knowledge
        if soul.agents_text:
            identity_parts.append(f"\n## Agent Orchestration Knowledge\n{soul.agents_text[:1000]}")

        # HEARTBEAT - Periodic tasks awareness
        if soul.heartbeat_text:
            identity_parts.append(f"\n## Heartbeat Tasks\n{soul.heartbeat_text[:500]}")

        # TOOLS - What you can do
        if soul.tools_text:
            identity_parts.append(f"\n## Tools Knowledge\n{soul.tools_text[:1000]}")

        identity_block = "\n".join(identity_parts)

        # Skills
        available_skills = self.skills.get_active_skills(self.config.skills)
        skills_text = ""
        if available_skills:
            skills_text = "\n\n## Available Skills\n"
            for skill in available_skills:
                skills_text += f"- {skill.name}: {skill.description}\n"

        # Active files
        active_files = ""
        if self.context.file_context:
            active_files = "\n\n## Active Files\n"
            for name, content in self.context.file_context.items():
                active_files += f"File: {name}\n```\n{content[:1500]}\n```\n"

        prompt = f"""{identity_block}

---

## Your Capabilities (Tools)
You can use tools by calling them in your response:

```tool
read_file:{{"path": "file.py"}}
write_file:{{"path": "file.py", "content": "..."}}
edit_file:{{"path": "file.py", "old_string": "...", "new_string": "..."}}
execute_command:{{"command": "ls -la"}}
glob_search:{{"pattern": "*.py"}}
grep_search:{{"pattern": "def main"}}
list_directory:{{"path": "."}}
web_search:{{"query": "your search"}}
web_fetch:{{"url": "https://..."}}
ask_user:{{"question": "What format?"}}
spawn_agent:{{"task": "Analyze codebase", "agent_id": "analyzer"}}
```

Use the ReAct pattern: Plan → Act → Observe → Iterate.{skills_text}{active_files}"""

        return prompt

    def parse_tool_calls(self, text: str) -> List[Dict]:
        """Parse tool calls from model response."""
        calls = []
        # Match ```tool\ntool_name:{"args"}\n```
        pattern = r'```(?:tool)?\s*\n?(\w+):(.*?)\n```'
        for match in re.finditer(pattern, text, re.DOTALL):
            tool_name = match.group(1).strip()
            args_text = match.group(2).strip()
            try:
                args = json.loads(args_text)
                calls.append({"name": tool_name, "arguments": args})
            except json.JSONDecodeError:
                # Simple key=value fallback
                args = {}
                for line in args_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        args[key.strip()] = value.strip().strip('"')
                calls.append({"name": tool_name, "arguments": args})
        return calls

    async def run(self, user_input: str) -> str:
        """Run one turn of the ReAct loop."""
        # Detect skills
        detected = self._detect_skills(user_input)
        self.context.active_skills.update(detected)

        # Build messages
        messages = [
            {"role": "system", "content": self.system_prompt()},
            *self.history[-self.context.max_history:],
            {"role": "user", "content": user_input}
        ]

        # Stream response
        full_response = ""
        with Live(Spinner("dots", text="Thinking...", style="cyan"), transient=True):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.config.model.temperature,
                    max_tokens=self.config.model.max_tokens,
                    stream=True
                )
            except Exception as e:
                return f"Error: {e}"

        self.console.print(f"[bold cyan]{self.config.name}:[/bold cyan]")
        with Live("", refresh_per_second=15) as live:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    live.update(Markdown(full_response))

        # Parse and execute tools
        tool_calls = self.parse_tool_calls(full_response)
        tool_results = []

        for call in tool_calls:
            result = await self._execute_tool(call)
            if result:
                tool_results.append(f"{call['name']}: {result}")

        # Update history
        self.history.append({"role": "user", "content": user_input})
        assistant_msg = full_response
        if tool_results:
            assistant_msg += "\n\nTool results:\n" + "\n".join(tool_results)
        self.history.append({"role": "assistant", "content": assistant_msg})

        self.metrics.request_count += 1
        return full_response

    def _detect_skills(self, user_input: str) -> Set[str]:
        """Auto-detect skills based on keywords."""
        detected = set()
        keywords = {
            "python": ["code", "python", "script"],
            "web": ["search", "web", "url", "http"],
            "file": ["read", "file", "edit", "write"],
            "git": ["commit", "git", "branch", "merge"],
        }
        for skill, words in keywords.items():
            for word in words:
                if word in user_input.lower():
                    detected.add(skill)
                    break
        return detected

    async def _execute_tool(self, call: Dict) -> Optional[str]:
        """Execute a tool call."""
        tool_name = call["name"]
        args = call["arguments"]

        # Get tool implementation
        from ..tools import ToolRegistry
        tools = ToolRegistry()

        if tool_name not in tools:
            return f"Tool {tool_name} not found"

        # Check permissions
        if not self._check_permission(tool_name, args):
            return "Permission denied"

        # Execute
        self.console.print(f"[dim]Running {tool_name}...[/dim]")
        try:
            result = tools[tool_name](**args)
            self.console.print(Panel(result[:500], title=tool_name, border_style="dim"))
            return result[:1000]
        except Exception as e:
            return f"Error: {e}"

    def _check_permission(self, tool: str, args: Dict) -> bool:
        """Check if tool execution is allowed."""
        from ..config.config import PermissionMode
        mode = self.config.permission_mode

        if mode == PermissionMode.NEVER:
            return False
        if mode == PermissionMode.AUTO:
            return True
        if mode == PermissionMode.ACCEPT_EDITS and tool in ["write_file", "edit_file"]:
            return True

        # ASK mode - prompt user
        from rich.prompt import Confirm
        console = Console()

        if tool == "execute_command":
            cmd = args.get("command", "")
            console.print(f"\n[bold yellow]? Execute:[/bold yellow] {cmd}")
        elif tool in ["write_file", "edit_file"]:
            path = args.get("path", "")
            console.print(f"\n[bold yellow]? {tool.replace('_', ' ').title()}:[/bold yellow] {path}")
        else:
            console.print(f"\n[bold yellow]? Use tool:[/bold yellow] {tool}")

        return Confirm.ask("Allow", default=False)