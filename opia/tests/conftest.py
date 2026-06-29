"""Pytest configuration."""
import asyncio
import sys
import pytest


# Configure pytest-asyncio event loop
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()
