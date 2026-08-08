"""Base workspace abstract class for sandboxed file operations."""

from abc import abstractmethod
from pydantic import Field

from app.core.base_component import BaseComponent


class BaseWorkspace(BaseComponent):
    """Abstract foundation for isolated sandboxed project filesystem management."""

    root_path: str = Field(
        ..., min_length=1, description="Absolute or relative root file path of the sandbox workspace."
    )

    @abstractmethod
    async def write_file(self, relative_path: str, content: str) -> None:
        """Write text content to a target file within the workspace sandbox."""
        pass

    @abstractmethod
    async def read_file(self, relative_path: str) -> str:
        """Read and return string content from a target file within the sandbox."""
        pass

    @abstractmethod
    async def delete_file(self, relative_path: str) -> None:
        """Delete a file within the workspace sandbox."""
        pass

    @abstractmethod
    async def list_files(self, sub_dir: str = "") -> list[str]:
        """List relative paths of all files within a subdirectory or the root sandbox."""
        pass