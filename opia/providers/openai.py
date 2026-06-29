"""OpenAI provider implementation."""
import httpx
from typing import Optional

from opia.providers.base import BaseProvider, Message, ChatResponse, ModelInfo, EmbeddingsResponse


class OpenAIProvider(BaseProvider):
    name = "openai"
    base_url = "https://api.openai.com/v1"
    supports_streaming = True
    supports_oauth = False

    def __init__(self, name: str = "openai", base_url: str = "https://api.openai.com/v1"):
        self.name = name
        self.base_url = base_url
        self._default_model = "gpt-4o"

    async def validate_credentials(self, credential: str) -> bool:
        headers = {"Authorization": f"Bearer {credential}"}
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get(f"{self.base_url}/models", headers=headers)
                return r.status_code == 200
            except Exception:
                return False

    async def authenticate(self, credential: str) -> bool:
        return await self.validate_credentials(credential)

    async def list_models(self) -> list[ModelInfo]:
        from opia.config.loader import load_providers_config
        cfg = load_providers_config().providers["openai"]
        return [ModelInfo(id=cfg.default_model, name=cfg.default_model, provider=self.name)]

    async def chat(self, messages: list[Message], model: str, **kwargs) -> ChatResponse:
        headers = {}
        cred = kwargs.pop("credential", None)
        if cred:
            headers["Authorization"] = f"Bearer {cred}"
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
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
        headers = {}
        cred = kwargs.pop("credential", None)
        if cred:
            headers["Authorization"] = f"Bearer {cred}"
        payload = {"model": model, "input": input, **kwargs}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base_url}/embeddings", headers=headers, json=payload
            )
            r.raise_for_status()
            data = r.json()
            return EmbeddingsResponse(
                embeddings=[d["embedding"] for d in data["data"]],
                model=data.get("model", model),
                provider=self.name,
            )
