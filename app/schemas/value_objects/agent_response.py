"""Agent response value object capturing the outcome of an agent execution cycle."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AgentExecutionStatus, AgentRole
from app.schemas.value_objects.metadata import Metadata
from app.schemas.value_objects.attachment import Attachment


class AgentResponse(BaseModel):
    """Represents the structured output returned by an agent after processing a task."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    status: AgentExecutionStatus = Field(
        ..., description="Standardized execution status of the agent task."
    )
    message: str = Field(
        ..., description="Descriptive rationale or summary from the agent."
    )
    created_tasks: list[UUID] = Field(
        default_factory=list, description="List of task UUIDs created during execution."
    )
    updated_tasks: list[UUID] = Field(
        default_factory=list, description="List of task UUIDs updated during execution."
    )
    artifacts: list[Attachment] = Field(
        default_factory=list, description="Artifacts or files produced during execution."
    )
    next_agent: Optional[AgentRole] = Field(
        default=None, description="Recommended next agent role to take over."
    )
    metadata: Metadata = Field(
        default_factory=Metadata, description="Typed telemetry metadata."
    )