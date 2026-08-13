"""Tests for Phase 3: Project artifact and isolated workspace management."""

import pytest
from pathlib import Path
from app.workspace.local_workspace import LocalWorkspace, get_project_workspace
from app.projects.project_manager import ProjectManager


@pytest.mark.asyncio
async def test_get_project_workspace_factory(tmp_path):
    """Verify factory creates an isolated LocalWorkspace under workspace_dir/projects/{project_id}."""
    ws = get_project_workspace(project_id="proj-123", base_dir=tmp_path)
    await ws.initialize()

    expected_path = tmp_path / "projects" / "proj-123"
    assert Path(ws.root_path).resolve() == expected_path.resolve()
    assert expected_path.exists()

    # Write file inside isolated workspace
    await ws.write_file("src/main.py", "print('hello world')")
    content = await ws.read_file("src/main.py")
    assert content == "print('hello world')"

    files = await ws.list_files()
    assert "src/main.py" in files

    # Verify containment security prevents directory traversal out of project root
    with pytest.raises(ValueError, match="Access denied"):
        await ws.read_file("../../outside.txt")

    await ws.shutdown()


@pytest.mark.asyncio
async def test_project_manager_creates_isolated_workspace(tmp_path, monkeypatch):
    """Verify ProjectManager creates isolated workspace paths automatically."""
    monkeypatch.setattr("app.settings.settings.data_dir", str(tmp_path / "data"))
    monkeypatch.setattr("app.settings.settings.workspace_dir", str(tmp_path / "workspace_sandbox"))

    pm = ProjectManager()
    await pm.initialize()

    project = pm.create_project(prompt="Build isolated app")
    assert project.workspace_path is not None
    assert "projects/" in project.workspace_path
    assert Path(project.workspace_path).exists()

    await pm.shutdown()
