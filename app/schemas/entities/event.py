"""Event entity schema for system-wide telemetry and event dispatching."""

from collections.abc import Mapping
from typing import Any, Optional
from uuid import UUID
from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.enums import AgentRole, EventType
from app.schemas.value_objects.metadata import Metadata


class Event(BaseSchema):
    """Represents a system event emitted across the event broker."""

    event_type: EventType = Field(
        ..., description="Classification category of the event."
    )
    source_agent: Optional[AgentRole] = Field(
        default=None, description="Agent role that triggered the event."
    )
    destination_agent: Optional[AgentRole] = Field(
        default=None, description="Target agent role for the event."
    )
    task_id: Optional[UUID] = Field(
        default=None, description="Optional associated task UUID."
    )
    payload: Mapping[str, Any] = Field(
        default_factory=dict, description="Immutable structured event payload data."
    )
    metadata: Metadata = Field(
        default_factory=Metadata, description="Typed entity metadata."
    )