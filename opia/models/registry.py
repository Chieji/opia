"""Model registry with 1-hour TTL cache."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import asyncio

from opia.models.base import ModelInfo
from opia.models.discovery import discover_models
from opia.providers.base import ProviderInfo

OPIA_DIR = Path.home() / ".opia"
MODELS_CACHE = OPIA_DIR / "models_cache.json"
CACHE_TTL = 3600  # 1 hour in seconds


class ModelRegistry:
    """Cache models with TTL expiry."""

    def __init__(self):
        OPIA_DIR.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, tuple[datetime, list[ModelInfo]]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if not MODELS_CACHE.exists():
            return
        try:
            with open(MODELS_CACHE, "r") as f:
                data = json.load(f)
            now = datetime.now(timezone.utc)
            for provider, entry in data.items():
                ts = datetime.fromisoformat(entry["timestamp"])
                age = (now - ts).total_seconds()
                if age < CACHE_TTL:
                    items = [ModelInfo(**m) for m in entry["models"]]
                    self._cache[provider] = (ts, items)
        except Exception:
            pass

    def _save_cache(self) -> None:
        data: dict = {}
        for provider, (ts, models) in self._cache.items():
            data[provider] = {
                "timestamp": ts.isoformat(),
                "models": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "provider": m.provider,
                        "context_length": m.context_length,
                        "supports_streaming": m.supports_streaming,
                        "supports_vision": m.supports_vision,
                        "metadata": m.metadata,
                    }
                    for m in models
                ],
            }
        with open(MODELS_CACHE, "w") as f:
            json.dump(data, f, indent=2)

    async def discover_models(self, provider: str) -> list[ModelInfo]:
        """Discover models for a provider, using cache if fresh."""
        provider = provider.lower()
        cached = self._cache.get(provider)
        if cached:
            ts, models = cached
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            if age < CACHE_TTL:
                return models
        models = await discover_models(provider)
        self._cache[provider] = (datetime.now(timezone.utc), models)
        self._save_cache()
        return models

    async def list_models(self) -> list[ModelInfo]:
        """Return all cached models across all configured providers."""
        all_models: list[ModelInfo] = []
        for provider in self._cache:
            all_models.extend(self._cache[provider][1])
        return all_models

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        for _, (_, models) in self._cache.items():
            for m in models:
                if m.id == model_id:
                    return m
        return None

    def clear(self) -> None:
        self._cache.clear()
        if MODELS_CACHE.exists():
            MODELS_CACHE.unlink()
