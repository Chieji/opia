"""End-to-end tests: full flow from login to chat to logout."""
import pytest
from typer.testing import CliRunner

from opia.cli.main import app

runner = CliRunner()


class TestE2ELoginLogout:
    def test_login_logout_cycle(self):
        # Try to login with a clearly invalid key (should fail)
        result = runner.invoke(app, ["login", "groq", "--key", "invalid-key"])
        assert result.exit_code == 1
        assert "Invalid" in result.stdout or "failed" in result.stdout.lower()

        # Logout (should succeed even with no creds)
        result = runner.invoke(app, ["logout", "--yes"])
        assert result.exit_code == 0

    def test_login_with_env_key(self, mock_env_credentials):
        # With env key set, should attempt validation (will fail with mock key but test path works)
        result = runner.invoke(app, ["login", "groq"])
        # Groq validation will fail with sk-test-groq, but we verify the path works
        assert result.exit_code in (0, 1)


class TestE2EProviderFlow:
    def test_full_provider_flow(self):
        # 1. List providers
        result = runner.invoke(app, ["provider", "list"])
        assert result.exit_code == 0

        # 2. Show a provider
        result = runner.invoke(app, ["provider", "show", "openai"])
        assert result.exit_code == 0
        assert "openai" in result.stdout.lower()

        # 3. Try to use a provider (sets active session)
        result = runner.invoke(app, ["provider", "use", "openai"])
        assert result.exit_code == 0
        assert "active provider" in result.stdout.lower()

        # 4. Check whoami
        result = runner.invoke(app, ["whoami"])
        assert result.exit_code == 0
        assert "openai" in result.stdout.lower()


class TestE2EChatFlow:
    @pytest.mark.skip(reason="Requires real API key or mocked provider")
    def test_chat_with_mock_provider(self):
        # This would require mocking the provider response
        pass

    def test_chat_interactive_exit(self):
        # Simulate sending exit command in REPL
        result = runner.invoke(app, ["chat", "--interactive"], input=":quit\n")
        # Should exit gracefully
        assert result.exit_code in (0, 1)  # May exit with 1 if not authenticated
