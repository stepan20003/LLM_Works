"""Tests for Phase 1: Persistent execution state and event-driven timeline."""

import pytest
from uuid import uuid4
from app.schemas.enums import AgentRole, ProjectStatus, EventType
from app.schemas.entities.project import Project
from app.projects.project_manager import ProjectManager


@pytest.mark.asyncio
async def test_project_schema_phase1_fields():
    """Verify that Project entity includes phase 1 fields."""
    project = Project(
        prompt="Build a SaaS dashboard",
        current_agent=AgentRole.MANAGER,
        current_phase="Requirements Analysis",
        workspace_path="/tmp/test_workspace",
    )
    assert project.current_agent == AgentRole.MANAGER
    assert project.current_phase == "Requirements Analysis"
    assert project.workspace_path == "/tmp/test_workspace"
    assert project.timeline_events == []
    assert project.created_files == []
    assert project.modified_files == []
    assert project.test_results == []
    assert project.review_results == []
    assert project.errors_and_retries == []


@pytest.mark.asyncio
async def test_project_manager_timeline_and_tracking(tmp_path, monkeypatch):
    """Verify ProjectManager methods for phase transitions, timeline events, and tracking."""
    monkeypatch.setattr("app.settings.settings.data_dir", str(tmp_path))

    pm = ProjectManager()
    await pm.initialize()

    project = pm.create_project(prompt="Build a CLI tool", workspace_path=str(tmp_path / "sandbox"))
    assert project.status == ProjectStatus.CREATED
    assert project.workspace_path == str(tmp_path / "sandbox")

    # Update phase
    pm.update_project_phase(project.id, phase="Architect: System Design", current_agent=AgentRole.ARCHITECT)
    p = pm.get_project(project.id)
    assert p.current_phase == "Architect: System Design"
    assert p.current_agent == AgentRole.ARCHITECT
    assert len(p.timeline_events) == 1
    assert p.timeline_events[0]["event_type"] == "PROJECT_PHASE_CHANGED"

    # Record file changes
    pm.record_file_change(project.id, "main.py", action="created")
    pm.record_file_change(project.id, "utils.py", action="created")
    pm.record_file_change(project.id, "main.py", action="modified")

    p = pm.get_project(project.id)
    assert "main.py" in p.created_files
    assert "utils.py" in p.created_files
    assert "main.py" not in p.modified_files  # Already in created_files

    # Record test result
    pm.record_test_result(project.id, {"status": "SUCCESS", "passed": 5, "failed": 0, "output": "OK"})
    p = pm.get_project(project.id)
    assert len(p.test_results) == 1
    assert p.test_results[0]["passed"] == 5

    # Record review result
    pm.record_review_result(project.id, {"status": "APPROVED", "comments": "Code looks good", "reviewer": "REVIEWER"})
    p = pm.get_project(project.id)
    assert len(p.review_results) == 1
    assert p.review_results[0]["status"] == "APPROVED"

    # Record error/retry
    pm.record_error_retry(project.id, {"agent": "DEVELOPER", "error": "SyntaxError on line 12", "retry_count": 1})
    p = pm.get_project(project.id)
    assert len(p.errors_and_retries) == 1
    assert p.errors_and_retries[0]["retry_count"] == 1

    await pm.shutdown()
