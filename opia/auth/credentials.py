"""Credential model and resolution logic."""
from dataclasses import dataclass
from typing import Optional

from opia.config.loader import load_providers_config

_CONFIG = None

def _get_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = load_providers_config()
    return _CONFIG


@dataclass
class CredentialInfo:
    """Resolved credential info for a provider."""
    provider: str
    keyring_service: str
    env_var: str
    key: Optional[str] = None
    source: Optional[str] = None  # "keyring", "file", "env", or None

    @classmethod
    def for_provider(cls, provider_name: str) -> Optional["CredentialInfo"]:
        config = _get_config()
        provider_cfg = config.providers.get(provider_name)
        if not provider_cfg:
            return None
        return cls(
            provider=provider_name,
            keyring_service=provider_cfg.keyring_service,
            env_var=provider_cfg.env_var,
        )
