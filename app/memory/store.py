"""In-memory storage implementation inheriting from BaseMemory with TTL support."""

import asyncio
import logging
import time
from typing import Any, Optional
from pydantic import Field

from app.core.base_memory import BaseMemory

logger = logging.getLogger(__name__)


class InMemoryStore(BaseMemory):
    """Enterprise-grade in-memory key-value store with time-to-live (TTL) expiration support."""

    component_id: str = "in-memory-store"
    store_data: dict[str, tuple[Any, Optional[float]]] = Field(
        default_factory=dict,
        description="Internal storage mapping keys to tuples of (value, expiration_timestamp).",
    )

    async def initialize(self) -> None:
        """Initialize the in-memory store."""
        self.store_data = {}
        self.is_initialized = True
        logger.info("InMemoryStore initialized successfully.")

    async def shutdown(self) -> None:
        """Shutdown and clear all stored memory data."""
        self.store_data.clear()
        self.is_initialized = False
        logger.info("InMemoryStore shut down and memory cleared.")

    async def health_check(self) -> bool:
        """Verify operational health of the memory store."""
        return self.is_initialized

    async def store(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        """Store a key-value pair with an optional time-to-live expiration in seconds."""
        self.validate_state()
        
        expire_at: Optional[float] = None
        if ttl_seconds is not None and ttl_seconds > 0:
            expire_at = time.time() + float(ttl_seconds)

        self.store_data[key] = (value, expire_at)
        logger.debug(f"Stored key '{key}' with TTL: {ttl_seconds}s")

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a stored value by its key, checking and enforcing TTL expiration."""
        self.validate_state()
        
        if key not in self.store_data:
            return None

        value, expire_at = self.store_data[key]

        # Check if the entry has expired
        if expire_at is not None and time.time() > expire_at:
            logger.debug(f"Key '{key}' has expired. Removing from store.")
            del self.store_data[key]
            return None

        return value

    async def delete(self, key: str) -> bool:
        """Delete a stored entry by key; return True if deleted, False if not found."""
        self.validate_state()
        
        if key in self.store_data:
            del self.store_data[key]
            logger.debug(f"Deleted key '{key}' from store.")
            return True
        return False

    async def clear(self) -> None:
        """Clear all stored entries from memory."""
        self.validate_state()
        self.store_data.clear()
        logger.debug("Cleared all entries from InMemoryStore.")