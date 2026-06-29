"""Model discovery — fetch models from provider APIs."""
import asyncio
from typing import Optional

from opia.providers.base import ModelInfo
from opia.providers.registry import get_provider


async def discover_models(provider_name: str) -> list[ModelInfo]:
    """Fetch available models for a specific provider."""
    from opia.config.loader import load_providers_config
    from opia.auth.storage import CredentialStorage
    storage = CredentialStorage()
    config = load_providers_config()
    cfg = config.providers.get(provider_name)
    if not cfg:
        raise ValueError(f"Unknown provider: {provider_name}")
    cred = storage.get_credential(provider_name, cfg.keyring_service, cfg.env_var)
    provider = get_provider(provider_name)
    kwargs = {}
    if cred:
        kwargs["credential"] = cred
    return await provider.list_models(**kwargs)
