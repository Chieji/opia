"""Unit tests for Router and Models."""
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import pytest_asyncio

TMP_HOME = tempfile.mkdtemp()
os.environ["HOME"] = TMP_HOME
os.environ["USERPROFILE"] = TMP_HOME
os.environ["XDG_CONFIG_HOME"] = os.path.join(TMP_HOME, ".config")


@pytest_asyncio.fixture(autouse=True)
def reset_modules():
    with patch.dict("sys.modules", {}):
        yield


class TestModelRegistry:
    @pytest.fixture
    def registry(self):
        from opia.models.registry import ModelRegistry
        return ModelRegistry()

    @pytest.mark.asyncio
    async def test_clear(self, registry):
        registry.clear()
        models = await registry.list_models()
        assert models == []

    def test_get_model_not_found(self, registry):
        result = registry.get_model("nonexistent-model")
        assert result is None


class TestRouter:
    @pytest.mark.asyncio
    async def test_chat_no_provider_raises(self):
        from opia.router.chat import UnifiedChatRouter
        router = UnifiedChatRouter()
        from opia.providers.base import Message
        with pytest.raises(ValueError):
            await router.chat([Message("user", "")])

    @pytest.mark.asyncio
    async def test_chat_invalid_provider_raises(self):
        from opia.router.chat import UnifiedChatRouter
        from opia.providers.base import Message
        router = UnifiedChatRouter()
        with pytest.raises(ValueError):
            await router.chat([Message("user", "")], provider="nonexistent")
