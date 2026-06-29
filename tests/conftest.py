"""Shared test fixtures for Opia."""
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _tmp_home(monkeypatch):
    """Redirect home to a temp directory for all tests."""
    tmp = tempfile.mkdtemp(prefix="opia_test_")
    monkeypatch.setenv("HOME", tmp)
    monkeypatch.setenv("USERPROFILE", tmp)
    monkeypatch.setenv("XDG_CONFIG_HOME", os.path.join(tmp, ".config"))
    monkeypatch.delenv("OPIA_MASTER_KEY", raising=False)
    yield tmp


@pytest.fixture
def opia_dir(_tmp_home):
    """Return the ~/.opia directory inside the temp home."""
    d = Path(_tmp_home) / ".opia"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def mock_env_credentials(monkeypatch):
    """Set fake env credentials for provider testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("GROQ_API_KEY", "sk-test-groq")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic")


@pytest.fixture
def orch():
    """Create a fresh OpiaOrchestrator."""
    from opia.core.orchestrator import OpiaOrchestrator
    return OpiaOrchestrator()
