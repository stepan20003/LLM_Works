"""Tests for Project entity, ProjectPlan value objects, and ProjectManager lifecycle."""

import pytest
import pytest_asyncio
from uuid import uuid4

from app.schemas.entities.project import Project
from app.schemas.enums import AgentRole, ProjectStatus, TaskPriority
from app.schemas.value_objects.project_plan import ProjectPlan, SubtaskSpec
from app.projects.project_manager import ProjectManager
from app.exceptions.base import WorkflowError


# ---------------------------------------------------------------------------
# SubtaskSpec tests
# ---------------------------------------------------------------------------

class TestSubtaskSpec:
    """Validation tests for the SubtaskSpec value object."""

    def test_minimal_subtask_spec(self):
        spec = SubtaskSpec(title="Setup DB", description="Create database schema")
        assert spec.title == "Setup DB"
        assert spec.assigned_role == AgentRole.DEVELOPER
        assert spec.priority == TaskPriority.NORMAL
        assert spec.dependencies == []
        assert spec.estimated_duration == 0.0

    def test_full_subtask_spec(self):
        spec = SubtaskSpec(
            title="Write auth module",
            description="Implement JWT authentication",
            assigned_role=AgentRole.DEVELOPER,
            dependencies=["Setup DB"],
            priority=TaskPriority.HIGH,
            estimated_duration=3600.0,
        )
        assert spec.assigned_role == AgentRole.DEVELOPER
        assert spec.dependencies == ["Setup DB"]
        assert spec.priority == TaskPriority.HIGH
        assert spec.estimated_duration == 3600.0

    def test_subtask_spec_rejects_empty_title(self):
        with pytest.raises(Exception):
            SubtaskSpec(title="", description="desc")

    def test_subtask_spec_rejects_negative_duration(self):
        with pytest.raises(Exception):
            SubtaskSpec(title="Task", description="desc", estimated_duration=-1.0)


# ---------------------------------------------------------------------------
# ProjectPlan tests
# ---------------------------------------------------------------------------

class TestProjectPlan:
    """Validation tests for the ProjectPlan value object."""

    def test_minimal_plan(self):
        plan = ProjectPlan(summary="Build an e-commerce platform")
        assert plan.summary == "Build an e-commerce platform"
        assert plan.requirements == []
        assert plan.subtasks == []
        assert plan.acceptance_criteria == []
        assert plan.architecture == ""

    def test_full_plan(self):
        subtask = SubtaskSpec(title="Setup", description="Init project")
        plan = ProjectPlan(
            summary="E-commerce platform",
            requirements=["Auth", "Payments", "Cart"],
            architecture="Microservices with PostgreSQL",
            subtasks=[subtask],
            acceptance_criteria=["All tests pass", "Docker deployment works"],
        )
        assert len(plan.requirements) == 3
        assert len(plan.subtasks) == 1
        assert plan.subtasks[0].title == "Setup"
        assert len(plan.acceptance_criteria) == 2

    def test_plan_rejects_empty_summary(self):
        with pytest.raises(Exception):
            ProjectPlan(summary="")

    def test_plan_with_multiple_subtasks_and_dependencies(self):
        plan = ProjectPlan(
            summary="Complex project",
            subtasks=[
                SubtaskSpec(title="A", description="First task"),
                SubtaskSpec(title="B", description="Depends on A", dependencies=["A"]),
                SubtaskSpec(title="C", description="Depends on A and B", dependencies=["A", "B"]),
            ],
        )
        assert len(plan.subtasks) == 3
        assert plan.subtasks[2].dependencies == ["A", "B"]


# ---------------------------------------------------------------------------
# Project entity tests
# ---------------------------------------------------------------------------

class TestProject:
    """Validation tests for the Project entity."""

    def test_create_minimal_project(self):
        project = Project(prompt="Build a blog")
        assert project.prompt == "Build a blog"
        assert project.status == ProjectStatus.CREATED
        assert project.plan is None
        assert project.summary is None
        assert project.error_message is None
        assert project.tasks == []
        assert project.progress == 0.0
        assert project.completed_at is None
        assert project.failed_at is None

    def test_project_with_plan(self):
        plan = ProjectPlan(summary="Blog app", subtasks=[])
        project = Project(prompt="Build a blog", plan=plan, summary="Blog app")
        assert project.plan.summary == "Blog app"
        assert project.summary == "Blog app"

    def test_project_rejects_completed_at_when_not_done(self):
        from datetime import datetime, timezone
        with pytest.raises(ValueError, match="completed_at cannot exist"):
            Project(
                prompt="Build a blog",
                status=ProjectStatus.CREATED,
                completed_at=datetime.now(timezone.utc),
            )

    def test_project_allows_completed_at_when_done(self):
        from datetime import datetime, timezone
        project = Project(
            prompt="Build a blog",
            status=ProjectStatus.DONE,
            completed_at=datetime.now(timezone.utc),
        )
        assert project.completed_at is not None

    def test_project_allows_completed_at_when_approved(self):
        from datetime import datetime, timezone
        project = Project(
            prompt="Build a blog",
            status=ProjectStatus.APPROVED,
            completed_at=datetime.now(timezone.utc),
        )
        assert project.completed_at is not None

    def test_project_rejects_empty_prompt(self):
        with pytest.raises(Exception):
            Project(prompt="")


# ---------------------------------------------------------------------------
# ProjectManager tests
# ---------------------------------------------------------------------------

class TestProjectManager:
    """Tests for the ProjectManager component."""

    @pytest_asyncio.fixture
    async def pm(self):
        manager = ProjectManager()
        await manager.initialize()
        yield manager
        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_initialize_and_health_check(self, pm):
        assert await pm.health_check() is True

    @pytest.mark.asyncio
    async def test_create_project(self, pm):
        project = pm.create_project(prompt="Build an e-commerce platform")
        assert project.prompt == "Build an e-commerce platform"
        assert project.status == ProjectStatus.CREATED
        assert project.id in pm.projects

    @pytest.mark.asyncio
    async def test_get_project(self, pm):
        project = pm.create_project(prompt="Build a blog")
        retrieved = pm.get_project(project.id)
        assert retrieved.id == project.id
        assert retrieved.prompt == "Build a blog"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, pm):
        with pytest.raises(WorkflowError, match="not found"):
            pm.get_project(uuid4())

    @pytest.mark.asyncio
    async def test_get_all_projects(self, pm):
        assert pm.get_all_projects() == []
        pm.create_project(prompt="Project A")
        pm.create_project(prompt="Project B")
        assert len(pm.get_all_projects()) == 2

    @pytest.mark.asyncio
    async def test_update_project_status(self, pm):
        project = pm.create_project(prompt="Test status")
        updated = pm.update_project_status(project.id, ProjectStatus.PLANNING)
        assert updated.status == ProjectStatus.PLANNING

    @pytest.mark.asyncio
    async def test_update_status_to_done_sets_completed_at(self, pm):
        project = pm.create_project(prompt="Test done")
        updated = pm.update_project_status(project.id, ProjectStatus.DONE)
        assert updated.status == ProjectStatus.DONE
        assert updated.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_to_approved_sets_completed_at(self, pm):
        project = pm.create_project(prompt="Test approved")
        updated = pm.update_project_status(project.id, ProjectStatus.APPROVED)
        assert updated.status == ProjectStatus.APPROVED
        assert updated.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_project_plan(self, pm):
        project = pm.create_project(prompt="Test plan")
        plan = ProjectPlan(
            summary="A simple plan",
            subtasks=[SubtaskSpec(title="Task 1", description="Do something")],
        )
        updated = pm.update_project_plan(project.id, plan)
        assert updated.plan is not None
        assert updated.plan.summary == "A simple plan"
        assert updated.summary == "A simple plan"
        assert updated.status == ProjectStatus.PLANNING

    @pytest.mark.asyncio
    async def test_update_plan_does_not_change_status_if_not_created(self, pm):
        project = pm.create_project(prompt="Test plan status")
        pm.update_project_status(project.id, ProjectStatus.EXECUTING)
        plan = ProjectPlan(summary="Another plan")
        updated = pm.update_project_plan(project.id, plan)
        assert updated.status == ProjectStatus.EXECUTING

    @pytest.mark.asyncio
    async def test_link_task(self, pm):
        project = pm.create_project(prompt="Test linkage")
        task_id = uuid4()
        updated = pm.link_task(project.id, task_id)
        assert task_id in updated.tasks
        # Duplicate linkage should be idempotent
        updated2 = pm.link_task(project.id, task_id)
        assert updated2.tasks.count(task_id) == 1

    @pytest.mark.asyncio
    async def test_update_progress(self, pm):
        project = pm.create_project(prompt="Test progress")
        t1, t2, t3 = uuid4(), uuid4(), uuid4()
        pm.link_task(project.id, t1)
        pm.link_task(project.id, t2)
        pm.link_task(project.id, t3)

        statuses = {t1: "DONE", t2: "DONE", t3: "IN_PROGRESS"}
        updated = pm.update_progress(project.id, statuses)
        assert updated.progress == pytest.approx(66.67, abs=0.1)

    @pytest.mark.asyncio
    async def test_update_progress_all_done(self, pm):
        project = pm.create_project(prompt="Test full progress")
        t1, t2 = uuid4(), uuid4()
        pm.link_task(project.id, t1)
        pm.link_task(project.id, t2)

        statuses = {t1: "DONE", t2: "DONE"}
        updated = pm.update_progress(project.id, statuses)
        assert updated.progress == 100.0

    @pytest.mark.asyncio
    async def test_update_progress_no_tasks(self, pm):
        project = pm.create_project(prompt="Empty project")
        updated = pm.update_progress(project.id, {})
        assert updated.progress == 0.0

    @pytest.mark.asyncio
    async def test_fail_project(self, pm):
        project = pm.create_project(prompt="Test failure")
        failed = pm.fail_project(project.id, "Something went wrong")
        assert failed.status == ProjectStatus.FAILED
        assert failed.error_message == "Something went wrong"
        assert failed.failed_at is not None

    @pytest.mark.asyncio
    async def test_delete_project(self, pm):
        project = pm.create_project(prompt="Delete me")
        pm.delete_project(project.id)
        assert project.id not in pm.projects

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, pm):
        with pytest.raises(WorkflowError, match="not found"):
            pm.delete_project(uuid4())

    @pytest.mark.asyncio
    async def test_shutdown_clears_projects(self, pm):
        pm.create_project(prompt="Will be cleared")
        await pm.shutdown()
        assert len(pm.projects) == 0
        assert await pm.health_check() is False
