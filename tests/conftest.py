"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def mock_settings(monkeypatch):
    """Override settings for testing."""
    monkeypatch.setenv("SUPABASE_DB_HOST", "localhost")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "test")
    monkeypatch.setenv("TEMPORAL_ADDRESS", "localhost:7233")

    # Clear cached settings
    from signalroom.common.config import get_settings

    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing S3 exports source."""
    return [
        {"id": "1", "name": "Test 1", "value": "100"},
        {"id": "2", "name": "Test 2", "value": "200"},
        {"id": "3", "name": "Test 3", "value": "300"},
    ]
