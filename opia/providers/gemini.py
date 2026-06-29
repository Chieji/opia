"""Gemini provider implementation."""
import httpx
from typing import Optional

from opia.providers.base import BaseProvider, Message, ChatResponse, ModelInfo, EmbeddingsResponse


class GeminiProvider(BaseProvider):
    name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    supports_streaming = True
    supports_oauth = False

    def __init__(self, name: str = "gemini", base_url: str = "https://generativelanguage.googleapis.com/v1beta"):
        self.name = name
        self.base_url = base_url
        self._default_model = "gemini-2.0-flash"

    async def validate_credentials(self, credential: str) -> bool:
        url = f"{self.base_url}/models?key={credential}"
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get(url)
                return r.status_code == 200
            except Exception:
                return False

    async def authenticate(self, credential: str) -> bool:
        return await self.validate_credentials(credential)

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id=self._default_model, name=self._default_model, provider=self.name)]

    async def chat(self, messages: list[Message], model: str, **kwargs) -> ChatResponse:
        cred = kwargs.pop("credential", None)
        model_id = model or self._default_model
        url = f"{self.base_url}/models/{model_id}:generateContent?key={cred}"
        contents = []
        for m in messages:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})
        payload = {"contents": contents, **kwargs}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json=payload)
            if r.status_code == 401:
                raise RuntimeError("Invalid Gemini API key")
            r.raise_for_status()
            data = r.json()
            text = ""
            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    text += part.get("text", "")
            return ChatResponse(
                content=text,
                model=model_id,
                provider=self.name,
                usage=data.get("usageMetadata", {}),
            )

    async def embeddings(self, input, model: str, **kwargs) -> EmbeddingsResponse:
        cred = kwargs.pop("credential", None)
        model_id = model or self._default_model
        url = f"{self.base_url}/models/{model_id}:batchEmbedContents?key={cred}"
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json={"requests": [{"content": {"parts": [{"text": x}]}} for x in input]})
            r.raise_for_status()
            data = r.json()
            return EmbeddingsResponse(
                embeddings=[e["values"] for e in data.get("embeddings", [])],
                model=model_id,
                provider=self.name,
            )
