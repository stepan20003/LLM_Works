"""OpenAI asynchronous LLM client implementation inheriting from BaseLLM."""

import logging
from typing import Any, Optional
from pydantic import Field, SecretStr
from openai import AsyncOpenAI

from app.core.base_llm import BaseLLM
from app.exceptions.base import ConfigurationError

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLM):
    """Enterprise-grade asynchronous OpenAI LLM client supporting completions and structured outputs."""

    component_id: str = "openai-client"
    api_key: SecretStr = Field(..., description="API key for authentication with OpenAI or compatible provider.")
    base_url: Optional[str] = Field(default=None, description="Optional custom base URL for compatible APIs (e.g., DeepSeek, Groq).")
    client: Optional[AsyncOpenAI] = Field(default=None, exclude=True, description="Underlying AsyncOpenAI client instance.")

    async def initialize(self) -> None:
        """Initialize the AsyncOpenAI client instance."""
        try:
            self.client = AsyncOpenAI(
                api_key=self.api_key.get_secret_value(),
                base_url=self.base_url,
            )
            self.is_initialized = True
            logger.info(f"OpenAIClient initialized successfully for model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAIClient: {e}", exc_info=True)
            raise ConfigurationError(f"OpenAIClient initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Close client sessions and mark as uninitialized."""
        if self.client:
            # AsyncOpenAI manages its HTTP client sessions under the hood, but we clear reference
            self.client = None
        self.is_initialized = False
        logger.info("OpenAIClient shut down.")

    async def health_check(self) -> bool:
        """Verify client availability and initialization state."""
        return self.is_initialized and self.client is not None

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion asynchronously using the configured model."""
        self.validate_state()
        if not self.client:
            raise RuntimeError("OpenAIClient is not active.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                **kwargs,
            )
            content = response.choices[0].message.content
            return content if content is not None else ""
        except Exception as e:
            logger.error(f"Error generating completion with model {self.model_name}: {e}", exc_info=True)
            raise

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Any,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Generate a structured output conforming strictly to a provided Pydantic schema using response_format."""
        self.validate_state()
        if not self.client:
            raise RuntimeError("OpenAIClient is not active.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # Utilizing OpenAI's native beta parsed structured outputs or standard JSON schema parsing
            completion = await self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=messages,
                response_format=response_schema,
                temperature=self.temperature,
                **kwargs,
            )
            return completion.choices[0].message.parsed
        except Exception as e:
            logger.error(f"Error generating structured output with model {self.model_name}: {e}", exc_info=True)
            raise