"""Base tool abstract class providing executable capabilities to agents."""

from abc import abstractmethod
from typing import Any, Optional
from pydantic import Field

from app.core.base_component import BaseComponent
from app.schemas.enums import EventType
from app.schemas.value_objects.tool_result import ToolResult


class BaseTool(BaseComponent):
    """Abstract foundation for executable tools (file I/O, terminal commands, etc.)."""

    description: str = Field(
        ..., min_length=1, description="Detailed human-readable description of what the tool does."
    )
    event_bus: Optional[Any] = Field(
        default=None, description="EventBus instance for publishing telemetry.", exclude=True
    )

    async def publish_telemetry(self, event_type: EventType, payload: dict[str, Any], task_id: Optional[Any] = None) -> None:
        """Helper to publish a telemetry event if the event bus is attached."""
        if self.event_bus:
            from app.schemas.entities.event import Event
            event = Event(
                event_type=event_type,
                task_id=task_id,
                payload=payload,
                metadata=self.metadata
            )
            await self.event_bus.publish(event)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool capability asynchronously with arbitrary keyword arguments."""
        pass