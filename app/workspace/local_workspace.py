"""Local filesystem implementation of BaseWorkspace for sandboxed operations."""

import os
import aiofiles
import logging
from typing import List
from pathlib import Path
from pydantic import Field
from app.core.base_workspace import BaseWorkspace

logger = logging.getLogger(__name__)


class LocalWorkspace(BaseWorkspace):
    """Concrete workspace managing files inside a specific local directory sandbox."""

    component_id: str = "local-workspace"
    root_path: str = Field(..., description="Root path of the sandbox workspace.")

    async def initialize(self) -> None:
        """Ensure root directory exists."""
        os.makedirs(self.root_path, exist_ok=True)
        self.is_initialized = True
        logger.info(f"LocalWorkspace initialized at root: {self.root_path}")

    async def shutdown(self) -> None:
        """Shutdown workspace."""
        self.is_initialized = False
        logger.info("LocalWorkspace shut down.")

    async def health_check(self) -> bool:
        """Verify root path accessibility."""
        return self.is_initialized and os.path.exists(self.root_path)

    def _get_abs_path(self, relative_path: str) -> str:
        """Resolve and validate path to prevent directory traversal attacks."""
        root_abs = os.path.abspath(self.root_path)
        root_path = Path(root_abs)

        if os.path.isabs(relative_path):
            candidate_path = Path(relative_path)
        else:
            candidate_path = Path(root_abs, relative_path)

        try:
            resolved_path = candidate_path.resolve(strict=False)
        except (RuntimeError, OSError) as exc:
            raise ValueError(f"Access denied: Path '{relative_path}' is invalid.") from exc

        try:
            resolved_root = root_path.resolve(strict=False)
        except (RuntimeError, OSError) as exc:
            raise ValueError(f"Access denied: Workspace root '{self.root_path}' is invalid.") from exc

        if not resolved_path.is_relative_to(resolved_root):
            raise ValueError(f"Access denied: Path '{relative_path}' escapes workspace root.")

        return str(resolved_path)

    async def write_file(self, relative_path: str, content: str) -> None:
        """Write content to a file asynchronously."""
        self.validate_state()
        abs_path = self._get_abs_path(relative_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        async with aiofiles.open(abs_path, mode="w", encoding="utf-8") as f:
            await f.write(content)
        logger.debug(f"File written: {relative_path}")

    async def read_file(self, relative_path: str) -> str:
        """Read content from a file asynchronously."""
        self.validate_state()
        abs_path = self._get_abs_path(relative_path)
        async with aiofiles.open(abs_path, mode="r", encoding="utf-8") as f:
            content = await f.read()
        return content

    async def delete_file(self, relative_path: str) -> None:
        """Delete a file from the workspace."""
        self.validate_state()
        abs_path = self._get_abs_path(relative_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
            logger.debug(f"File deleted: {relative_path}")

    async def list_files(self, sub_dir: str = "") -> List[str]:
        """List all relative file paths inside the workspace or subdirectory."""
        self.validate_state()
        target_dir = self._get_abs_path(sub_dir)
        if not os.path.exists(target_dir):
            return []

        result_files = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.root_path)
                result_files.append(rel_path.replace("\\", "/"))
        return result_files