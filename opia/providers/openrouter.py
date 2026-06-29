"""OpenRouter provider implementation."""
import httpx
from typing import Optional

from opia.providers.base import BaseProvider, Message, ChatResponse, ModelInfo, EmbeddingsResponse


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    supports_streaming = True
    supports_oauth = False

    def __init__(self, name: str = "openrouter", base_url: str = "https://openrouter.ai/api/v1"):
        self.name = name
        self.base_url = base_url
        self._default_model = "openai/gpt-4o"

    async def validate_credentials(self, credential: str) -> bool:
        headers = {
            "Authorization": f"Bearer {credential}",
            "HTTP-Referer": "https://opia.ai",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get(f"{self.base_url}/auth/key", headers=headers)
                return r.status_code == 200
            except Exception:
                return False

    async def authenticate(self, credential: str) -> bool:
        return await self.validate_credentials(credential)

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id=self._default_model, name=self._default_model, provider=self.name)]

    async def chat(self, messages: list[Message], model: str, **kwargs) -> ChatResponse:
        cred = kwargs.pop("credential", None)
        headers = {
            "Authorization": f"Bearer {cred or ''}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )
            if r.status_code == 401:
                raise RuntimeError("Invalid OpenRouter API key")
            r.raise_for_status()
            data = r.json()
            return ChatResponse(
                content=data["choices"][0]["message"]["content"],
                model=data.get("model", model),
                provider=self.name,
                usage=data.get("usage", {}),
                finish_reason=data["choices"][0].get("finish_reason"),
            )

    async def embeddings(self, input, model: str, **kwargs) -> EmbeddingsResponse:
        raise NotImplementedError("OpenRouter embeddings require a specific model")
