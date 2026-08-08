"""Message entity schema for communication between agents."""

from typing import Optional
from uuid import UUID
from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from app.schemas.enums import AgentRole, MessageStatus, TaskPriority
from app.schemas.value_objects.attachment import Attachment
from app.schemas.value_objects.metadata import Metadata


class Message(BaseSchema):
    """Represents an asynchronous message exchanged between agents."""

    sender: AgentRole = Field(
        ..., description="Role of the agent sending the message."
    )
    receiver: AgentRole = Field(
        ..., description="Role of the agent receiving the message."
    )
    task_id: UUID = Field(
        ..., description="UUID of the task associated with this message."
    )
    status: MessageStatus = Field(
        ..., description="Current status or intent of the message."
    )
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL, description="Priority level of the message."
    )
    content: str = Field(
        ..., min_length=1, description="Text payload or body of the message."
    )
    attachments: list[Attachment] = Field(
        default_factory=list, description="List of structured file attachments."
    )
    metadata: Metadata = Field(
        default_factory=Metadata, description="Typed entity metadata."
    )
    correlation_id: Optional[UUID] = Field(
        default=None, description="Correlation identifier for tracing request-response flows."
    )
    reply_to: Optional[UUID] = Field(
        default=None, description="UUID of the message this message is replying to."
    )

    @model_validator(mode="after")
    def validate_sender_receiver(self) -> "Message":
        """Validate that the sender and receiver are distinct roles."""
        if self.sender == self.receiver:
            raise ValueError("Message sender and receiver roles cannot be identical.")
        return self