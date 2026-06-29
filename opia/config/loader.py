"""Config loader for Opia provider configuration."""
import os
from pathlib import Path

import yaml
from pydantic import BaseModel


class ProviderConfig(BaseModel):
    name: str
    base_url: str
    auth_type: str
    env_var: str
    keyring_service: str
    default_model: str
    supports_oauth: bool = False


class ProvidersConfig(BaseModel):
    providers: dict[str, ProviderConfig]


def load_providers_config() -> ProvidersConfig:
    """Load providers.yaml from package root or cwd."""
    search_paths = [
        Path(__file__).parent.parent / "config" / "providers.yaml",
        Path("config") / "providers.yaml",
        Path("opia") / "config" / "providers.yaml",
    ]
    for path in search_paths:
        if path.exists():
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            providers = {
                k: ProviderConfig(**v) for k, v in data.get("providers", {}).items()
            }
            return ProvidersConfig(providers=providers)
    raise FileNotFoundError("providers.yaml not found in any search path")
