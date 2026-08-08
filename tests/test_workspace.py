"""Unit tests for LocalWorkspace sandboxed filesystem and security isolation."""

import os
import pytest
from pathlib import Path

from app.workspace.local_workspace import LocalWorkspace


@pytest.mark.asyncio
async def test_workspace_file_operations(tmp_path: Path) -> None:
    """Verify asynchronous writing, reading, listing, and deleting of files in sandbox."""
    workspace_dir = str(tmp_path / "sandbox")
    workspace = LocalWorkspace(component_id="test-workspace", root_path=workspace_dir)
    await workspace.initialize()

    # Write file
    rel_path = "test_dir/hello.txt"
    content = "Hello, AI Development Team!"
    await workspace.write_file(rel_path, content)

    # Read file
    read_content = await workspace.read_file(rel_path)
    assert read_content == content

    # List files
    files = await workspace.list_files()
    normalized_files = [f.replace("\\", "/") for f in files]
    assert "test_dir/hello.txt" in normalized_files

    # Delete file
    await workspace.delete_file(rel_path)
    files_after = await workspace.list_files()
    assert len(files_after) == 0

    await workspace.shutdown()


@pytest.mark.asyncio
async def test_path_traversal_security(tmp_path: Path) -> None:
    """Verify that directory traversal and absolute/sibling paths outside the sandbox are rejected."""
    workspace_dir = str(tmp_path / "sandbox")
    workspace = LocalWorkspace(component_id="security-workspace", root_path=workspace_dir)
    await workspace.initialize()

    with pytest.raises(ValueError, match="Access denied"):
        await workspace.write_file("../outside.txt", "Malicious content")

    with pytest.raises(ValueError, match="Access denied"):
        await workspace.read_file("../../etc/passwd")

    with pytest.raises(ValueError, match="Access denied"):
        await workspace.delete_file(str(tmp_path / "outside.txt"))

    with pytest.raises(ValueError, match="Access denied"):
        await workspace.write_file(str(tmp_path / "sandbox-other" / "escaped.txt"), "Bad")

    await workspace.shutdown()


@pytest.mark.asyncio
async def test_workspace_path_validation_allows_safe_paths_and_blocks_symlink_escape(tmp_path: Path) -> None:
    """Verify safe paths remain accessible while symlink escape attempts are blocked."""
    workspace_dir = tmp_path / "sandbox"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    workspace = LocalWorkspace(component_id="safe-paths-workspace", root_path=str(workspace_dir))
    await workspace.initialize()

    await workspace.write_file("nested/hello.txt", "inside sandbox")
    read_content = await workspace.read_file("nested/hello.txt")
    assert read_content == "inside sandbox"

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / "link").symlink_to(outside_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="Access denied"):
        await workspace.read_file("link/escaped.txt")

    await workspace.shutdown()