"""In-memory task manager handling engineering task lifecycle, dependencies, and retries."""

import logging
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.base_component import BaseComponent
from app.settings.settings import settings
from app.schemas.enums import AgentRole, TaskPriority, TaskStatus
from app.schemas.entities.task import Task
from app.exceptions.base import WorkflowError

logger = logging.getLogger(__name__)


class TaskManager(BaseComponent):
    """Manages the creation, state transitions, dependency checks, and retries of Tasks."""

    component_id: str = "task-manager"
    tasks: dict[UUID, Task] = {}

    def _get_storage_path(self) -> Path:
        data_dir = Path(settings.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "tasks.json"

    def _load_state(self) -> None:
        path = self._get_storage_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for task_id_str, task_data in data.items():
                    task = Task(**task_data)
                    self.tasks[task.id] = task
                logger.info(f"Loaded {len(self.tasks)} tasks from {path}.")
            except Exception as e:
                logger.error(f"Failed to load task state: {e}")

    def _save_state(self) -> None:
        if not self.is_initialized:
            return
        path = self._get_storage_path()
        try:
            data = {str(k): v.model_dump(mode="json") for k, v in self.tasks.items()}
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save task state: {e}")

    async def initialize(self) -> None:
        """Initialize the task manager system."""
        self.tasks = {}
        self._load_state()
        self.is_initialized = True
        logger.info("TaskManager initialized successfully.")

    async def shutdown(self) -> None:
        """Shutdown and clear all managed tasks from memory."""
        self.tasks.clear()
        self.is_initialized = False
        logger.info("TaskManager shut down and task memory cleared.")

    async def health_check(self) -> bool:
        """Verify operational health of the task manager."""
        return self.is_initialized

    def create_task(
        self,
        title: str,
        description: str,
        created_by: AgentRole,
        parent_task: Optional[UUID] = None,
        dependencies: Optional[list[UUID]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 5,
        estimated_duration: float = 0.0,
        assigned_to: Optional[AgentRole] = None,
    ) -> Task:
        """Create a new Task entity, register it in internal memory, and return it."""
        self.validate_state()

        deps = dependencies or []
        # Validate that all dependency tasks exist
        for dep_id in deps:
            if dep_id not in self.tasks:
                raise WorkflowError(
                    f"Cannot create task '{title}': Dependency task UUID {dep_id} does not exist."
                )

        task = Task(
            title=title,
            description=description,
            created_by=created_by,
            assigned_to=assigned_to,
            parent_task=parent_task,
            dependencies=deps,
            priority=priority,
            max_retries=max_retries,
            estimated_duration=estimated_duration,
            status=TaskStatus.CREATED,
        )

        self.tasks[task.id] = task
        logger.info(f"Task created: [{task.id}] '{task.title}' (Created by: {created_by})")
        self._save_state()
        return task

    def get_task(self, task_id: UUID) -> Task:
        """Retrieve a task by its UUID; raise WorkflowError if not found."""
        self.validate_state()
        if task_id not in self.tasks:
            raise WorkflowError(f"Task with ID {task_id} not found in TaskManager.")
        return task_id and self.tasks[task_id]  # type: ignore[return-value]

    def update_task_status(self, task_id: UUID, new_status: TaskStatus) -> Task:
        """Update the status of a task and trigger timestamp validation/touch."""
        self.validate_state()
        task = self.get_task(task_id)

        logger.debug(f"Updating task {task_id} status: {task.status} -> {new_status}")

        # If transitioning to IN_PROGRESS and started_at is not set, record it
        if new_status == TaskStatus.IN_PROGRESS and task.started_at is None:
            object.__setattr__(task, "started_at", datetime.now(timezone.utc))

        # Re-instantiate or mutate task with new status to trigger Pydantic validators
        # Since BaseModel is validation-on-assignment or model validation:
        task.status = new_status
        task.touch()

        self.tasks[task_id] = task
        logger.info(f"Task {task_id} status successfully updated to {new_status}")
        self._save_state()
        return task

    def get_ready_tasks(self) -> list[Task]:
        """Return tasks that are READY, or transition CREATED/WAITING to READY if dependencies are all DONE."""
        self.validate_state()
        ready_tasks: list[Task] = []

        for task in self.tasks.values():
            # Եթե արդեն պատրաստ է, միանգամից վերադարձնում ենք
            if task.status == TaskStatus.READY:
                ready_tasks.append(task)
            # Եթե սպասում է, ստուգում ենք կախվածությունները
            elif task.status in {TaskStatus.CREATED, TaskStatus.WAITING}:
                all_deps_done = True
                for dep_id in task.dependencies:
                    dep_task = self.tasks.get(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.DONE:
                        all_deps_done = False
                        break

                if all_deps_done:
                    # Automatically transition status to READY if it was CREATED or WAITING
                    task.status = TaskStatus.READY
                    task.touch()
                    ready_tasks.append(task)

        if ready_tasks:
            self._save_state()
        return ready_tasks
    def fail_task(self, task_id: UUID, error_message: str) -> Task:
        """Handle task failure by incrementing retries and setting RETRYING or FAILED status."""
        self.validate_state()
        task = self.get_task(task_id)

        new_retry_count = task.retry_count + 1
        object.__setattr__(task, "retry_count", new_retry_count)

        if new_retry_count <= task.max_retries:
            task.status = TaskStatus.RETRYING
            logger.warning(
                f"Task {task_id} failed (Attempt {new_retry_count}/{task.max_retries}). "
                f"Reason: {error_message}. Set to RETRYING."
            )
        else:
            task.status = TaskStatus.FAILED
            object.__setattr__(task, "failed_at", datetime.now(timezone.utc))
            logger.error(
                f"Task {task_id} permanently FAILED after {task.max_retries} max retries. "
                f"Reason: {error_message}."
            )

        task.touch()
        self.tasks[task_id] = task
        self._save_state()
        return task

    def update_task_fields(
        self,
        task_id: UUID,
        assigned_to: Optional[AgentRole] = None,
        priority: Optional[TaskPriority] = None,
    ) -> Task:
        """Update non-status fields of a task such as assignment and priority."""
        self.validate_state()
        task = self.get_task(task_id)

        if assigned_to is not None:
            task.assigned_to = assigned_to
        if priority is not None:
            task.priority = priority

        task.touch()
        self.tasks[task_id] = task
        logger.info(f"Task {task_id} updated fields: assigned_to={assigned_to}, priority={priority}")
        self._save_state()
        return task

    def delete_task(self, task_id: UUID) -> None:
        """Remove a task from the manager storage."""
        self.validate_state()
        if task_id not in self.tasks:
            raise WorkflowError(f"Task with ID {task_id} not found in TaskManager.")
        del self.tasks[task_id]
        logger.info(f"Task {task_id} deleted from TaskManager.")
        self._save_state()

    def retry_task(self, task_id: UUID) -> Task:
        """Prepare a previously failed task to be retried.

        Rules:
        - Only tasks in FAILED or RETRYING state are eligible.
        - If retry_count >= max_retries the retry is not allowed.
        - Reset retry_count and failed_at so validators allow new lifecycle transitions.
        - Set status back to CREATED to be picked up by the readiness checks.
        """
        self.validate_state()
        task = self.get_task(task_id)

        if task.status not in {TaskStatus.FAILED, TaskStatus.RETRYING}:
            raise WorkflowError(f"Task {task_id} is not in a retryable state ({task.status}).")

        if task.retry_count >= task.max_retries:
            raise WorkflowError(
                f"Task {task_id} has reached its maximum retries ({task.max_retries})."
            )

        # Reset retry bookkeeping and clear failure timestamp so validators accept the new status
        object.__setattr__(task, "retry_count", 0)
        object.__setattr__(task, "failed_at", None)

        # Move task back to CREATED so readiness logic can advance it to READY when dependencies allow
        task.status = TaskStatus.CREATED
        task.touch()
        self.tasks[task_id] = task
        logger.info(f"Task {task_id} reset for retry (retry_count cleared).")
        self._save_state()
        return task

    def autonomous_retry_task(self, task_id: UUID) -> Task:
        """Prepare a previously failed task to be retried automatically by the Orchestrator loop.

        Rules:
        - Only tasks in RETRYING state are eligible.
        - Preserves the incremented retry_count.
        - Sets the status to READY so the orchestrator can immediately dispatch it again.
        - Clears failed_at so validation passes.
        """
        self.validate_state()
        task = self.get_task(task_id)

        if task.status != TaskStatus.RETRYING:
            raise WorkflowError(f"Task {task_id} is not in RETRYING state ({task.status}).")

        # Clear failed_at so Pydantic validators accept non-FAILED status
        object.__setattr__(task, "failed_at", None)

        task.status = TaskStatus.READY
        task.touch()
        self.tasks[task_id] = task
        logger.info(f"Task {task_id} marked as READY for autonomous retry (Attempt {task.retry_count}/{task.max_retries}).")
        self._save_state()
        return task
