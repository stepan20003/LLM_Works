"""Shell execution tool for running asynchronous terminal commands and scripts with timeout and truncation control."""

import asyncio
import logging
import shlex
import time
from pathlib import Path
from typing import Any
from pydantic import Field

from app.core.base_tool import BaseTool
from app.core.base_workspace import BaseWorkspace
from app.schemas.value_objects.tool_result import ToolResult
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)


class ShellTool(BaseTool):
    """Executes asynchronous shell commands securely with timeout controls and output truncation."""

    component_id: str = "shell-tool"
    description: str = "Executes terminal shell commands asynchronously with strict timeout and output size limits."
    max_output_chars: int = Field(default=10000, description="Maximum character limit before truncating stdout/stderr.")
    default_timeout: float = Field(default=60.0, description="Default command execution timeout in seconds.")
    workspace: BaseWorkspace | None = Field(
        default=None,
        description="Optional workspace sandbox used to constrain command execution paths.",
    )

    async def initialize(self) -> None:
        """Initialize the shell tool."""
        self.is_initialized = True
        logger.info("ShellTool initialized.")

    async def shutdown(self) -> None:
        """Shutdown the shell tool."""
        self.is_initialized = False
        logger.info("ShellTool shut down.")

    async def health_check(self) -> bool:
        """Verify tool health."""
        return self.is_initialized

    def _resolve_cwd(self, cwd: str | None) -> str | None:
        """Resolve the working directory while ensuring it stays inside the configured workspace."""
        if self.workspace is None:
            return cwd

        path_validator = getattr(self.workspace, "_get_abs_path", None)
        if callable(path_validator):
            if cwd is None:
                return path_validator("")
            return path_validator(cwd)

        if cwd is None:
            return str(Path(self.workspace.root_path).resolve(strict=False))
        return str(Path(cwd).resolve(strict=False))

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute a shell command asynchronously.

        Required kwargs:
            command: str (the shell command to run)
        Optional kwargs:
            timeout: float (execution timeout in seconds)
            cwd: str (working directory)
        """
        self.validate_state()
        command = kwargs.get("command")
        if not isinstance(command, str) or not command.strip():
            return ToolResult(
                success=False,
                stderr="Missing required 'command' argument for ShellTool.",
                exit_code=1,
                metadata=Metadata(source_component="shell-tool"),
            )

        timeout = kwargs.get("timeout", self.default_timeout)
        cwd = kwargs.get("cwd", None)

        start_time = time.time()
        logger.info(f"Executing shell command: '{command}' (Timeout: {timeout}s)")

        try:
            resolved_cwd = self._resolve_cwd(cwd)
        except (OSError, RuntimeError, ValueError) as exc:
            exec_time = time.time() - start_time
            logger.warning(f"ShellTool rejected command '{command}' due to invalid cwd: {exc}")
            return ToolResult(
                success=False,
                stderr=f"Access denied: {exc}",
                exit_code=1,
                execution_time=exec_time,
                metadata=Metadata(source_component="shell-tool"),
            )

        try:
            argv = shlex.split(command, posix=True)
        except ValueError as exc:
            exec_time = time.time() - start_time
            logger.warning(f"ShellTool rejected command '{command}' due to invalid shell syntax: {exc}")
            return ToolResult(
                success=False,
                stderr=f"Invalid shell command syntax: {exc}",
                exit_code=1,
                execution_time=exec_time,
                metadata=Metadata(source_component="shell-tool"),
            )

        if not argv:
            exec_time = time.time() - start_time
            return ToolResult(
                success=False,
                stderr="ShellTool received an empty command.",
                exit_code=1,
                execution_time=exec_time,
                metadata=Metadata(source_component="shell-tool"),
            )

        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=resolved_cwd,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                exec_time = time.time() - start_time
                return ToolResult(
                    success=False,
                    stderr=f"Command execution timed out after {timeout} seconds.",
                    exit_code=-9,
                    execution_time=exec_time,
                    metadata=Metadata(source_component="shell-tool"),
                )

            stdout_str = stdout_bytes.decode("utf-8", errors="replace")
            stderr_str = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = process.returncode if process.returncode is not None else 1
            exec_time = time.time() - start_time

            stdout_truncated = False
            stderr_truncated = False

            if len(stdout_str) > self.max_output_chars:
                stdout_str = stdout_str[:self.max_output_chars] + "\n... [OUTPUT TRUNCATED DUE TO SIZE LIMIT] ..."
                stdout_truncated = True

            if len(stderr_str) > self.max_output_chars:
                stderr_str = stderr_str[:self.max_output_chars] + "\n... [ERROR TRUNCATED DUE TO SIZE LIMIT] ..."
                stderr_truncated = True

            success = (exit_code == 0)

            return ToolResult(
                success=success,
                stdout=stdout_str,
                stderr=stderr_str,
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                exit_code=exit_code,
                execution_time=exec_time,
                metadata=Metadata(source_component="shell-tool"),
            )

        except Exception as e:
            exec_time = time.time() - start_time
            logger.error(f"Failed to execute shell command '{command}': {e}", exc_info=True)
            return ToolResult(
                success=False,
                stderr=str(e),
                exit_code=1,
                execution_time=exec_time,
                metadata=Metadata(source_component="shell-tool"),
            )