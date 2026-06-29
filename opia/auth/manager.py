"""AuthManager — login/logout/validate/whoami."""
from typing import Optional

from opia.auth.credentials import CredentialInfo
from opia.auth.storage import CredentialStorage
from opia.auth.session import SessionManager, ActiveSession
from opia.config.loader import load_providers_config

_CONFIG = None


def _get_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = load_providers_config()
    return _CONFIG


class AuthManager:
    """Orchestrates login, logout, validation, and session tracking."""

    def __init__(self):
        self._storage = CredentialStorage()
        self._session = SessionManager()
        self._providers = {k: v for k, v in _get_config().providers.items()}

    async def login(self, provider: str, key: Optional[str] = None) -> bool:
        """Validate and store credentials for a provider."""
        info = CredentialInfo.for_provider(provider)
        if not info:
            raise ValueError(f"Unknown provider: {provider}")

        credential = key or info.key
        if not credential:
            raise ValueError(f"No credential provided for {provider}")

        # Get provider instance and validate
        from opia.providers.registry import get_provider
        prov = get_provider(provider)
        valid = await asyncio_wrap(prov.validate_credentials, credential)
        if not valid:
            return False

        stored = self._storage.set_credential(
            provider, info.keyring_service, credential
        )
        if stored:
            provider_cfg = self._providers[provider]
            default_model = provider_cfg.default_model if provider_cfg else ""
            self._session.set_active(provider, default_model)
        return stored

    async def logout(self, provider: Optional[str] = None) -> None:
        """Remove credentials (all if no provider specified)."""
        targets = [provider] if provider else list(self._providers.keys())
        for name in targets:
            info = CredentialInfo.for_provider(name)
            if info:
                self._storage.delete_credential(name, info.keyring_service)
        if not provider:
            self._session.clear()

    async def validate(self, provider: str) -> bool:
        """Test credentials against provider API."""
        info = CredentialInfo.for_provider(provider)
        if not info:
            return False
        cred = await self._storage.aget_credential(
            provider, info.keyring_service, info.env_var
        )
        if not cred:
            return False
        from opia.providers.registry import get_provider
        prov = get_provider(provider)
        return await asyncio_wrap(prov.validate_credentials, cred)

    def whoami(self) -> dict:
        session = self._session.get_active()
        if not session or not session.provider:
            return {"status": "anonymous", "provider": None, "model": None}
        session_dict = {
            "provider": session.provider,
            "model": session.model,
            "auth_status": session.auth_status,
            "last_used": session.last_used,
            "created_at": session.created_at,
        }
        return session_dict


def asyncio_wrap(func, *args, **kwargs):
    """Run an async/callable function safely."""
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return func(*args, **kwargs)
    return asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs))
