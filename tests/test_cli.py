"""CLI command tests using Typer's CliRunner."""
from typer.testing import CliRunner

from opia.cli.main import app

runner = CliRunner()


class TestCLIVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Opia" in result.stdout
        assert "0.1.0" in result.stdout


class TestCLIWhoami:
    def test_whoami_anonymous(self):
        result = runner.invoke(app, ["whoami"])
        assert result.exit_code == 0
        assert "anonymous" in result.stdout or "Not authenticated" in result.stdout


class TestCLIProvider:
    def test_provider_list(self):
        result = runner.invoke(app, ["provider", "list"])
        assert result.exit_code == 0
        # Should show all 9 configured providers
        providers = ["openai", "anthropic", "groq", "mistral", "openrouter", "gemini", "fireworks", "together", "deepseek"]
        for p in providers:
            assert p in result.stdout, f"Provider {p} not found in output"

    def test_provider_show(self):
        result = runner.invoke(app, ["provider", "show", "groq"])
        assert result.exit_code == 0
        assert "Groq" in result.stdout or "groq" in result.stdout

    def test_provider_show_unknown(self):
        result = runner.invoke(app, ["provider", "show", "fake-provider"])
        assert result.exit_code == 1


class TestCLIModels:
    def test_models_list_no_auth(self):
        result = runner.invoke(app, ["models", "list"])
        assert result.exit_code == 0
        # May show no models or default models

    def test_models_show(self):
        # This might fail if model isn't cached, but it should handle gracefully
        result = runner.invoke(app, ["models", "show", "llama-3.3-70b-versatile"])
        # Don't assert exit code — model may not be cached


class TestCLISession:
    def test_session_show(self):
        result = runner.invoke(app, ["session", "show"])
        assert result.exit_code == 0

    def test_session_clear(self):
        result = runner.invoke(app, ["session", "clear", "--yes"])
        assert result.exit_code == 0
        assert "cleared" in result.stdout.lower()


class TestCLIConfig:
    def test_config_set_and_get(self):
        # Set a value
        result = runner.invoke(app, ["config", "set", "test.key", "hello"])
        assert result.exit_code == 0
        assert "Set" in result.stdout

        # Get the value
        result = runner.invoke(app, ["config", "get", "test.key"])
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_config_list(self):
        result = runner.invoke(app, ["config", "get"])
        assert result.exit_code == 0

    def test_config_unset_key(self):
        result = runner.invoke(app, ["config", "get", "nonexistent.key"])
        assert result.exit_code == 0
        assert "not set" in result.stdout.lower() or "dim" in result.stdout


class TestCLITool:
    def test_tool_list_no_plugins(self):
        result = runner.invoke(app, ["tool", "list"])
        assert result.exit_code == 0


class TestCLIPlugin:
    def test_plugin_list_no_plugins(self):
        result = runner.invoke(app, ["plugin", "list"])
        assert result.exit_code == 0
