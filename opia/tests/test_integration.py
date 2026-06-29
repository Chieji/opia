"""Integration tests across Auth, Router, and Plugin stubs."""
import pytest
from opia.core.orchestrator import OpiaOrchestrator
from opia.providers.base import Message


class TestOrchestrator:
    def test_orchestrator_instantiates(self, orch):
        assert orch.auth is not None
        assert orch.router is not None
        assert orch.models is not None

    @pytest.mark.asyncio
    async def test_discover_providers(self, orch, mock_env_credentials):
        providers = await orch.discover_providers()
        assert len(providers) >= 9
        names = [p.name for p in providers]
        assert "groq" in names
        assert "openai" in names

    def test_list_tools_stubs(self, orch):
        tools = orch.list_tools()
        assert isinstance(tools, list)
        # Should be empty until Codex builds the plugin system

    def test_list_plugins_stubs(self, orch):
        plugins = orch.list_plugins()
        assert isinstance(plugins, list)
        # Should be empty until Codex builds the plugin system


class TestConfigPersistence:
    def test_config_file_created(self, opia_dir):
        from opia.cli.config import _load_config, _set_nested, _save_config
        config = _load_config()
        _set_nested(config, "provider.default", "groq")
        _save_config(config)
        config_file = opia_dir / "config.toml"
        assert config_file.exists()


class TestProviderRegistry:
    def test_all_providers_registered(self):
        from opia.providers.registry import list_providers
        names = list_providers()
        expected = ["openai", "anthropic", "groq", "mistral", "openrouter", "gemini", "fireworks", "together", "deepseek"]
        for p in expected:
            assert p in names, f"Provider {p} not registered"


class TestAuthManager:
    @pytest.mark.asyncio
    async def test_auth_manager_whoami(self, orch):
        info = orch.auth.whoami()
        assert info["status"] == "anonymous"
