"""Base agent abstract class representing autonomous engineering workers."""

from abc import abstractmethod
from typing import Any, Optional
from uuid import UUID
from pydantic import Field

from app.core.base_component import BaseComponent
from app.schemas.enums import AgentRole, AgentState, EventType
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.agent_runtime import AgentRuntimeState


class BaseAgent(BaseComponent):
    """Abstract foundation for all specialized autonomous agents."""

    role: AgentRole = Field(
        ..., description="Specialized functional role of the agent."
    )
    state: AgentState = Field(
        default=AgentState.IDLE, description="Current operational state of the agent."
    )
    current_task_id: Optional[UUID] = Field(
        default=None, description="UUID of the task currently being processed, if any."
    )
    event_bus: Optional[Any] = Field(
        default=None, description="EventBus instance for publishing telemetry.", exclude=True
    )

    async def publish_telemetry(self, event_type: EventType, payload: dict[str, Any]) -> None:
        """Helper to publish a telemetry event if the event bus is attached."""
        if self.event_bus:
            # Import Event inside to avoid potential circular dependencies if schemas change
            from app.schemas.entities.event import Event
            event = Event(
                event_type=event_type,
                source_agent=self.role,
                task_id=self.current_task_id,
                payload=payload,
                metadata=self.metadata
            )
            await self.event_bus.publish(event)

    @abstractmethod
    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Execute assigned engineering task asynchronously and return structured response."""
        pass

    @abstractmethod
    async def handle_message(self, message: Any) -> Optional[AgentResponse]:
        """Process incoming asynchronous messages or direct queries from other agents."""
        pass

    def get_runtime_state(self) -> AgentRuntimeState:
        """Construct and return an immutable AgentRuntimeState snapshot."""
        return AgentRuntimeState(
            agent_id=self.component_id,
            role=self.role,
            state=self.state,
            current_task_id=self.current_task_id,
            metadata=self.metadata,
        )