"""Plan executor: materializes a ProjectPlan into real Task entities with dependency resolution."""

import logging
from collections import defaultdict, deque
from typing import Optional
from uuid import UUID

from app.schemas.enums import AgentRole, ProjectStatus
from app.schemas.value_objects.project_plan import ProjectPlan, SubtaskSpec
from app.schemas.entities.project import Project
from app.tasks.task_manager import TaskManager
from app.projects.project_manager import ProjectManager
from app.exceptions.base import WorkflowError

logger = logging.getLogger(__name__)


class DependencyCycleError(WorkflowError):
    """Raised when a dependency cycle is detected in the plan."""
    pass


class DuplicateSubtaskError(WorkflowError):
    """Raised when duplicate subtask titles are detected in the plan."""
    pass


def validate_dependency_graph(subtasks: list[SubtaskSpec]) -> list[str]:
    """Validate the dependency graph and return a topologically sorted list of titles.

    Raises:
        DependencyCycleError: If a cycle is detected.
        DuplicateSubtaskError: If duplicate titles exist.
        WorkflowError: If a dependency references a non-existent subtask.

    Returns:
        List of subtask titles in topological execution order.
    """
    titles = [s.title for s in subtasks]

    # Check for duplicate titles
    seen = set()
    for title in titles:
        if title in seen:
            raise DuplicateSubtaskError(f"Duplicate subtask title: '{title}'")
        seen.add(title)

    title_set = set(titles)

    # Validate all dependency references exist
    for subtask in subtasks:
        for dep in subtask.dependencies:
            if dep not in title_set:
                raise WorkflowError(
                    f"Subtask '{subtask.title}' depends on '{dep}' which does not exist in the plan."
                )

    # Build adjacency list and in-degree map for Kahn's algorithm
    in_degree: dict[str, int] = {title: 0 for title in titles}
    adjacency: dict[str, list[str]] = defaultdict(list)

    for subtask in subtasks:
        for dep in subtask.dependencies:
            # dep -> subtask (dep must come before subtask)
            adjacency[dep].append(subtask.title)
            in_degree[subtask.title] += 1

    # Kahn's algorithm for topological sort
    queue: deque[str] = deque()
    for title in titles:
        if in_degree[title] == 0:
            queue.append(title)

    sorted_titles: list[str] = []
    while queue:
        current = queue.popleft()
        sorted_titles.append(current)
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_titles) != len(titles):
        # Find the cycle participants for a helpful error message
        cycle_members = [t for t in titles if in_degree[t] > 0]
        raise DependencyCycleError(
            f"Dependency cycle detected involving subtasks: {cycle_members}"
        )

    return sorted_titles


class PlanExecutor:
    """Converts a validated ProjectPlan into real Task entities via TaskManager."""

    def __init__(self, task_manager: TaskManager, project_manager: ProjectManager):
        self.task_manager = task_manager
        self.project_manager = project_manager

    def execute_plan(self, project_id: UUID) -> list[UUID]:
        """Materialize a project's plan into Task entities.

        Steps:
            1. Retrieve the project and validate it has a plan.
            2. Validate the dependency graph (cycle detection).
            3. Create tasks in topological order.
            4. Map title-based dependencies to UUID-based dependencies.
            5. Link all created tasks to the project.
            6. Update project status to EXECUTING.

        Args:
            project_id: UUID of the project whose plan to execute.

        Returns:
            List of created Task UUIDs in execution order.

        Raises:
            WorkflowError: If the project has no plan or dependencies are invalid.
            DependencyCycleError: If a cycle is detected.
        """
        project = self.project_manager.get_project(project_id)

        if project.plan is None:
            raise WorkflowError(f"Project {project_id} has no plan to execute.")

        if not project.plan.subtasks:
            logger.warning(f"Project {project_id} plan has no subtasks.")
            self.project_manager.update_project_status(project_id, ProjectStatus.EXECUTING)
            return []

        plan = project.plan

        # Step 1: Validate and get topological order
        sorted_titles = validate_dependency_graph(plan.subtasks)

        # Build a lookup from title -> SubtaskSpec
        spec_by_title: dict[str, SubtaskSpec] = {s.title: s for s in plan.subtasks}

        # Step 2: Create tasks in topological order, mapping title deps -> UUID deps
        title_to_uuid: dict[str, UUID] = {}
        created_task_ids: list[UUID] = []

        for title in sorted_titles:
            spec = spec_by_title[title]

            # Resolve title-based dependencies to UUIDs
            uuid_deps = [title_to_uuid[dep] for dep in spec.dependencies]

            task = self.task_manager.create_task(
                title=spec.title,
                description=spec.description,
                created_by=AgentRole.MANAGER,
                assigned_to=spec.assigned_role,
                priority=spec.priority,
                estimated_duration=spec.estimated_duration,
                dependencies=uuid_deps,
            )
            task.metadata.extra["workspace_path"] = project.workspace_path
            task.metadata.extra["project_id"] = str(project_id)
            if project.architecture_spec:
                task.metadata.extra["architecture_spec"] = project.architecture_spec
            self.task_manager.tasks[task.id] = task

            title_to_uuid[title] = task.id
            created_task_ids.append(task.id)

            # Link task to project
            self.project_manager.link_task(project_id, task.id)

        # Step 3: Move project to EXECUTING
        self.project_manager.update_project_status(project_id, ProjectStatus.EXECUTING)

        logger.info(
            f"Plan executed for project {project_id}: "
            f"{len(created_task_ids)} tasks created in dependency order."
        )

        return created_task_ids
