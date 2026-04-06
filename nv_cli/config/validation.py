"""Configuration validation."""

from typing import Dict, Any, List

def validate_config(data: Dict[str, Any]) -> List[str]:
    """Validate configuration data."""
    errors = []

    # Check version
    if "version" not in data:
        errors.append("Missing 'version' field")

    # Validate agents
    agents = data.get("agents", [])
    if not isinstance(agents, list):
        errors.append("'agents' must be a list")
    else:
        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                errors.append(f"Agent {i} must be an object")
                continue
            if "id" not in agent:
                errors.append(f"Agent {i} missing 'id' field")

    return errors