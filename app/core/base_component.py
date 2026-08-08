"""Base component abstract class for all framework building blocks."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.value_objects.metadata import Metadata


class BaseComponent(BaseModel, ABC):
    """Abstract kernel component providing lifecycle management and state validation."""

    model_config = ConfigDict(
        frozen=False,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    component_id: str = Field(
        ..., min_length=1, description="Unique identifier for the component instance."
    )
    is_initialized: bool = Field(
        default=False, description="Flag indicating whether the component has been initialized."
    )
    metadata: Metadata = Field(
        default_factory=Metadata, description="Structured component metadata."
    )

    @abstractmethod
    async def initialize(self) -> None:
        """Asynchronously initialize component resources, connections, or state."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Asynchronously shutdown and release component resources."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify operational health and responsiveness of the component."""
        pass

    def validate_state(self) -> None:
        """Verify that the component is initialized; raise RuntimeError if not."""
        if not self.is_initialized:
            raise RuntimeError(
                f"Component '{self.component_id}' is not initialized. Call initialize() first."
            )

    async def cleanup(self) -> None:
        """Safely invoke shutdown if the component is currently initialized."""
        if self.is_initialized:
            await self.shutdown()
            self.is_initialized = False