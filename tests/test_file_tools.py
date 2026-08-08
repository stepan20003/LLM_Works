import pytest
import pytest_asyncio
from pathlib import Path

from app.tools.file_tools import FileTool
from app.workspace.local_workspace import LocalWorkspace

@pytest_asyncio.fixture
async def workspace(tmp_path: Path):
    ws = LocalWorkspace(component_id="test-ws", root_path=str(tmp_path))
    await ws.initialize()
    yield ws
    await ws.shutdown()

@pytest_asyncio.fixture
async def file_tool(workspace: LocalWorkspace):
    tool = FileTool(workspace=workspace)
    await tool.initialize()
    yield tool
    await tool.shutdown()

@pytest.mark.asyncio
async def test_file_tool_write_and_read(file_tool: FileTool):
    # 1. Գրում ենք ֆայլ
    write_result = await file_tool.execute(
        action="write", 
        path="hello.txt", 
        content="Hello AI Agent!"
    )
    assert write_result.success is True

    # 2. Կարդում ենք ֆայլը և ստուգում պարունակությունը
    read_result = await file_tool.execute(
        action="read", 
        path="hello.txt"
    )
    assert read_result.success is True
    assert read_result.stdout == "Hello AI Agent!"

@pytest.mark.asyncio
async def test_file_tool_list_and_delete(file_tool: FileTool):
    # 1. Ստեղծում ենք ֆայլ
    await file_tool.execute(action="write", path="temp/data.txt", content="data")
    
    # 2. Ցուցակագրում ենք
    list_result = await file_tool.execute(action="list")
    assert list_result.success is True
    assert "temp/data.txt" in list_result.stdout.replace("\\", "/")

    # 3. Ջնջում ենք ֆայլը
    delete_result = await file_tool.execute(action="delete", path="temp/data.txt")
    assert delete_result.success is True

    # 4. Ստուգում ենք, որ ջնջվել է
    list_after_delete = await file_tool.execute(action="list")
    assert "temp/data.txt" not in list_after_delete.stdout.replace("\\", "/")

@pytest.mark.asyncio
async def test_file_tool_invalid_action_and_missing_paths(file_tool: FileTool):
    # Սխալ action
    invalid_action = await file_tool.execute(action="hack")
    assert invalid_action.success is False
    assert "Unknown or unsupported" in invalid_action.stderr

    # Բացակայող path
    missing_path = await file_tool.execute(action="read")
    assert missing_path.success is False
    assert "Path is required" in missing_path.stderr