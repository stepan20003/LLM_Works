"""Agent runtime state value object tracking operational status and current activity."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AgentRole, AgentState
from app.schemas.value_objects.metadata import Metadata


class AgentRuntimeState(BaseModel):
    """Represents the current runtime state and context of an agent."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    agent_id: str = Field(
        ..., min_length=1, description="Unique identifier or name of the agent."
    )
    role: AgentRole = Field(
        ..., description="Specialized role assigned to the agent."
    )
    state: AgentState = Field(
        ..., description="Current operational state of the agent."
    )
    current_task_id: Optional[UUID] = Field(
        default=None, description="UUID of the task currently being processed, if any."
    )
    metadata: Metadata = Field(
        default_factory=Metadata, description="Typed agent runtime metadata."
    )