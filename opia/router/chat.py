"""UnifiedChatRouter — the single entry point for all chat requests."""
import asyncio
from typing import Optional, AsyncIterator

import httpx

from opia.providers.base import (
    BaseProvider, Message, ChatResponse, ChatChunk, ModelInfo
)
from opia.providers.registry import get_provider, list_providers, discover_available
from opia.auth.credentials import CredentialInfo
from opia.auth.storage import CredentialStorage
from opia.auth.session import SessionManager
from opia.config.loader import load_providers_config


class UnifiedChatRouter:
    """THE central gateway. No one talks to providers directly except this router."""

    def __init__(self):
        self._storage = CredentialStorage()
        self._session = SessionManager()
        self._config = load_providers_config()

    async def chat(
        self,
        messages: list[Message],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> ChatResponse | AsyncIterator[ChatChunk]:
        """Send a chat request with retries and provider resolution."""
        prov_name = provider or self._session.active_provider
        if not prov_name:
            raise ValueError("No provider specified and no active session")

        provider_cfg = self._config.providers.get(prov_name)
        if not provider_cfg:
            raise ValueError(f"Unknown provider: {prov_name}")

        cred_info = CredentialInfo.for_provider(prov_name)
        credential = None
        if cred_info:
            credential = await self._storage.aget_credential(
                prov_name, cred_info.keyring_service, cred_info.env_var
            )

        prov = get_provider(prov_name)
        resolved_model = model or provider_cfg.default_model
        chat_kwargs = {
            "temperature": temperature,
            "stream": stream,
            **kwargs,
        }
        if max_tokens:
            chat_kwargs["max_tokens"] = max_tokens
        if credential:
            chat_kwargs["credential"] = credential

        for attempt in range(3):
            try:
                if stream:
                    return prov.chat(messages, resolved_model, **chat_kwargs)
                return await asyncio_wrap(
                    prov.chat, messages, resolved_model, **chat_kwargs
                )
            except RuntimeError as e:
                if "Invalid" in str(e):
                    raise
                raise
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("Chat failed after 3 retries")


def asyncio_wrap(func, *args, **kwargs):
    """Execute async/callable function."""
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return func(*args, **kwargs)
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))
