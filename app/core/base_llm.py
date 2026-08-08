"""Base LLM abstract class for language model interactions and structured outputs."""

from abc import abstractmethod
from typing import Any, Optional
from pydantic import Field

from app.core.base_component import BaseComponent


class BaseLLM(BaseComponent):
    """Abstract foundation for multi-provider AI model completions and structured parsing."""

    model_name: str = Field(
        ..., min_length=1, description="Identifier of the underlying language model."
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature controlling randomness and creativity.",
    )

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion asynchronously from the language model."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Any,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Generate a validated structured output conforming to a specified schema."""
        pass