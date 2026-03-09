"""Soul and Identity system for nv_cli.

The Soul/Identity system is file-based personality management.
Files are human-editable and re-read each session for continuity.
"""

from .soul import SoulManager, Identity
from .templates import DEFAULT_SOUL, DEFAULT_IDENTITY

__all__ = [
    "SoulManager",
    "Identity",
    "DEFAULT_SOUL",
    "DEFAULT_IDENTITY",
]