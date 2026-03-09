"""Utility helpers."""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt
from dotenv import load_dotenv

console = Console()


def get_api_key(interactive: bool = True) -> Optional[str]:
    """Get NVIDIA API key from environment, .env, or prompt."""
    # Try environment first
    key = os.getenv("NVIDIA_API_KEY")
    if key:
        return key

    # Try .env file
    load_dotenv()
    key = os.getenv("NVIDIA_API_KEY")
    if key:
        return key

    # Try config file
    config_dir = Path.home() / ".nv-cli-config"
    config_file = config_dir / "config.json"
    if config_file.exists():
        import json
        try:
            config = json.loads(config_file.read_text())
            key = config.get("api_key")
            if key:
                return key
        except Exception:
            pass

    if not interactive:
        return None

    # Prompt user
    console.print("[yellow]NVIDIA_API_KEY not found[/yellow]")
    if console.input("Open browser to get API key? [Y/n]: ").lower() != "n":
        import webbrowser
        webbrowser.open("https://build.nvidia.com/explore")

    key = Prompt.ask("Enter NVIDIA API Key", password=True)

    if key:
        # Save for future use
        os.environ["NVIDIA_API_KEY"] = key
        # Optionally save to config
        if Prompt.ask("Save to config?", default=False):
            config_dir.mkdir(parents=True, exist_ok=True)
            config = {"api_key": key}
            config_file.write_text(json.dumps(config, indent=2))

    return key if key.startswith("nvapi-") else None


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    import logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def truncate_string(s: str, max_len: int, suffix: str = "...") -> str:
    """Truncate string to max length."""
    if len(s) <= max_len:
        return s
    return s[:max_len - len(suffix)] + suffix