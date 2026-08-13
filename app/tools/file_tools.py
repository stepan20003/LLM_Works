"""File operation tools leveraging BaseWorkspace for sandboxed filesystem access."""

import logging
from typing import Any
from pydantic import Field

from app.core.base_tool import BaseTool
from app.core.base_workspace import BaseWorkspace
from app.schemas.value_objects.tool_result import ToolResult
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)


class FileTool(BaseTool):
    """Tool for reading, writing, and deleting files inside the sandboxed workspace."""

    component_id: str = "file-tool"
    description: str = "Secure sandboxed file operations (read, write, delete, list)."
    workspace: BaseWorkspace = Field(..., description="Target workspace sandbox instance.")

    async def initialize(self) -> None:
        """Initialize the file tool and target workspace."""
        if hasattr(self, "workspace") and self.workspace and not getattr(self.workspace, "is_initialized", False):
            await self.workspace.initialize()
        self.is_initialized = True
        logger.info("FileTool initialized.")

    async def shutdown(self) -> None:
        """Shutdown the file tool."""
        self.is_initialized = False
        logger.info("FileTool shut down.")

    async def health_check(self) -> bool:
        """Verify tool health."""
        return self.is_initialized and await self.workspace.health_check()

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute file operations based on action parameter ('read', 'write', 'delete', 'list').

        Required kwargs:
            action: str ('read', 'write', 'delete', 'list')
            path: str (relative path, mandatory for read/write/delete)
            content: str (mandatory for 'write')
        """
        self.validate_state()
        action = kwargs.get("action")
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")

        import time
        start_time = time.time()

        try:
            if action == "read":
                if not path:
                    raise ValueError("Path is required for file read operation.")
                file_content = await self.workspace.read_file(path)
                exec_time = time.time() - start_time
                return ToolResult(
                    success=True,
                    stdout=file_content,
                    execution_time=exec_time,
                    metadata=Metadata(source_component="file-tool"),
                )

            elif action == "write":
                if not path:
                    raise ValueError("Path is required for file write operation.")
                await self.workspace.write_file(path, content)
                exec_time = time.time() - start_time
                return ToolResult(
                    success=True,
                    stdout=f"Successfully wrote content to {path}",
                    execution_time=exec_time,
                    metadata=Metadata(source_component="file-tool"),
                )

            elif action == "delete":
                if not path:
                    raise ValueError("Path is required for file delete operation.")
                await self.workspace.delete_file(path)
                exec_time = time.time() - start_time
                return ToolResult(
                    success=True,
                    stdout=f"Successfully deleted {path}",
                    execution_time=exec_time,
                    metadata=Metadata(source_component="file-tool"),
                )

            elif action == "list":
                sub_dir = kwargs.get("sub_dir", "")
                files = await self.workspace.list_files(sub_dir)
                exec_time = time.time() - start_time
                return ToolResult(
                    success=True,
                    stdout="\n".join(files),
                    execution_time=exec_time,
                    metadata=Metadata(source_component="file-tool"),
                )

            else:
                raise ValueError(f"Unknown or unsupported file action: {action}")

        except Exception as e:
            exec_time = time.time() - start_time
            logger.error(f"FileTool execution failed for action '{action}': {e}")
            return ToolResult(
                success=False,
                stderr=str(e),
                exit_code=1,
                execution_time=exec_time,
                metadata=Metadata(source_component="file-tool"),
            )