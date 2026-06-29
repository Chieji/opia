"""
Opia Plugin Ecosystem

The execution engine that makes Opia an agent rather than just a chat client.
"""

__version__ = "1.0.0"

from .base import BaseTool, ToolResult, ToolMetadata
from .registry import PluginRegistry
from .manager import PluginManager
from .sandbox import Sandbox

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolMetadata",
    "PluginRegistry",
    "PluginManager",
    "Sandbox",
]
"