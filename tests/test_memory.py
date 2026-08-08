"""Unit tests for InMemoryStore component covering storage, TTL expiration, and clearing."""

import pytest
import asyncio

from app.memory.store import InMemoryStore


@pytest.mark.asyncio
async def test_in_memory_store_basic_operations() -> None:
    """Verify basic store, retrieve, delete, and non-existent key handling."""
    store = InMemoryStore()
    await store.initialize()

    # Store and retrieve
    await store.store("key1", "value1")
    val = await store.retrieve("key1")
    assert val == "value1"

    # Delete
    deleted = await store.delete("key1")
    assert deleted is True
    assert await store.retrieve("key1") is None

    # Delete non-existent
    assert await store.delete("non_existent") is False

    await store.shutdown()


@pytest.mark.asyncio
async def test_in_memory_store_ttl_expiration() -> None:
    """Verify that keys expire correctly after their Time-To-Live (TTL) elapses."""
    store = InMemoryStore()
    await store.initialize()

    # Store with short TTL (1 second)
    await store.store("temp_key", "temp_value", ttl_seconds=1)

    # Immediately retrieve should work
    assert await store.retrieve("temp_key") == "temp_value"

    # Wait for expiration
    await asyncio.sleep(1.2)

    # Retrieve after TTL should return None and purge key
    assert await store.retrieve("temp_key") is None
    assert "temp_key" not in store.store_data

    await store.shutdown()


@pytest.mark.asyncio
async def test_in_memory_store_clear() -> None:
    """Verify clearing all stored entries from memory."""
    store = InMemoryStore()
    await store.initialize()

    await store.store("a", 1)
    await store.store("b", 2)
    assert await store.retrieve("a") == 1

    await store.clear()
    assert await store.retrieve("a") is None
    assert await store.retrieve("b") is None
    assert len(store.store_data) == 0

    await store.shutdown()