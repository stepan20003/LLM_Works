"""Tests for Phase 2: REST API & WebSocket timeline exposure."""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient
from app.api.app import create_app
from app.schemas.enums import ProjectStatus, AgentExecutionStatus
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata


@pytest.fixture
def api_client():
    app = create_app()
    with TestClient(app) as client:
        # Mock manager_agent.process_task
        mock_plan_response = AgentResponse(
            status=AgentExecutionStatus.SUCCESS,
            message="Plan generated with 1 subtask.",
            metadata=Metadata(
                extra={
                    "plan": {
                        "summary": "Mock auth project",
                        "requirements": ["Auth endpoint"],
                        "architecture": "FastAPI",
                        "subtasks": [
                            {
                                "title": "Create auth schema",
                                "description": "Define Pydantic model",
                                "assigned_role": "DEVELOPER",
                                "dependencies": [],
                                "priority": "HIGH",
                                "estimated_duration": 600.0,
                            }
                        ],
                        "acceptance_criteria": ["Tests pass"],
                    }
                }
            ),
        )
        if hasattr(app.state, "manager_agent") and app.state.manager_agent:
            object.__setattr__(app.state.manager_agent, "process_task", AsyncMock(return_value=mock_plan_response))

        # Mock developer_agent.process_task
        async def mock_dev_process_task(task_id, context_payload):
            ws_path = context_payload.get("workspace_path")
            arch_spec = context_payload.get("architecture_spec")
            created = ["app/main.py", "tests/test_main.py", "pyproject.toml", "README.md"]
            if ws_path:
                from pathlib import Path
                p = Path(ws_path)
                (p / "app").mkdir(parents=True, exist_ok=True)
                (p / "tests").mkdir(parents=True, exist_ok=True)
                (p / "app" / "__init__.py").write_text("", encoding="utf-8")
                (p / "app" / "main.py").write_text("def entrypoint(): return 'OK'\n", encoding="utf-8")
                (p / "tests" / "__init__.py").write_text("", encoding="utf-8")
                (p / "tests" / "test_main.py").write_text("from app.main import entrypoint\ndef test_entrypoint(): assert entrypoint() == 'OK'\n", encoding="utf-8")
                (p / "pyproject.toml").write_text("[project]\nname = 'app'\nversion = '0.1.0'\n", encoding="utf-8")
                (p / "README.md").write_text("# Test App\n", encoding="utf-8")

                if arch_spec and isinstance(arch_spec, dict) and "required_files" in arch_spec:
                    for rf in arch_spec["required_files"]:
                        rf_p = rf.get("path") if isinstance(rf, dict) else str(rf)
                        if rf_p:
                            fp = p / rf_p
                            fp.parent.mkdir(parents=True, exist_ok=True)
                            if not fp.exists():
                                fp.write_text("# Stub file for test\n", encoding="utf-8")
                            created.append(rf_p)

            return AgentResponse(
                status=AgentExecutionStatus.SUCCESS,
                message="Code generated.",
                metadata=Metadata(extra={"created_files": created}),
            )

        if hasattr(app.state, "developer_agent") and app.state.developer_agent:
            object.__setattr__(app.state.developer_agent, "process_task", AsyncMock(side_effect=mock_dev_process_task))

        yield client


def test_project_timeline_and_execution_endpoints(api_client):
    """Test creating a project, fetching timeline, and triggering start pipeline via REST API."""
    # Create project
    create_resp = api_client.post("/projects/", json={"prompt": "Build an authentication service"})
    assert create_resp.status_code == 201
    project_data = create_resp.json()
    project_id = project_data["id"]

    # Get project details
    get_resp = api_client.get(f"/projects/{project_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == project_id

    # Fetch empty timeline initially
    timeline_resp = api_client.get(f"/projects/{project_id}/timeline")
    assert timeline_resp.status_code == 200
    t_data = timeline_resp.json()
    assert t_data["project_id"] == project_id
    assert isinstance(t_data["events"], list)

    # Start project execution pipeline
    start_resp = api_client.post(f"/projects/{project_id}/start")
    assert start_resp.status_code == 200
    updated_project = start_resp.json()
    assert updated_project["status"] in {ProjectStatus.APPROVED.value, ProjectStatus.DONE.value, ProjectStatus.EXECUTING.value}

    # Fetch updated timeline with events
    timeline_resp2 = api_client.get(f"/projects/{project_id}/timeline")
    assert timeline_resp2.status_code == 200
    t_data2 = timeline_resp2.json()
    assert len(t_data2["events"]) > 0
    assert len(t_data2["review_results"]) > 0
    assert len(t_data2["test_results"]) > 0
