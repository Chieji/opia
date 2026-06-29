"""Anthropic provider implementation."""
import httpx
from typing import Optional

from opia.providers.base import BaseProvider, Message, ChatResponse, ModelInfo, EmbeddingsResponse


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    base_url = "https://api.anthropic.com/v1"
    supports_streaming = True
    supports_oauth = False

    def __init__(self, name: str = "anthropic", base_url: str = "https://api.anthropic.com/v1"):
        self.name = name
        self.base_url = base_url
        self._default_model = "claude-3-opus-20240229"

    async def validate_credentials(self, credential: str) -> bool:
        headers = {
            "x-api-key": credential,
            "anthropic-version": "2023-06-01",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get(f"{self.base_url}/messages", headers=headers)
                return r.status_code in (200, 400)
            except Exception:
                return False

    async def authenticate(self, credential: str) -> bool:
        return await self.validate_credentials(credential)

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id=self._default_model, name=self._default_model, provider=self.name)]

    async def chat(self, messages: list[Message], model: str, **kwargs) -> ChatResponse:
        cred = kwargs.pop("credential", None)
        system = kwargs.pop("system", None)
        headers = {
            "x-api-key": cred or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {"model": model or self._default_model, "max_tokens": kwargs.get("max_tokens", 1024)}
        if system:
            payload["system"] = system
        payload["messages"] = [{"role": m.role, "content": m.content} for m in messages]
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/messages", headers=headers, json=payload
            )
            if r.status_code == 401:
                raise RuntimeError("Invalid Anthropic API key")
            r.raise_for_status()
            data = r.json()
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")
            return ChatResponse(
                content=content,
                model=data.get("model", model),
                provider=self.name,
                usage=data.get("usage", {}),
                finish_reason=data["stop_reason"],
            )

    async def embeddings(self, input, model: str, **kwargs) -> EmbeddingsResponse:
        raise NotImplementedError("Anthropic provider does not support embeddings yet")
