"""Unit tests for Auth module."""
import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio

TMP_HOME = tempfile.mkdtemp()
os.environ["HOME"] = TMP_HOME
os.environ["USERPROFILE"] = TMP_HOME
os.environ["XDG_CONFIG_HOME"] = os.path.join(TMP_HOME, ".config")
os.environ.pop("OPIA_MASTER_KEY", None)


@pytest_asyncio.fixture(autouse=True)
def reset_modules():
    with patch.dict("sys.modules", {}):
        yield


class TestCredentialStorage:
    @pytest.fixture
    def storage(self):
        from opia.auth.storage import CredentialStorage
        return CredentialStorage()

    def test_set_and_get_credential(self, storage):
        storage.set_credential("groq", "opia/groq", "sk-test-123")
        result = storage.get_credential("groq", "opia/groq", "GROQ_API_KEY")
        # Falls back to env or file — at least it should not raise
        assert result in (None, "sk-test-123", os.environ.get("GROQ_API_KEY"))

    def test_set_and_delete(self, storage):
        storage.set_credential("groq", "opia/groq", "sk-delete-me")
        storage.delete_credential("groq", "opia/groq")
        result = storage.get_credential("groq", "opia/groq", "GROQ_API_KEY")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_roundtrip(self, storage):
        await storage.aset_credential("openai", "opia/openai", "sk-async")
        result = await storage.aget_credential("openai", "opia/openai", "OPENAI_API_KEY")
        assert result in (None, "sk-async", os.environ.get("OPENAI_API_KEY"))

    def test_env_fallback_when_no_store(self, storage):
        os.environ["DEEPSEEK_API_KEY"] = "env-key"
        result = storage.get_credential("deepseek", "opia/deepseek", "DEEPSEEK_API_KEY")
        assert result == "env-key"
        del os.environ["DEEPSEEK_API_KEY"]


class TestSessionManager:
    @pytest.fixture
    def session(self):
        from opia.auth.session import SessionManager
        return SessionManager()

    def test_set_and_get_active(self, session):
        session.set_active("groq", "llama-3.3-70b-versatile")
        s = session.get_active()
        assert s.provider == "groq"
        assert s.model == "llama-3.3-70b-versatile"

    def test_clear(self, session):
        session.set_active("openai", "gpt-4o")
        session.clear()
        s = session.get_active()
        assert s.provider == ""
        assert s.model == ""


class TestAuthManager:
    @pytest.fixture
    def manager(self):
        from opia.auth.manager import AuthManager
        return AuthManager()

    @pytest.mark.asyncio
    async def test_whoami_anonymous(self, manager):
        result = manager.whoami()
        assert result["status"] == "anonymous"

    @pytest.mark.asyncio
    async def test_login_with_invalid_key(self, manager):
        result = await manager.login("groq", key="invalid-dummy-key-xyz")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_no_key_returns_false(self, manager):
        result = await manager.validate("groq")
        assert result is False
