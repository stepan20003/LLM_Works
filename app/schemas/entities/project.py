"""Project entity definition for high-level project management and orchestration."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from app.schemas.enums import AgentRole, ProjectStatus
from app.schemas.value_objects.project_plan import ProjectPlan


class Project(BaseSchema):
    """Represents a high-level software engineering project requested by the user."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier of the project.")
    prompt: str = Field(..., min_length=1, description="Original project description/prompt provided by the user.")
    summary: Optional[str] = Field(default=None, description="Short one-line summary produced after planning.")
    status: ProjectStatus = Field(default=ProjectStatus.CREATED, description="Current status of the project lifecycle.")
    current_agent: Optional[AgentRole] = Field(default=None, description="Active agent role processing the project.")
    current_phase: Optional[str] = Field(default=None, description="Current high-level execution phase.")
    workspace_path: Optional[str] = Field(default=None, description="Isolated workspace path for project artifacts.")
    plan: Optional[ProjectPlan] = Field(default=None, description="Structured project plan produced by the Manager.")
    requirements_coverage: Optional[dict] = Field(default=None, description="Requirement coverage report from validation.")
    architecture_spec: Optional[dict] = Field(default=None, description="Architect's file manifest specification.")
    tasks: List[UUID] = Field(default_factory=list, description="List of task UUIDs associated with this project.")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall execution progress percentage.")
    timeline_events: List[dict] = Field(default_factory=list, description="Chrono log of events for real-time timeline.")
    created_files: List[str] = Field(default_factory=list, description="List of files created during project execution.")
    modified_files: List[str] = Field(default_factory=list, description="List of files modified during project execution.")
    test_results: List[dict] = Field(default_factory=list, description="Structured test execution records.")
    review_results: List[dict] = Field(default_factory=list, description="Structured review findings.")
    errors_and_retries: List[dict] = Field(default_factory=list, description="Log of errors encountered and retries attempted.")
    error_message: Optional[str] = Field(default=None, description="Error description if the project failed.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the project was created.")
    completed_at: Optional[datetime] = Field(default=None, description="Timestamp when the project was completed.")
    failed_at: Optional[datetime] = Field(default=None, description="Timestamp when the project failed, if any.")

    @model_validator(mode="after")
    def validate_project_constraints(self) -> "Project":
        """Validate timestamp state consistency."""
        if self.status not in {ProjectStatus.DONE, ProjectStatus.APPROVED} and self.completed_at is not None:
            raise ValueError("completed_at cannot exist unless project status is DONE or APPROVED.")
        return self