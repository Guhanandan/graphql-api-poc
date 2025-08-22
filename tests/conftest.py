# conftest.py

import pytest
import asyncio
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "base_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
        "auth_token": os.getenv("TEST_AUTH_TOKEN", "test-token"),
        "test_user_id": os.getenv("TEST_USER_ID", "test-user-123"),
        "timeout": int(os.getenv("TEST_TIMEOUT", "30"))
    }


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Add any cleanup logic here
    await asyncio.sleep(0.1)  # Small delay between tests