"""Tool registry for managing available tools."""

from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass
import inspect


@dataclass
class Tool:
    """Definition of a tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


class ToolRegistry:
    """Registry of available tools."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, Tool] = {}
            cls._instance._load_builtin_tools()
        return cls._instance

    def _load_builtin_tools(self):
        """Load built-in tools."""
        from . import implementations

        self.register("read_file", Tool(
            name="read_file",
            description="Read the contents of a file",
            parameters={"path": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}},
            function=implementations.read_file
        ))

        self.register("write_file", Tool(
            name="write_file",
            description="Create or overwrite a file",
            parameters={"path": {"type": "string"}, "content": {"type": "string"}},
            function=implementations.write_file
        ))

        self.register("edit_file", Tool(
            name="edit_file",
            description="Edit an existing file",
            parameters={"path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}},
            function=implementations.edit_file
        ))

        self.register("execute_command", Tool(
            name="execute_command",
            description="Execute a shell command",
            parameters={"command": {"type": "string"}},
            function=implementations.execute_command
        ))

        self.register("glob_search", Tool(
            name="glob_search",
            description="Search files by pattern",
            parameters={"pattern": {"type": "string"}},
            function=implementations.glob_search
        ))

        self.register("grep_search", Tool(
            name="grep_search",
            description="Search file contents",
            parameters={"pattern": {"type": "string"}, "path": {"type": "string"}},
            function=implementations.grep_search
        ))

        self.register("list_directory", Tool(
            name="list_directory",
            description="List directory contents",
            parameters={"path": {"type": "string"}},
            function=implementations.list_directory
        ))

        self.register("web_search", Tool(
            name="web_search",
            description="Search the web",
            parameters={"query": {"type": "string"}},
            function=implementations.web_search
        ))

        self.register("web_fetch", Tool(
            name="web_fetch",
            description="Fetch content from a URL",
            parameters={"url": {"type": "string"}},
            function=implementations.web_fetch
        ))

        self.register("ask_user", Tool(
            name="ask_user",
            description="Ask the user for input",
            parameters={"question": {"type": "string"}},
            function=implementations.ask_user
        ))

        self.register("spawn_subagent", Tool(
            name="spawn_subagent",
            description="Spawn a subagent for parallel work",
            parameters={"task": {"type": "string"}, "agent_id": {"type": "string"}},
            function=implementations.spawn_subagent
        ))

    def register(self, name: str, tool: Tool):
        """Register a tool."""
        self._tools[name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        """Check if a tool exists."""
        return name in self._tools

    def __getitem__(self, name: str) -> Callable:
        """Get the tool function."""
        tool = self._tools.get(name)
        if tool:
            return tool.function
        raise KeyError(f"Tool {name} not found")

    def list_tools(self) -> Dict[str, Tool]:
        """List all tools."""
        return dict(self._tools)

    def get_spec(self, tool_name: Optional[str] = None) -> Dict:
        """Get tool specifications for LLM."""
        if tool_name:
            tool = self._tools.get(tool_name)
            if tool:
                return {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": tool.parameters,
                            "required": list(tool.parameters.keys())
                        }
                    }
                }
            return {}

        return {
            "type": "object",
            "properties": {
                name: {
                    "type": "object",
                    "description": tool.description,
                    "properties": tool.parameters
                }
                for name, tool in self._tools.items()
            }
        }