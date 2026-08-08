"""Unit tests for TaskManager component covering lifecycle, dependencies, and retries."""

import pytest
from uuid import UUID

from app.tasks.task_manager import TaskManager
from app.schemas.enums import AgentRole, TaskPriority, TaskStatus
from app.exceptions.base import WorkflowError


@pytest.mark.asyncio
async def test_task_creation() -> None:
    """Verify task creation and initial field settings."""
    manager = TaskManager()
    await manager.initialize()

    task = manager.create_task(
        title="Test Task",
        description="Testing task creation logic.",
        created_by=AgentRole.MANAGER,
        priority=TaskPriority.HIGH,
    )

    assert task.title == "Test Task"
    assert task.status == TaskStatus.CREATED
    assert task.priority == TaskPriority.HIGH
    assert task.created_by == AgentRole.MANAGER
    
    retrieved = manager.get_task(task.id)
    assert retrieved.id == task.id

    await manager.shutdown()


@pytest.mark.asyncio
async def test_task_status_updates_and_timestamps() -> None:
    """Verify task status updates and automated timestamp recordings (started_at, completed_at)."""
    manager = TaskManager()
    await manager.initialize()

    task = manager.create_task(
        title="Timestamp Task",
        description="Testing timestamps.",
        created_by=AgentRole.DEVELOPER,
    )

    assert task.started_at is None
    assert task.completed_at is None

    # Transition to IN_PROGRESS
    manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)
    updated = manager.get_task(task.id)
    assert updated.status == TaskStatus.IN_PROGRESS
    assert updated.started_at is not None

    # Transition to DONE
    manager.update_task_status(task.id, TaskStatus.DONE)
    done_task = manager.get_task(task.id)
    assert done_task.status == TaskStatus.DONE
    assert done_task.completed_at is not None

    await manager.shutdown()


@pytest.mark.asyncio
async def test_get_ready_tasks_with_dependencies() -> None:
    """Verify that tasks with uncompleted dependencies remain unready until parents finish."""
    manager = TaskManager()
    await manager.initialize()

    # Parent task
    parent = manager.create_task(
        title="Parent Task",
        description="Must be done first.",
        created_by=AgentRole.MANAGER,
    )

    # Child task depending on parent
    child = manager.create_task(
        title="Child Task",
        description="Depends on parent.",
        created_by=AgentRole.DEVELOPER,
        dependencies=[parent.id],
    )

    # Initially, only parent should be ready
    ready_tasks = manager.get_ready_tasks()
    ready_ids = [t.id for t in ready_tasks]

    assert parent.id in ready_ids
    assert child.id not in ready_ids

    # Complete parent task
    manager.update_task_status(parent.id, TaskStatus.DONE)

    # Now child should become ready
    ready_tasks_after = manager.get_ready_tasks()
    ready_ids_after = [t.id for t in ready_tasks_after]

    assert child.id in ready_ids_after

    await manager.shutdown()


@pytest.mark.asyncio
async def test_fail_task_and_retries() -> None:
    """Verify fail_task retry counting, RETRYING state, and ultimate FAILED transition."""
    manager = TaskManager()
    await manager.initialize()

    task = manager.create_task(
        title="Flaky Task",
        description="Testing retries.",
        created_by=AgentRole.DEVELOPER,
        max_retries=2,
    )

    # Fail 1st time -> RETRYING
    failed_1 = manager.fail_task(task.id, "Error 1")
    assert failed_1.retry_count == 1
    assert failed_1.status == TaskStatus.RETRYING

    # Fail 2nd time -> RETRYING
    failed_2 = manager.fail_task(task.id, "Error 2")
    assert failed_2.retry_count == 2
    assert failed_2.status == TaskStatus.RETRYING

    # Fail 3rd time (exceeds max_retries=2) -> FAILED
    failed_3 = manager.fail_task(task.id, "Error 3")
    assert failed_3.retry_count == 3
    assert failed_3.status == TaskStatus.FAILED
    assert failed_3.failed_at is not None

    await manager.shutdown()