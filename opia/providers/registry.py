"""Provider registry with credential-aware discovery."""
from typing import Optional

from opia.config.loader import load_providers_config
from opia.providers.base import BaseProvider, ProviderInfo
from opia.auth.credentials import CredentialInfo
from opia.auth.storage import CredentialStorage

_PROVIDER_CLASSES = {}


def register_provider(name: str, cls):
    """Register a provider class."""
    _PROVIDER_CLASSES[name] = cls


def get_provider(name: str) -> BaseProvider:
    """Return a provider instance by name."""
    config = load_providers_config()
    if name not in config.providers:
        raise ValueError(f"Unknown provider: {name}")
    cfg = config.providers[name]
    cls = _PROVIDER_CLASSES.get(name)
    if not cls:
        raise ValueError(f"Provider class not registered for: {name}")
    return cls(name=name, base_url=cfg.base_url)


def list_providers() -> list[str]:
    return sorted(_PROVIDER_CLASSES.keys())


async def discover_available() -> list[ProviderInfo]:
    """Check which providers have valid credentials configured."""
    import asyncio
    config = load_providers_config()
    storage = CredentialStorage()
    results: list[ProviderInfo] = []
    for name, cfg in config.providers.items():
        cred = storage.get_credential(name, cfg.keyring_service, cfg.env_var)
        has_cred = cred is not None and len(cred.strip()) > 0
        results.append(ProviderInfo(
            name=name,
            display_name=cfg.name,
            base_url=cfg.base_url,
            default_model=cfg.default_model,
            has_credentials=has_cred,
            supports_oauth=cfg.supports_oauth,
        ))
    return results
