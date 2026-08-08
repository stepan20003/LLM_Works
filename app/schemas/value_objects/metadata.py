"""Centralized metadata value object for platform entities."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class Metadata(BaseModel):
    """Structured and typed metadata container for tracking operational context."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    version: str = Field(
        default="1.0.0", description="Schema version of the metadata payload."
    )
    source_component: str = Field(
        default="system", description="Component or service that generated the metadata."
    )
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary extensible key-value pairs."
    )