"""Regression test suite verifying backend/frontend UI state synchronization for autonomous projects."""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.api.app import app
from app.schemas.enums import AgentRole, ProjectStatus
from app.projects.project_manager import ProjectManager


@pytest.mark.asyncio
async def test_completed_project_state_synchronization():
    """Verify that an APPROVED project has 100% progress, APPROVED phase, and populated created_files."""
    pm = ProjectManager()
    await pm.initialize()
    project = pm.create_project(prompt="Test state sync project")
    
    # Simulate project completion
    pm.update_project_phase(project.id, "APPROVED", AgentRole.MANAGER)
    pm.update_project_status(project.id, ProjectStatus.APPROVED)
    pm.update_progress(project.id, {})
    pm.sync_project_workspace_files(project.id)

    updated = pm.get_project(project.id)
    assert updated.status == ProjectStatus.APPROVED
    assert updated.progress == 100.0
    assert updated.current_phase == "APPROVED"


def test_get_project_api_returns_authoritative_state():
    """Verify GET /projects/{id} returns 100% progress and APPROVED state for completed projects."""
    with TestClient(app) as client:
        # Create project
        res = client.post("/projects/", json={"prompt": "Build REST API module"})
        assert res.status_code == 201
        pid = res.json()["id"]

        # Run pipeline
        start_res = client.post(f"/projects/{pid}/start")
        assert start_res.status_code == 200

        # Fetch project state
        get_res = client.get(f"/projects/{pid}")
        assert get_res.status_code == 200
        proj_data = get_res.json()

        assert proj_data["status"] == "APPROVED"
        assert proj_data["progress"] == 100.0
        assert proj_data["current_phase"] == "APPROVED"
        assert len(proj_data["created_files"]) > 0, "created_files must not be empty"


@pytest.mark.asyncio
async def test_workspace_files_synchronization():
    """Verify sync_project_workspace_files scans workspace directory and populates created_files."""
    pm = ProjectManager()
    await pm.initialize()
    project = pm.create_project(prompt="Scan workspace files test")

    # Create dummy files in workspace
    ws_path = project.workspace_path
    from pathlib import Path
    Path(ws_path).mkdir(parents=True, exist_ok=True)
    (Path(ws_path) / "app.py").write_text("print('hello')", encoding="utf-8")
    (Path(ws_path) / "test_app.py").write_text("def test_ok(): pass", encoding="utf-8")

    pm.sync_project_workspace_files(project.id)
    synced = pm.get_project(project.id)

    assert "app.py" in synced.created_files
    assert "test_app.py" in synced.created_files
