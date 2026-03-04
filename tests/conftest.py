# tests/conftest.py
# Pytest configuration.
# - Registers the "integration" marker to skip integration tests when
#   the P4 backend (localhost:3001) is unreachable.
# - Unit tests always run regardless of network state.

import pytest
import httpx

BACKEND_URL = "http://localhost:3001"
DATA_URL = "http://localhost:8001"


def _is_reachable(url: str) -> bool:
    """Return True if the service at url responds within 2 seconds."""
    try:
        httpx.get(f"{url}/health", timeout=2)
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def backend_online():
    return _is_reachable(BACKEND_URL)


@pytest.fixture(scope="session")
def data_api_online():
    return _is_reachable(DATA_URL)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require the full stack (P4 on :3001, P5 on :8001)",
    )


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests when backend is offline."""
    if not _is_reachable(BACKEND_URL):
        skip_integration = pytest.mark.skip(
            reason=f"Integration test skipped — P4 backend not reachable at {BACKEND_URL}"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
