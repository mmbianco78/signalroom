#!/usr/bin/env python3
"""Test Temporal Cloud connection.

Usage:
    python scripts/test_temporal_connection.py
"""

import asyncio
import sys

from signalroom.common import get_logger, settings
from signalroom.temporal.config import get_temporal_client

log = get_logger(__name__)


async def test_connection() -> bool:
    """Test connection to Temporal Cloud."""
    print(f"Temporal Address: {settings.temporal_address}")
    print(f"Temporal Namespace: {settings.temporal_namespace}")
    print(f"API Key configured: {bool(settings.temporal_api_key.get_secret_value())}")
    print()

    try:
        print("Connecting to Temporal...")
        client = await get_temporal_client()
        print(f"✓ Connected to namespace: {client.namespace}")

        # Test by listing workflows (should return empty if no workflows)
        print("Testing workflow listing...")
        workflows = [w async for w in client.list_workflows(query="", page_size=1)]
        print(f"✓ Can query workflows (found {len(workflows)} recent)")

        print()
        print("=" * 50)
        print("✓ Temporal Cloud connection successful!")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        log.exception("temporal_connection_failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
