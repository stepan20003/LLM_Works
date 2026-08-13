"""Structured project planning value objects for Manager agent output."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AgentRole, TaskPriority


class SubtaskSpec(BaseModel):
    """Specification of a single subtask within a project plan."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(
        ..., min_length=1, description="Concise title of the subtask."
    )
    description: str = Field(
        ..., min_length=1, description="Detailed requirements for the subtask."
    )
    assigned_role: AgentRole = Field(
        default=AgentRole.DEVELOPER,
        description="Agent role responsible for executing this subtask.",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Titles of other subtasks that must complete before this one.",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL,
        description="Priority level of the subtask.",
    )
    estimated_duration: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated execution duration in seconds (0.0 if unknown).",
    )


class ProjectPlan(BaseModel):
    """Structured plan produced by the ManagerAgent for a project."""

    model_config = ConfigDict(frozen=True)

    summary: str = Field(
        ..., min_length=1, description="One-paragraph project overview."
    )
    requirements: list[str] = Field(
        default_factory=list,
        description="Extracted functional and non-functional requirements.",
    )
    architecture: str = Field(
        default="",
        description="High-level architecture description.",
    )
    subtasks: list[SubtaskSpec] = Field(
        default_factory=list,
        description="Ordered list of subtasks to execute.",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Criteria that must be met for the project to be considered complete.",
    )
