"""Regression test suite verifying that generated projects are real, complete, runnable, and packaged into valid ZIP archives."""

import pytest
import zipfile
import tempfile
import sys
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient

from app.api.app import app
from app.projects.project_manager import ProjectManager
from app.schemas.enums import AgentRole, ProjectStatus


@pytest.mark.asyncio
async def test_developer_agent_creates_physical_source_files(tmp_path):
    """Verify DeveloperAgent creates physical source files in the project workspace."""
    from app.agents.developer_agent import DeveloperAgent
    from app.tools.file_tools import FileTool
    from app.tools.shell_tool import ShellTool
    from app.workspace.local_workspace import LocalWorkspace
    from uuid import uuid4

    ws_dir = tmp_path / "project_ws"
    ws_dir.mkdir()

    ws = LocalWorkspace(root_path=str(ws_dir))
    await ws.initialize()

    file_tool = FileTool(workspace=ws)
    shell_tool = ShellTool(workspace=ws)
    await file_tool.initialize()
    await shell_tool.initialize()

    dev_agent = DeveloperAgent(component_id="dev-test")
    dev_agent.register_tool("file_tool", file_tool)
    dev_agent.register_tool("shell_tool", shell_tool)
    await dev_agent.initialize()

    res = await dev_agent.process_task(
        task_id=uuid4(),
        context_payload={
            "content": "Build a math operations module with unit tests.",
            "workspace_path": str(ws_dir),
        },
    )

    assert res.status.value == "SUCCESS"
    assert (ws_dir / "app" / "main.py").exists() or (ws_dir / "calculator.py").exists() or len(list(ws_dir.glob("*.py"))) > 0


@pytest.mark.asyncio
async def test_create_project_zip_contains_runnable_files_and_passes_validation():
    """Verify create_project_zip creates clean archive with source code and passes programmatic ZIP validation."""
    pm = ProjectManager()
    await pm.initialize()

    project = pm.create_project(prompt="Build a fast utility library")
    ws_path = Path(project.workspace_path)
    ws_path.mkdir(parents=True, exist_ok=True)

    # Add source code, test, and config files
    (ws_path / "app").mkdir(exist_ok=True)
    (ws_path / "tests").mkdir(exist_ok=True)
    (ws_path / "app" / "utility.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (ws_path / "tests" / "test_utility.py").write_text("from app.utility import add\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    (ws_path / "pyproject.toml").write_text("[project]\nname = 'utility'\nversion = '0.1.0'\n", encoding="utf-8")
    (ws_path / "README.md").write_text("# Utility Library\n", encoding="utf-8")

    pm.sync_project_workspace_files(project.id)
    zip_path = pm.create_project_zip(project.id)

    assert zip_path.exists()
    zip_info = pm.validate_project_zip(zip_path)

    assert zip_info["has_source_file"] is True
    assert zip_info["file_count"] >= 4

    # Extract ZIP into temp directory and run pytest on extracted project
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        temp_path = Path(temp_dir)
        extracted_files = list(temp_path.rglob("*"))
        source_files = [f for f in extracted_files if f.name == "test_utility.py"]
        assert len(source_files) > 0, "Extracted archive must contain test_utility.py"

        # Execute pytest on extracted project
        import os
        proj_root = source_files[0].parent.parent
        cmd = [sys.executable, "-m", "pytest", "-v", str(proj_root / "tests")]
        env = {**os.environ, "PYTHONPATH": str(proj_root)}
        proc = subprocess.run(cmd, cwd=str(proj_root), capture_output=True, text=True, env=env)
        assert proc.returncode == 0, f"Extracted project tests failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"


def test_e2e_full_project_zip_download_and_execution():
    """End-to-end test creating project via API, verifying ZIP content, extracting and executing pytest."""
    import os
    with TestClient(app) as client:
        res = client.post("/projects/", json={"prompt": "Build a simple calculator module with pytest tests."})
        assert res.status_code == 201
        pid = res.json()["id"]

        start_res = client.post(f"/projects/{pid}/start")
        assert start_res.status_code == 200

        dl_res = client.get(f"/projects/{pid}/download")
        assert dl_res.status_code == 200
        assert len(dl_res.content) > 0

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_zip = Path(temp_dir) / "downloaded.zip"
            temp_zip.write_bytes(dl_res.content)

            with zipfile.ZipFile(temp_zip, "r") as zf:
                namelist = zf.namelist()
                has_py = any(f.endswith(".py") for f in namelist)
                assert has_py, f"Downloaded ZIP must contain .py files: {namelist}"

                extract_dir = Path(temp_dir) / "extracted"
                zf.extractall(extract_dir)

            py_tests = list(extract_dir.rglob("test_*.py"))
            assert len(py_tests) > 0, "Extracted project must contain pytest test files"

            # Execute pytest on extracted project
            proj_root = py_tests[0].parent.parent
            cmd = [sys.executable, "-m", "pytest", "-v", str(py_tests[0].parent)]
            env = {**os.environ, "PYTHONPATH": str(proj_root)}
            proc = subprocess.run(cmd, cwd=str(proj_root), capture_output=True, text=True, env=env)
            assert proc.returncode == 0, f"Extracted project pytest failed:\n{proc.stdout}\n{proc.stderr}"
