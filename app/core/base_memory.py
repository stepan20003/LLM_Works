"""Base memory abstract class for short-term and persistent data storage."""

from abc import abstractmethod
from typing import Any, Optional

from app.core.base_component import BaseComponent


class BaseMemory(BaseComponent):
    """Abstract foundation for state storage, caching, and contextual retrieval."""

    @abstractmethod
    async def store(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> None:
        """Store a key-value pair with optional time-to-live expiration."""
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a stored value by its key, or return None if missing/expired."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a stored entry by key; return True if deleted, False if not found."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all stored entries from the memory partition."""
        pass