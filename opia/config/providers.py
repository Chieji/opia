from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


class ProviderConfigData(BaseModel):
    name: str
    base_url: str
    auth_type: str = "api_key"
    env_var: Optional[str] = None
    keyring_service: Optional[str] = None
    default_model: Optional[str] = None
    supports_streaming: bool = True
    supports_vision: bool = False


class ProvidersConfig(BaseModel):
    providers: dict[str, ProviderConfigData]


@dataclass
class ProviderConfig:
    """Runtime provider configuration loaded from providers.yaml."""
    name: str
    base_url: str
    auth_type: str
    env_var: Optional[str]
    keyring_service: Optional[str]
    default_model: Optional[str]
    supports_streaming: bool
    supports_vision: bool


def _load_config(path: Optional[str] = None) -> ProvidersConfig:
    import yaml
    from pathlib import Path

    if path is None:
        path = str(Path(__file__).parent.parent / "config" / "providers.yaml")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return ProvidersConfig.model_validate(data)


_config: Optional[ProvidersConfig] = None


def get_config(path: Optional[str] = None) -> ProvidersConfig:
    global _config
    if _config is None:
        _config = _load_config(path)
    return _config


def get_provider_config(provider: str) -> Optional[ProviderConfig]:
    cfg = get_config()
    data = cfg.providers.get(provider)
    if not data:
        return None
    return ProviderConfig(
        name=data.name,
        base_url=data.base_url,
        auth_type=data.auth_type,
        env_var=data.env_var,
        keyring_service=data.keyring_service,
        default_model=data.default_model,
        supports_streaming=data.supports_streaming,
        supports_vision=data.supports_vision,
    )


def list_provider_names() -> list[str]:
    return list(get_config().providers.keys())
