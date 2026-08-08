"""Security-focused tests for ShellTool sandbox containment and safe execution behavior."""

import sys
from pathlib import Path

import pytest

from app.tools.shell_tool import ShellTool
from app.workspace.local_workspace import LocalWorkspace


@pytest.mark.asyncio
async def test_shell_tool_runs_command_inside_workspace(tmp_path: Path) -> None:
    """A simple command should execute successfully when run inside the sandbox root."""
    workspace_dir = tmp_path / "sandbox"
    workspace = LocalWorkspace(component_id="shell-workspace", root_path=str(workspace_dir))
    await workspace.initialize()

    shell_tool = ShellTool(workspace=workspace)
    await shell_tool.initialize()

    result = await shell_tool.execute(command=f"{sys.executable} -c 'print(\"inside workspace\")'")

    assert result.success
    assert "inside workspace" in result.stdout

    await shell_tool.shutdown()
    await workspace.shutdown()


@pytest.mark.asyncio
async def test_shell_tool_allows_valid_workspace_cwd(tmp_path: Path) -> None:
    """A command should be allowed when its cwd is a nested directory inside the workspace."""
    workspace_dir = tmp_path / "sandbox"
    workspace = LocalWorkspace(component_id="cwd-workspace", root_path=str(workspace_dir))
    await workspace.initialize()

    nested_dir = workspace_dir / "nested"
    nested_dir.mkdir(parents=True, exist_ok=True)

    shell_tool = ShellTool(workspace=workspace)
    await shell_tool.initialize()

    result = await shell_tool.execute(
        command=f"{sys.executable} -c 'import os; print(os.getcwd())'",
        cwd="nested",
    )

    assert result.success
    assert str(nested_dir.resolve()) in result.stdout

    await shell_tool.shutdown()
    await workspace.shutdown()


@pytest.mark.asyncio
async def test_shell_tool_rejects_cwd_outside_workspace(tmp_path: Path) -> None:
    """Commands should fail fast when the requested cwd escapes the sandbox."""
    workspace_dir = tmp_path / "sandbox"
    workspace = LocalWorkspace(component_id="outside-cwd-workspace", root_path=str(workspace_dir))
    await workspace.initialize()

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)

    shell_tool = ShellTool(workspace=workspace)
    await shell_tool.initialize()

    result = await shell_tool.execute(
        command=f"{sys.executable} -c 'print(\"noop\")'",
        cwd=str(outside_dir),
    )

    assert not result.success
    assert "Access denied" in result.stderr

    await shell_tool.shutdown()
    await workspace.shutdown()


@pytest.mark.asyncio
async def test_shell_tool_handles_timeout_safely(tmp_path: Path) -> None:
    """Long-running commands should be terminated and reported as a tool failure."""
    workspace_dir = tmp_path / "sandbox"
    workspace = LocalWorkspace(component_id="timeout-workspace", root_path=str(workspace_dir))
    await workspace.initialize()

    shell_tool = ShellTool(workspace=workspace)
    await shell_tool.initialize()

    result = await shell_tool.execute(
        command=f"{sys.executable} -c 'import time; time.sleep(2)'",
        timeout=0.05,
    )

    assert not result.success
    assert result.exit_code == -9
    assert "timed out" in result.stderr.lower()

    await shell_tool.shutdown()
    await workspace.shutdown()


@pytest.mark.asyncio
async def test_shell_tool_truncates_large_output(tmp_path: Path) -> None:
    """Large stdout/stderr should still be truncated according to the tool's existing design."""
    workspace_dir = tmp_path / "sandbox"
    workspace = LocalWorkspace(component_id="truncate-workspace", root_path=str(workspace_dir))
    await workspace.initialize()

    shell_tool = ShellTool(workspace=workspace)
    await shell_tool.initialize()

    command = f"{sys.executable} -c 'import sys; sys.stdout.write(\"x\" * 20000)'"
    result = await shell_tool.execute(command=command)

    assert result.success
    assert result.stdout_truncated
    assert "OUTPUT TRUNCATED" in result.stdout

    await shell_tool.shutdown()
    await workspace.shutdown()


@pytest.mark.asyncio
async def test_shell_tool_returns_structured_failure_for_command_errors(tmp_path: Path) -> None:
    """Command failures should return a structured ToolResult rather than an exception."""
    workspace_dir = tmp_path / "sandbox"
    workspace = LocalWorkspace(component_id="failure-workspace", root_path=str(workspace_dir))
    await workspace.initialize()

    shell_tool = ShellTool(workspace=workspace)
    await shell_tool.initialize()

    result = await shell_tool.execute(
        command=f"{sys.executable} -c 'import sys; sys.stderr.write(\"boom\\n\"); sys.exit(3)'"
    )

    assert not result.success
    assert result.exit_code == 3
    assert "boom" in result.stderr

    await shell_tool.shutdown()
    await workspace.shutdown()
