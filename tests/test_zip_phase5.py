"""Tests for Phase 5: ZIP packaging and download endpoint."""

import pytest
import zipfile
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.api.app import create_app
from app.schemas.enums import AgentExecutionStatus
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata


@pytest.fixture
def api_client():
    app = create_app()
    with TestClient(app) as client:
        # Mock manager_agent.process_task
        mock_plan_response = AgentResponse(
            status=AgentExecutionStatus.SUCCESS,
            message="Plan generated.",
            metadata=Metadata(
                extra={
                    "plan": {
                        "summary": "Mock zip project",
                        "requirements": ["Zip test"],
                        "architecture": "FastAPI",
                        "subtasks": [
                            {
                                "title": "Create zip model",
                                "description": "Model spec",
                                "assigned_role": "DEVELOPER",
                                "dependencies": [],
                                "priority": "HIGH",
                                "estimated_duration": 300.0,
                            }
                        ],
                        "acceptance_criteria": ["ZIP contains 6 reports"],
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


def test_download_project_zip_endpoint(api_client):
    """Test creating a project, running pipeline, and downloading the completed ZIP archive."""
    create_resp = api_client.post("/projects/", json={"prompt": "Build an e-commerce zip test"})
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    start_resp = api_client.post(f"/projects/{project_id}/start")
    assert start_resp.status_code == 200

    # Download ZIP endpoint
    download_resp = api_client.get(f"/projects/{project_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/zip"

    # Verify ZIP contents in memory
    import io
    zip_bytes = download_resp.content
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = z.namelist()
        assert any(f.endswith("README.md") for f in names)
        assert any(f.endswith("REQUIREMENTS.md") for f in names)
        assert any(f.endswith("ARCHITECTURE.md") for f in names)
        assert any(f.endswith("TEST_REPORT.md") for f in names)
        assert any(f.endswith("PROJECT_REPORT.md") for f in names)
        assert any(f.endswith("CHANGELOG.md") for f in names)
