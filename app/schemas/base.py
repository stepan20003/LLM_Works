"""Base Pydantic schema providing common identifier, timestamp, and utility methods."""

from datetime import datetime, timezone
from typing import Any, Self
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Abstract base schema model for all platform entities."""

    model_config = ConfigDict(
        frozen=False,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique universal identifier for the entity.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the entity was created in UTC.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the entity was last updated in UTC.",
    )

    def touch(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = datetime.now(timezone.utc)

    def to_json(self) -> str:
        """Serialize model to a JSON formatted string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Deserialize model from a JSON formatted string."""
        return cls.model_validate_json(json_str)

    def clone(self, **update_values: Any) -> Self:
        """Create a deep copy clone of the model with optional field overrides."""
        data = self.model_dump(exclude={"id", "created_at", "updated_at"})
        data.update(update_values)
        return self.__class__(**data)