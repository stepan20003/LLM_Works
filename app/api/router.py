import json
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.schemas.enums import AgentRole, ProjectStatus, TaskPriority, TaskStatus
from app.schemas.enums import EventType
from app.schemas.entities.task import Task
from app.schemas.entities.event import Event
from app.schemas.entities.project import Project
from app.schemas.value_objects.project_plan import ProjectPlan
from app.tasks.task_manager import TaskManager
from app.projects.project_manager import ProjectManager
from app.orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Development Team API"])

# Global references injected during startup (lifespan)
_task_manager: Optional[TaskManager] = None
_orchestrator: Optional[Orchestrator] = None
_project_manager: Optional[ProjectManager] = None


def set_api_dependencies(
    task_manager: TaskManager,
    orchestrator: Orchestrator,
    project_manager: Optional[ProjectManager] = None,
) -> None:
    """Inject core dependency instances into the API router."""
    global _task_manager, _orchestrator, _project_manager
    _task_manager = task_manager
    _orchestrator = orchestrator
    _project_manager = project_manager


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
        orchestrator = _get_orchestrator(request)
        if orchestrator is not None:
            await orchestrator.event_bus.publish(
                Event(
                    event_type=EventType.TASK_CREATED,
                    source_agent=payload.created_by,
                    destination_agent=payload.assigned_to,
                    task_id=task.id,
                    payload={
                        "status": task.status,
                        "title": task.title,
                        "priority": task.priority,
                    },
                )
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


# ---------------------------------------------------------------------------
# Project endpoints
# ---------------------------------------------------------------------------

def _get_project_manager(request: Request) -> Optional[ProjectManager]:
    """Resolve the active ProjectManager from request app state or router globals."""
    pm = getattr(request.app.state, "project_manager", None)
    if pm is not None:
        return pm
    if getattr(request.app.state, "api_dependencies_ready", False):
        return _project_manager
    return None


class ProjectCreateRequest(BaseModel):
    """Payload schema for creating a new project."""

    prompt: str = Field(..., min_length=1, description="The full project description/prompt.")


@router.post("/projects/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(request: Request, payload: ProjectCreateRequest) -> Project:
    """Create a new project from a user prompt."""
    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")

    try:
        project = project_manager.create_project(prompt=payload.prompt)
        return project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/projects/", response_model=List[Project])
async def list_projects(request: Request) -> List[Project]:
    """Retrieve all projects."""
    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")
    return project_manager.get_all_projects()


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(request: Request, project_id: UUID) -> Project:
    """Retrieve a specific project by UUID."""
    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")
    try:
        return project_manager.get_project(project_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.") from e


@router.post("/projects/{project_id}/plan", response_model=Project)
async def plan_project(request: Request, project_id: UUID) -> Project:
    """Trigger the ManagerAgent to generate a structured plan for the project."""
    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")

    try:
        project = project_manager.get_project(project_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.") from e

    # Get the manager agent from app state
    manager_agent = getattr(request.app.state, "manager_agent", None)
    if not manager_agent:
        raise HTTPException(status_code=500, detail="ManagerAgent is not available.")

    # Ask the manager to produce a plan
    from uuid import uuid4
    response = await manager_agent.process_task(
        task_id=uuid4(),
        context_payload={"project_prompt": project.prompt, "content": project.prompt},
    )

    # Extract plan from response metadata
    plan_data = response.metadata.extra.get("plan") if response.metadata and response.metadata.extra else None

    if plan_data and response.status.value == "SUCCESS":
        plan = ProjectPlan(**plan_data)
        project = project_manager.update_project_plan(project_id, plan)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Planning failed: {response.message}",
        )

    return project


@router.post("/projects/{project_id}/execute", response_model=Project)
async def execute_project_plan(request: Request, project_id: UUID) -> Project:
    """Materialize a project's plan into real Task entities with dependency resolution.

    The plan's subtasks are validated for cycles, then created as Task entities
    in topological order with proper UUID-based dependencies.
    """
    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")

    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")

    try:
        project_manager.get_project(project_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.") from e

    from app.projects.plan_executor import PlanExecutor, DependencyCycleError, DuplicateSubtaskError

    executor = PlanExecutor(task_manager=task_manager, project_manager=project_manager)

    try:
        task_ids = executor.execute_plan(project_id)
    except DependencyCycleError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except DuplicateSubtaskError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    project = project_manager.get_project(project_id)
    return project


@router.get("/projects/{project_id}/timeline")
async def get_project_timeline(request: Request, project_id: UUID) -> dict:
    """Retrieve chronologically ordered execution timeline events for a project."""
    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")

    try:
        project = project_manager.get_project(project_id)
        return {
            "project_id": str(project.id),
            "status": project.status,
            "current_agent": project.current_agent,
            "current_phase": project.current_phase,
            "progress": project.progress,
            "events": project.timeline_events,
            "created_files": project.created_files,
            "modified_files": project.modified_files,
            "test_results": project.test_results,
            "review_results": project.review_results,
            "errors_and_retries": project.errors_and_retries,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.") from e


@router.post("/projects/{project_id}/start", response_model=Project)
async def start_full_project_pipeline(request: Request, project_id: UUID) -> Project:
    """Orchestrate end-to-end execution of a project through all pipeline stages."""
    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")
    task_manager = _get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager is not initialized.")
    orchestrator = _get_orchestrator(request)
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator is not initialized.")

    try:
        project = project_manager.get_project(project_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.") from e

    from uuid import uuid4
    from app.schemas.enums import AgentRole, EventType, ProjectStatus
    from app.schemas.entities.event import Event
    from app.projects.plan_executor import PlanExecutor

    # Step 1: Manager Phase
    project_manager.update_project_phase(project_id, "Manager: Requirements Analysis & Planning", AgentRole.MANAGER)
    await orchestrator.event_bus.publish(
        Event(
            event_type=EventType.PROJECT_PHASE_CHANGED,
            source_agent=AgentRole.MANAGER,
            destination_agent=AgentRole.SYSTEM,
            payload={"project_id": str(project_id), "phase": "Manager: Requirements Analysis & Planning"},
        )
    )

    manager_agent = getattr(request.app.state, "manager_agent", None)
    if manager_agent:
        response = await manager_agent.process_task(
            task_id=uuid4(),
            context_payload={"project_prompt": project.prompt, "content": project.prompt},
        )
        plan_data = response.metadata.extra.get("plan") if response.metadata and response.metadata.extra else None
        if plan_data and response.status.value == "SUCCESS":
            plan = ProjectPlan(**plan_data)
            project_manager.update_project_plan(project_id, plan)

    # Step 2: Architect Phase
    project_manager.update_project_phase(project_id, "Architect: System Architecture & Design", AgentRole.ARCHITECT)
    await orchestrator.event_bus.publish(
        Event(
            event_type=EventType.PROJECT_PHASE_CHANGED,
            source_agent=AgentRole.ARCHITECT,
            destination_agent=AgentRole.SYSTEM,
            payload={"project_id": str(project_id), "phase": "Architect: System Architecture & Design"},
        )
    )

    arch_spec = None
    architect_agent = getattr(request.app.state, "architect_agent", None)
    if architect_agent:
        arch_res = await architect_agent.process_task(
            task_id=uuid4(),
            context_payload={"project_prompt": project.prompt, "workspace_path": project.workspace_path},
        )
        if arch_res.metadata and arch_res.metadata.extra:
            arch_spec = arch_res.metadata.extra.get("architecture_spec")
            if arch_spec:
                proj = project_manager.get_project(project_id)
                proj.architecture_spec = arch_spec
                project_manager.projects[project_id] = proj
                project_manager._save_state()

                from app.tools.file_tools import FileTool
                from app.workspace.local_workspace import LocalWorkspace
                ft = FileTool(workspace=LocalWorkspace(root_path=project.workspace_path))
                await ft.initialize()
                arch_md = f"# Architecture Specification\n\n```json\n{json.dumps(arch_spec, indent=2)}\n```\n"
                await ft.execute(action="write", path="ARCHITECTURE.md", content=arch_md)

    project_manager.add_timeline_event(
        project_id,
        event_type="PROJECT_TIMELINE_EVENT",
        agent=AgentRole.ARCHITECT,
        message=f"Architecture specification finalized. {len(arch_spec.get('required_files', [])) if arch_spec and isinstance(arch_spec, dict) else 0} files planned.",
    )

    # Step 3: Materialize Plan to Tasks
    executor = PlanExecutor(task_manager=task_manager, project_manager=project_manager)
    task_ids = executor.execute_plan(project_id)

    # Step 4: Autonomous Execution Loop (Developer -> Reviewer -> Tester -> Debugger when needed -> DONE)
    max_iterations = max(20, len(task_ids) * 8)
    for iteration in range(max_iterations):
        current_project = project_manager.get_project(project_id)
        active_task_ids = current_project.tasks
        task_statuses = {tid: task_manager.get_task(tid).status for tid in active_task_ids if tid in task_manager.tasks}
        
        # Check if all tasks are completed
        if task_statuses and all(st == TaskStatus.DONE for st in task_statuses.values()):
            break

        active_agents = [task_manager.get_task(tid).assigned_to for tid in active_task_ids if tid in task_manager.tasks and task_manager.get_task(tid).status != TaskStatus.DONE]
        current_agent = active_agents[0] if active_agents else AgentRole.DEVELOPER
        
        phase_messages = {
            AgentRole.DEVELOPER: "Developer: Code Implementation & File Generation",
            AgentRole.REVIEWER: "Reviewer: Code Quality & Security Gate",
            AgentRole.TESTER: "Tester: Automated Test Suite Execution",
            AgentRole.DEBUGGER: "Debugger: Root Cause Analysis & Autonomous Fix",
        }
        phase_str = phase_messages.get(current_agent, f"{current_agent.value}: Executing Pipeline Tasks")
        project_manager.update_project_phase(project_id, phase_str, current_agent)

        await orchestrator.run_iteration()
        project_manager.update_progress(project_id, task_statuses)

    # Step 5: Post-Loop Validation & Requirement Coverage Verification
    project_manager.sync_project_workspace_files(project_id)

    # Requirement coverage check
    from app.projects.requirement_tracker import extract_requirements_from_prompt, check_requirement_coverage
    reqs = extract_requirements_from_prompt(project.prompt)
    coverage = check_requirement_coverage(reqs, project.workspace_path)

    current_project = project_manager.get_project(project_id)
    current_project.requirements_coverage = coverage
    project_manager.projects[project_id] = current_project
    project_manager._save_state()

    # Manifest check
    manifest_info = {}
    if arch_spec and isinstance(arch_spec, dict) and "required_files" in arch_spec:
        manifest_info = project_manager.validate_against_manifest(project_id, arch_spec["required_files"])

    # Strict Validation Checks
    validation_passed = True
    validation_errors = []

    try:
        project_manager.validate_project_workspace(project_id)
    except Exception as ve:
        validation_passed = False
        validation_errors.append(str(ve))

    if manifest_info and not manifest_info.get("valid", True):
        validation_passed = False
        missing_str = ", ".join(manifest_info.get("missing_files", []))
        validation_errors.append(f"Architect manifest validation failed: missing files: {missing_str}")

    # If coverage < 100% or validation failed, mark FAILED instead of APPROVED
    if not validation_passed or coverage.get("coverage_pct", 0) < 100.0:
        err_msg = "Validation failed: " + "; ".join(validation_errors) if validation_errors else f"Requirement coverage incomplete ({coverage.get('coverage_pct', 0)}%). Missing: {', '.join(coverage.get('missing', []))}"
        project_manager.fail_project(project_id, err_msg)
        raise HTTPException(status_code=422, detail=err_msg)

    # Approve project
    project_manager.update_project_phase(project_id, "APPROVED", AgentRole.MANAGER)
    project_manager.update_project_status(project_id, ProjectStatus.APPROVED)
    
    current_project = project_manager.get_project(project_id)
    object.__setattr__(current_project, "progress", 100.0)
    project_manager.projects[project_id] = current_project
    project_manager._save_state()

    # Generate documentation reports and ZIP archive with validation
    try:
        project_manager.create_project_zip(project_id)
        project_manager.sync_project_workspace_files(project_id)
    except Exception as e:
        logger.error(f"Error creating project ZIP: {e}", exc_info=True)

    project_manager.add_timeline_event(
        project_id,
        event_type="PROJECT_APPROVED",
        agent=AgentRole.MANAGER,
        message=f"Project pipeline completed successfully with APPROVED state. Requirement coverage: {coverage.get('coverage_pct')}% ({coverage.get('satisfied_count')}/{coverage.get('total_count')}). Downloadable ZIP created.",
    )

    final_proj = project_manager.get_project(project_id)

    await orchestrator.event_bus.publish(
        Event(
            event_type=EventType.PROJECT_APPROVED,
            source_agent=AgentRole.MANAGER,
            destination_agent=AgentRole.SYSTEM,
            payload={
                "project_id": str(project_id),
                "status": "APPROVED",
                "phase": "APPROVED",
                "progress": 100.0,
                "created_files": final_proj.created_files,
                "modified_files": final_proj.modified_files,
                "test_results": final_proj.test_results,
                "review_results": final_proj.review_results,
                "requirements_coverage": coverage,
            },
        )
    )

    return final_proj


@router.get("/projects/{project_id}/download")
async def download_project_archive(request: Request, project_id: UUID) -> Response:
    """Download completed project files and documentation reports as a ZIP archive."""
    from fastapi.responses import FileResponse

    project_manager = _get_project_manager(request)
    if not project_manager:
        raise HTTPException(status_code=500, detail="ProjectManager is not initialized.")

    try:
        project_manager.get_project(project_id)
        zip_path = project_manager.create_project_zip(project_id)

        if not zip_path.exists():
            raise HTTPException(status_code=500, detail="ZIP archive generation failed.")

        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"project_{project_id}.zip",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e