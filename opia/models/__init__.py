"""Model registry and discovery."""
from opia.models.registry import ModelRegistry
from opia.models.discovery import discover_models
from opia.models.base import ModelInfo

__all__ = ["ModelRegistry", "discover_models", "ModelInfo"]
