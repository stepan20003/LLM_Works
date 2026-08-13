"""Tests for PlanExecutor: dependency graph validation, cycle detection, and plan materialization."""

import pytest
import pytest_asyncio
from uuid import uuid4

from app.projects.plan_executor import (
    PlanExecutor,
    DependencyCycleError,
    DuplicateSubtaskError,
    validate_dependency_graph,
)
from app.projects.project_manager import ProjectManager
from app.tasks.task_manager import TaskManager
from app.schemas.enums import AgentRole, ProjectStatus, TaskPriority, TaskStatus
from app.schemas.value_objects.project_plan import ProjectPlan, SubtaskSpec
from app.exceptions.base import WorkflowError


# ---------------------------------------------------------------------------
# validate_dependency_graph tests
# ---------------------------------------------------------------------------

class TestValidateDependencyGraph:
    """Tests for the standalone dependency graph validation function."""

    def test_linear_chain(self):
        """A -> B -> C should produce [A, B, C]."""
        subtasks = [
            SubtaskSpec(title="A", description="First"),
            SubtaskSpec(title="B", description="Second", dependencies=["A"]),
            SubtaskSpec(title="C", description="Third", dependencies=["B"]),
        ]
        order = validate_dependency_graph(subtasks)
        assert order.index("A") < order.index("B") < order.index("C")

    def test_diamond_pattern(self):
        """
        A -> B
        A -> C
        B -> D
        C -> D
        """
        subtasks = [
            SubtaskSpec(title="A", description="Root"),
            SubtaskSpec(title="B", description="Left", dependencies=["A"]),
            SubtaskSpec(title="C", description="Right", dependencies=["A"]),
            SubtaskSpec(title="D", description="Join", dependencies=["B", "C"]),
        ]
        order = validate_dependency_graph(subtasks)
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_independent_tasks(self):
        """Tasks with no dependencies should all be valid."""
        subtasks = [
            SubtaskSpec(title="X", description="Independent 1"),
            SubtaskSpec(title="Y", description="Independent 2"),
            SubtaskSpec(title="Z", description="Independent 3"),
        ]
        order = validate_dependency_graph(subtasks)
        assert set(order) == {"X", "Y", "Z"}

    def test_empty_list(self):
        """Empty subtask list should return empty."""
        order = validate_dependency_graph([])
        assert order == []

    def test_single_task(self):
        """Single task with no deps."""
        subtasks = [SubtaskSpec(title="Solo", description="Only task")]
        order = validate_dependency_graph(subtasks)
        assert order == ["Solo"]

    def test_cycle_two_nodes(self):
        """A -> B -> A should raise DependencyCycleError."""
        subtasks = [
            SubtaskSpec(title="A", description="First", dependencies=["B"]),
            SubtaskSpec(title="B", description="Second", dependencies=["A"]),
        ]
        with pytest.raises(DependencyCycleError, match="cycle"):
            validate_dependency_graph(subtasks)

    def test_cycle_three_nodes(self):
        """A -> B -> C -> A should raise DependencyCycleError."""
        subtasks = [
            SubtaskSpec(title="A", description="First", dependencies=["C"]),
            SubtaskSpec(title="B", description="Second", dependencies=["A"]),
            SubtaskSpec(title="C", description="Third", dependencies=["B"]),
        ]
        with pytest.raises(DependencyCycleError, match="cycle"):
            validate_dependency_graph(subtasks)

    def test_self_cycle(self):
        """A task depending on itself should be detected."""
        subtasks = [
            SubtaskSpec(title="A", description="Self-dep", dependencies=["A"]),
        ]
        with pytest.raises(DependencyCycleError, match="cycle"):
            validate_dependency_graph(subtasks)

    def test_duplicate_titles(self):
        """Duplicate titles should raise DuplicateSubtaskError."""
        subtasks = [
            SubtaskSpec(title="Setup", description="First setup"),
            SubtaskSpec(title="Setup", description="Duplicate setup"),
        ]
        with pytest.raises(DuplicateSubtaskError, match="Duplicate"):
            validate_dependency_graph(subtasks)

    def test_nonexistent_dependency(self):
        """Referencing a non-existent subtask should raise WorkflowError."""
        subtasks = [
            SubtaskSpec(title="A", description="Task", dependencies=["Ghost"]),
        ]
        with pytest.raises(WorkflowError, match="does not exist"):
            validate_dependency_graph(subtasks)

    def test_complex_dag(self):
        """
        A (root)
        B depends on A
        C depends on A
        D depends on B, C
        E depends on C
        F depends on D, E
        """
        subtasks = [
            SubtaskSpec(title="A", description="Root"),
            SubtaskSpec(title="B", description="Left", dependencies=["A"]),
            SubtaskSpec(title="C", description="Right", dependencies=["A"]),
            SubtaskSpec(title="D", description="Mid", dependencies=["B", "C"]),
            SubtaskSpec(title="E", description="Right-child", dependencies=["C"]),
            SubtaskSpec(title="F", description="Final", dependencies=["D", "E"]),
        ]
        order = validate_dependency_graph(subtasks)
        # Verify all ordering constraints
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")
        assert order.index("C") < order.index("E")
        assert order.index("D") < order.index("F")
        assert order.index("E") < order.index("F")


# ---------------------------------------------------------------------------
# PlanExecutor tests
# ---------------------------------------------------------------------------

class TestPlanExecutor:
    """Tests for the PlanExecutor that materializes plans into tasks."""

    @pytest_asyncio.fixture
    async def managers(self):
        tm = TaskManager()
        pm = ProjectManager()
        await tm.initialize()
        await pm.initialize()
        yield tm, pm
        await tm.shutdown()
        await pm.shutdown()

    def _make_executor(self, tm, pm):
        return PlanExecutor(task_manager=tm, project_manager=pm)

    @pytest.mark.asyncio
    async def test_execute_linear_plan(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Linear plan",
            subtasks=[
                SubtaskSpec(title="A", description="First task"),
                SubtaskSpec(title="B", description="Second task", dependencies=["A"]),
                SubtaskSpec(title="C", description="Third task", dependencies=["B"]),
            ],
        )
        project = pm.create_project(prompt="Test linear")
        pm.update_project_plan(project.id, plan)

        task_ids = executor.execute_plan(project.id)

        assert len(task_ids) == 3

        # Verify tasks exist in TaskManager
        for tid in task_ids:
            task = tm.get_task(tid)
            assert task is not None

        # Verify dependency wiring
        task_a = tm.get_task(task_ids[0])
        task_b = tm.get_task(task_ids[1])
        task_c = tm.get_task(task_ids[2])

        assert task_a.title == "A"
        assert task_a.dependencies == []
        assert task_b.title == "B"
        assert task_b.dependencies == [task_a.id]
        assert task_c.title == "C"
        assert task_c.dependencies == [task_b.id]

    @pytest.mark.asyncio
    async def test_execute_diamond_plan(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Diamond plan",
            subtasks=[
                SubtaskSpec(title="Root", description="Start"),
                SubtaskSpec(title="Left", description="Left branch", dependencies=["Root"]),
                SubtaskSpec(title="Right", description="Right branch", dependencies=["Root"]),
                SubtaskSpec(title="Join", description="Merge", dependencies=["Left", "Right"]),
            ],
        )
        project = pm.create_project(prompt="Test diamond")
        pm.update_project_plan(project.id, plan)

        task_ids = executor.execute_plan(project.id)
        assert len(task_ids) == 4

        # Find the join task and verify it depends on both branches
        tasks_by_title = {tm.get_task(tid).title: tm.get_task(tid) for tid in task_ids}
        join_task = tasks_by_title["Join"]
        assert len(join_task.dependencies) == 2
        assert tasks_by_title["Left"].id in join_task.dependencies
        assert tasks_by_title["Right"].id in join_task.dependencies

    @pytest.mark.asyncio
    async def test_execute_independent_tasks(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Parallel tasks",
            subtasks=[
                SubtaskSpec(title="A", description="Independent 1"),
                SubtaskSpec(title="B", description="Independent 2"),
                SubtaskSpec(title="C", description="Independent 3"),
            ],
        )
        project = pm.create_project(prompt="Test parallel")
        pm.update_project_plan(project.id, plan)

        task_ids = executor.execute_plan(project.id)
        assert len(task_ids) == 3

        # All tasks should have no dependencies
        for tid in task_ids:
            assert tm.get_task(tid).dependencies == []

    @pytest.mark.asyncio
    async def test_execute_sets_project_status_to_executing(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Status test",
            subtasks=[SubtaskSpec(title="Task", description="A task")],
        )
        project = pm.create_project(prompt="Status test")
        pm.update_project_plan(project.id, plan)

        executor.execute_plan(project.id)

        updated_project = pm.get_project(project.id)
        assert updated_project.status == ProjectStatus.EXECUTING

    @pytest.mark.asyncio
    async def test_execute_links_tasks_to_project(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Linkage test",
            subtasks=[
                SubtaskSpec(title="A", description="First"),
                SubtaskSpec(title="B", description="Second"),
            ],
        )
        project = pm.create_project(prompt="Linkage test")
        pm.update_project_plan(project.id, plan)

        task_ids = executor.execute_plan(project.id)

        updated_project = pm.get_project(project.id)
        assert len(updated_project.tasks) == 2
        for tid in task_ids:
            assert tid in updated_project.tasks

    @pytest.mark.asyncio
    async def test_execute_assigns_roles_and_priorities(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Role assignment",
            subtasks=[
                SubtaskSpec(
                    title="Write code",
                    description="Implement feature",
                    assigned_role=AgentRole.DEVELOPER,
                    priority=TaskPriority.HIGH,
                ),
                SubtaskSpec(
                    title="Review code",
                    description="Code review",
                    assigned_role=AgentRole.REVIEWER,
                    priority=TaskPriority.NORMAL,
                    dependencies=["Write code"],
                ),
            ],
        )
        project = pm.create_project(prompt="Role test")
        pm.update_project_plan(project.id, plan)

        task_ids = executor.execute_plan(project.id)

        dev_task = tm.get_task(task_ids[0])
        review_task = tm.get_task(task_ids[1])

        assert dev_task.assigned_to == AgentRole.DEVELOPER
        assert dev_task.priority == TaskPriority.HIGH
        assert review_task.assigned_to == AgentRole.REVIEWER
        assert review_task.priority == TaskPriority.NORMAL

    @pytest.mark.asyncio
    async def test_execute_no_plan_raises_error(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        project = pm.create_project(prompt="No plan")

        with pytest.raises(WorkflowError, match="no plan"):
            executor.execute_plan(project.id)

    @pytest.mark.asyncio
    async def test_execute_empty_subtasks(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(summary="Empty plan", subtasks=[])
        project = pm.create_project(prompt="Empty")
        pm.update_project_plan(project.id, plan)

        task_ids = executor.execute_plan(project.id)
        assert task_ids == []

        updated = pm.get_project(project.id)
        assert updated.status == ProjectStatus.EXECUTING

    @pytest.mark.asyncio
    async def test_execute_rejects_cycle(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Cycle plan",
            subtasks=[
                SubtaskSpec(title="A", description="Depends on B", dependencies=["B"]),
                SubtaskSpec(title="B", description="Depends on A", dependencies=["A"]),
            ],
        )
        project = pm.create_project(prompt="Cycle test")
        pm.update_project_plan(project.id, plan)

        with pytest.raises(DependencyCycleError, match="cycle"):
            executor.execute_plan(project.id)

    @pytest.mark.asyncio
    async def test_execute_rejects_duplicates(self, managers):
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Duplicate plan",
            subtasks=[
                SubtaskSpec(title="Setup", description="First"),
                SubtaskSpec(title="Setup", description="Duplicate"),
            ],
        )
        project = pm.create_project(prompt="Duplicate test")
        pm.update_project_plan(project.id, plan)

        with pytest.raises(DuplicateSubtaskError, match="Duplicate"):
            executor.execute_plan(project.id)

    @pytest.mark.asyncio
    async def test_tasks_are_ready_after_dependencies_complete(self, managers):
        """Verify that TaskManager.get_ready_tasks works with the created dependency graph."""
        tm, pm = managers
        executor = self._make_executor(tm, pm)

        plan = ProjectPlan(
            summary="Ready test",
            subtasks=[
                SubtaskSpec(title="First", description="Root task"),
                SubtaskSpec(title="Second", description="Depends on first", dependencies=["First"]),
            ],
        )
        project = pm.create_project(prompt="Ready test")
        pm.update_project_plan(project.id, plan)

        task_ids = executor.execute_plan(project.id)

        # Initially only "First" should be ready (no deps)
        ready = tm.get_ready_tasks()
        ready_titles = [t.title for t in ready]
        assert "First" in ready_titles
        assert "Second" not in ready_titles

        # Complete "First"
        tm.update_task_status(task_ids[0], TaskStatus.DONE)

        # Now "Second" should become ready
        ready = tm.get_ready_tasks()
        ready_titles = [t.title for t in ready]
        assert "Second" in ready_titles
