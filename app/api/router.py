"""REST API endpoints for task management and system health checks."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.schemas.enums import AgentRole, TaskPriority, TaskStatus
from app.schemas.entities.task import Task
from app.tasks.task_manager import TaskManager
from app.orchestrator.orchestrator import Orchestrator

router = APIRouter(tags=["AI Development Team API"])

# Global references injected during startup (lifespan)
_task_manager: Optional[TaskManager] = None
_orchestrator: Optional[Orchestrator] = None


def set_api_dependencies(task_manager: TaskManager, orchestrator: Orchestrator) -> None:
    """Inject core dependency instances into the API router."""
    global _task_manager, _orchestrator
    _task_manager = task_manager
    _orchestrator = orchestrator


def _get_task_manager(request: Request) -> Optional[TaskManager]:
    """Resolve the active TaskManager from the request app state or router globals."""
    task_manager = getattr(request.app.state, "task_manager", None)
    if task_manager is not None:
        return task_manager

    if getattr(request.app.state, "api_dependencies_ready", False):
        return _task_manager

    return None


def _get_orchestrator(request: Request) -> Optional[Orchestrator]:
    """Resolve the active Orchestrator from the request app state or router globals."""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if orchestrator is not None:
        return orchestrator

    if getattr(request.app.state, "api_dependencies_ready", False):
        return _orchestrator

    return None


class TaskCreateRequest(BaseModel):
    """Payload schema for creating a new engineering task."""

    title: str = Field(..., min_length=1, description="Concise title of the task.")
    description: str = Field(..., min_length=1, description="Detailed requirements of the task.")
    created_by: AgentRole = Field(default=AgentRole.MANAGER, description="Role of the creator.")
    assigned_to: Optional[AgentRole] = Field(default=None, description="Assigned execution agent role.")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority.")
    max_retries: int = Field(default=5, ge=0, description="Max allowed retries.")
    estimated_duration: float = Field(default=0.0, ge=0.0, description="Estimated execution seconds.")


class TaskUpdateRequest(BaseModel):
    """Payload for partial updates to a Task (PATCH).

    Only status, assigned_to and priority are allowed to be changed by this endpoint.
    """

    status: Optional[TaskStatus] = Field(default=None, description="New lifecycle status for the task.")
    assigned_to: Optional[AgentRole] = Field(default=None, description="Role to assign the task to.")
    priority: Optional[TaskPriority] = Field(default=None, description="New task priority.")


@router.post("/tasks/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(request: Request, payload: TaskCreateRequest) -> Task:
    """Create a new engineering task within the task manager."""
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")

    try:
        task = task_manager.create_task(
            title=payload.title,
            description=payload.description,
            created_by=payload.created_by,
            assigned_to=payload.assigned_to,
            priority=payload.priority,
            max_retries=payload.max_retries,
            estimated_duration=payload.estimated_duration,
        )
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/tasks/", response_model=List[Task])
async def list_tasks(request: Request) -> List[Task]:
    """Retrieve all engineering tasks currently registered in the system."""
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")
    return list(task_manager.tasks.values())


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(request: Request, task_id: UUID) -> Task:
    """Retrieve detailed status and metadata for a specific task by its UUID."""
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")
    try:
        return task_manager.get_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.") from e


@router.patch("/tasks/{task_id}", response_model=Task)
async def patch_task(request: Request, task_id: UUID, payload: TaskUpdateRequest) -> Task:
    """Partially update a task's status, assignment, and priority."""
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")

    try:
        task: Task
        # If status is supplied, use TaskManager's status updater to ensure side-effects occur
        if payload.status is not None:
            task = task_manager.update_task_status(task_id, payload.status)
        else:
            task = task_manager.get_task(task_id)

        # Update assignment and priority fields if present
        if payload.assigned_to is not None or payload.priority is not None:
            task = task_manager.update_task_fields(
                task_id, assigned_to=payload.assigned_to, priority=payload.priority
            )

        return task
    except Exception as e:
        # Keep error messages compatible with existing endpoints
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(request: Request, task_id: UUID) -> Response:
    """Delete a task from the TaskManager storage."""
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")

    try:
        task_manager.delete_task(task_id)
        # FastAPI will return an empty body with the configured status code
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/tasks/{task_id}/retry", response_model=Task)
async def retry_task(request: Request, task_id: UUID) -> Task:
    """Reset a failed task so it can be retried according to retry policy."""
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")

    try:
        task = task_manager.retry_task(task_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/tasks/{task_id}/cancel", response_model=Task)
async def cancel_task(request: Request, task_id: UUID) -> Task:
    """Mark a task as CANCELLED."""
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")

    try:
        task = task_manager.update_task_status(task_id, TaskStatus.CANCELLED)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(request: Request) -> dict[str, str]:
    """Perform a health check on core orchestrator and task manager subsystems."""
    task_manager = _get_task_manager(request)
    orchestrator = _get_orchestrator(request)
    if not orchestrator or not task_manager:
        return {"status": "degraded", "detail": "Subsystems not fully initialized."}

    is_healthy = await orchestrator.health_check()
    if is_healthy:
        return {"status": "healthy", "service": "ai-development-team"}
    else:
        return {"status": "unhealthy"}