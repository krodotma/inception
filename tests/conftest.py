"""
Test configuration and fixtures for Inception test suite.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_db_path():
    """Provide temporary database path."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp) / "test.lmdb"


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton state between tests."""
    yield
    # Cleanup after test
