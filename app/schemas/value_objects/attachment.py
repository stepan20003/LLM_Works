"""Attachment value object representing files or code snippets."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class Attachment(BaseModel):
    """Represents a file or snippet attached to a communication message or artifact list."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    filename: str = Field(
        ..., min_length=1, description="Name of the file or asset."
    )
    mime_type: str = Field(
        default="text/plain", description="MIME type of the attachment."
    )
    size_bytes: int = Field(
        default=0, ge=0, description="Size of the file in bytes."
    )
    checksum: str = Field(
        default="", description="Cryptographic checksum (e.g., SHA-256) of the content."
    )
    path: str = Field(
        ..., min_length=1, description="Filepath in the workspace sandbox."
    )
    snippet: Optional[str] = Field(
        default=None, description="Optional text snippet or preview."
    )