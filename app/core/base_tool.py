"""Base tool abstract class providing executable capabilities to agents."""

from abc import abstractmethod
from typing import Any
from pydantic import Field

from app.core.base_component import BaseComponent
from app.schemas.value_objects.tool_result import ToolResult


class BaseTool(BaseComponent):
    """Abstract foundation for executable tools (file I/O, terminal commands, etc.)."""

    description: str = Field(
        ..., min_length=1, description="Detailed human-readable description of what the tool does."
    )

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool capability asynchronously with arbitrary keyword arguments."""
        pass