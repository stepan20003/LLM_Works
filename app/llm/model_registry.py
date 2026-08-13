"""Model Registry for managing available LLM definitions and client instantiation."""

import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.core.base_llm import BaseLLM
from app.llm.openai_client import OpenAIClient
from app.settings.settings import settings

logger = logging.getLogger(__name__)


class ModelDefinition(BaseModel):
    """Definition of an LLM model configuration."""
    model_id: str = Field(..., description="Unique identifier for the model config (e.g., 'groq/llama-3.1-8b')")
    provider: str = Field(..., description="Provider type (e.g., 'openai', 'groq')")
    model_name: str = Field(..., description="Actual model name passed to the client")
    base_url: Optional[str] = Field(default=None, description="Custom base URL if applicable")
    temperature: float = Field(default=0.2, description="Default temperature")


class ModelRegistry:
    """Registry to store and instantiate models dynamically."""

    def __init__(self):
        self._models: Dict[str, ModelDefinition] = {}
        self.register_default_models()

    def register_model(self, definition: ModelDefinition) -> None:
        """Register a new model definition."""
        self._models[definition.model_id] = definition
        logger.info(f"Registered model definition: {definition.model_id}")

    def register_default_models(self) -> None:
        """Register standard default and common provider models."""
        # Default fallback model from global settings
        self.register_model(
            ModelDefinition(
                model_id="default",
                provider=settings.provider,
                model_name=settings.llm_model,
                base_url=settings.base_url,
                temperature=settings.temperature,
            )
        )
        # Groq fast model
        self.register_model(
            ModelDefinition(
                model_id="groq/llama-3.1-8b",
                provider="openai",
                model_name="llama-3.1-8b-instant",
                base_url="https://api.groq.com/openai/v1",
                temperature=settings.temperature,
            )
        )
        # OpenAI GPT-4o
        self.register_model(
            ModelDefinition(
                model_id="openai/gpt-4o",
                provider="openai",
                model_name="gpt-4o",
                base_url=None,
                temperature=settings.temperature,
            )
        )

    def get_model_definition(self, model_id: str) -> ModelDefinition:
        """Retrieve model definition by ID with fallback to default."""
        if model_id not in self._models:
            logger.warning(f"Model ID '{model_id}' not found in registry. Falling back to 'default'.")
            return self._models.get("default", ModelDefinition(
                model_id="default",
                provider=settings.provider,
                model_name=settings.llm_model,
                base_url=settings.base_url,
                temperature=settings.temperature,
            ))
        return self._models[model_id]

    def create_client(self, model_id: str, api_key: Optional[str] = None) -> BaseLLM:
        """Instantiate a BaseLLM client based on the registered model definition."""
        definition = self.get_model_definition(model_id)
        resolved_api_key = api_key or settings.openai_api_key

        if definition.provider.lower() in ["openai", "groq", "compatible"]:
            return OpenAIClient(
                model_name=definition.model_name,
                temperature=definition.temperature,
                api_key=resolved_api_key,
                base_url=definition.base_url,
            )
        else:
            raise ValueError(f"Unsupported provider: {definition.provider}")


# Global model registry instance
model_registry = ModelRegistry()