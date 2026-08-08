"""Task entity schema representing units of work within the orchestrator."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from app.schemas.enums import AgentRole, TaskPriority, TaskStatus
from app.schemas.value_objects.metadata import Metadata


class Task(BaseSchema):
    """Represents an engineering task managed by the orchestrator."""

    title: str = Field(
        ..., min_length=1, description="Concise title of the task."
    )
    description: str = Field(
        ..., min_length=1, description="Detailed requirements and instructions for the task."
    )
    status: TaskStatus = Field(
        default=TaskStatus.CREATED, description="Current lifecycle status of the task."
    )
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL, description="Priority level of the task."
    )
    created_by: AgentRole = Field(
        ..., description="Role of the agent who created the task."
    )
    assigned_to: Optional[AgentRole] = Field(
        default=None, description="Role of the agent assigned to execute the task."
    )
    parent_task: Optional[UUID] = Field(
        default=None, description="UUID of the parent task if this is a subtask."
    )
    dependencies: list[UUID] = Field(
        default_factory=list, description="List of task UUIDs that must be DONE prior to starting."
    )
    tags: list[str] = Field(
        default_factory=list, description="Categorization tags associated with the task."
    )
    metadata: Metadata = Field(
        default_factory=Metadata, description="Typed metadata container."
    )
    retry_count: int = Field(
        default=0, ge=0, description="Number of retry attempts executed so far."
    )
    max_retries: int = Field(
        default=5, ge=0, description="Maximum permitted retry attempts."
    )
    estimated_duration: float = Field(
        default=0.0, ge=0.0, description="Estimated execution duration in seconds."
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the task execution started (UTC)."
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the task reached DONE status (UTC)."
    )
    failed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the task failed (UTC)."
    )

    @model_validator(mode="after")
    def validate_task_constraints(self) -> "Task":
        """Validate retry counts and timestamp state consistency."""
        # Թույլ ենք տալիսretry_count-ին գերազանցել max_retries-ը միայն այն դեպքում, երբ խնդիրը FAILED է
        if self.status != TaskStatus.FAILED and self.retry_count > self.max_retries:
            raise ValueError(
                f"retry_count ({self.retry_count}) cannot exceed max_retries ({self.max_retries})."
            )

        now = datetime.now(timezone.utc)

        if self.status == TaskStatus.DONE and self.completed_at is None:
            object.__setattr__(self, "completed_at", now)

        if self.status != TaskStatus.DONE and self.completed_at is not None:
            raise ValueError("completed_at cannot exist unless task status is DONE.")

        if self.status == TaskStatus.FAILED and self.failed_at is None:
            object.__setattr__(self, "failed_at", now)

        return self