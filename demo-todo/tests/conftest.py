"""
Pytest configuration file for the TODO API tests.
Handles fixture setup and pytest-asyncio configuration.
"""

import pytest
from app import db


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the in-memory database before each test."""
    db.reset_db()
    yield
    db.reset_db()


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register async marker
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async (deselect with '-m \"not asyncio\"')"
    )
