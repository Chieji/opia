"""Unit tests for Opia Authentication & Provider System."""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio

# Set up a temporary home for tests
TMP_HOME = tempfile.mkdtemp()
os.environ["HOME"] = TMP_HOME
os.environ["USERPROFILE"] = TMP_HOME
os.environ["XDG_CONFIG_HOME"] = os.path.join(TMP_HOME, ".config")


# ─── fixtures ─────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(autouse=True)
def reset_global_config():
    """Reset module-level caches between tests."""
    with patch.dict("sys.modules", {}):
        yield
    # Ensure no leakage
    for mod in list(sys.modules.keys()):
        if mod.startswith("opia."):
            del sys.modules[mod]


# ─── BaseProvider tests ────────────────────────────────────────────────────


class TestBaseProvider:
    def test_abstract_methods_exist(self):
        from opia.providers.base import BaseProvider
        import inspect
        abstract_methods = {
            name for name, method in inspect.getmembers(BaseProvider, predicate=inspect.isfunction)
            if getattr(method, "__isabstractmethod__", False)
        }
        expected = {"authenticate", "list_models", "chat", "embeddings", "validate_credentials"}
        assert expected == abstract_methods

    def test_dataclasses(self):
        from opia.providers.base import Message, ChatResponse, ModelInfo, EmbeddingsResponse
        msg = Message(role="user", content="hi")
        assert msg.role == "user"
        assert msg.content == "hi"
        resp = ChatResponse(content="hello", model="g", provider="p", usage={"tokens": 1})
        assert resp.usage["tokens"] == 1
        info = ModelInfo(id="m", name="M", provider="p")
        assert info.context_length == 4096


# ─── Provider impl tests ───────────────────────────────────────────────────


class TestOpenAIProvider:
    @pytest.fixture
    def provider(self):
        from opia.providers.openai import OpenAIProvider
        return OpenAIProvider()

    @pytest.mark.asyncio
    async def test_validate_credentials_invalid(self, provider):
        assert not await provider.validate_credentials("bad-key")

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        models = await provider.list_models()
        assert len(models) >= 1
        assert models[0].provider == "openai"

    @pytest.mark.asyncio
    async def test_chat_invalid_key(self, provider):
        from opia.providers.base import Message
        with pytest.raises((RuntimeError, Exception)):
            await provider.chat(
                [Message(role="user", content="hi")],
                model="gpt-4o",
                credential="bad",
            )


class TestGroqProvider:
    @pytest.fixture
    def provider(self):
        from opia.providers.groq import GroqProvider
        return GroqProvider()

    @pytest.mark.asyncio
    async def test_validate_false_on_bad(self, provider):
        assert not await provider.validate_credentials("bad-key")

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        models = await provider.list_models()
        assert any(m.id == "llama-3.3-70b-versatile" for m in models)


# ─── Provider Registry tests ───────────────────────────────────────────────


class TestProviderRegistry:
    @pytest.mark.asyncio
    async def test_list_providers_has_nine(self):
        from opia.providers import list_providers
        provs = list_providers()
        assert len(provs) == 9

    @pytest.mark.asyncio
    async def test_get_provider(self):
        from opia.providers import get_provider
        prov = get_provider("groq")
        assert prov.name == "groq"

    @pytest.mark.asyncio
    async def test_get_provider_invalid(self):
        from opia.providers import get_provider
        with pytest.raises(ValueError):
            get_provider("nonexistent")

    @pytest.mark.asyncio
    async def test_discover_available(self):
        from opia.providers.registry import discover_available
        results = await discover_available()
        assert len(results) == 9
        # No real keys, so all should show has_credentials=False (or dependent on env)
        for r in results:
            assert hasattr(r, "has_credentials")
