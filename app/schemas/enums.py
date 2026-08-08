"""Centralized enumerations for the AI Development Team platform."""

from enum import StrEnum


class MessageStatus(StrEnum):
    """Status classifications for agent messages."""

    INFO = "INFO"
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    NEEDS_FIX = "NEEDS_FIX"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TaskStatus(StrEnum):
    """Lifecycle states for tasks managed by the orchestrator."""

    CREATED = "CREATED"
    WAITING = "WAITING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    TESTING = "TESTING"
    RETRYING = "RETRYING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class TaskPriority(StrEnum):
    """Priority levels for tasks and messages."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentRole(StrEnum):
    """Specialized roles within the AI development team."""

    SYSTEM = "SYSTEM"
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"
    REVIEWER = "REVIEWER"
    TESTER = "TESTER"


class AgentState(StrEnum):
    """Operational states of an agent during execution."""

    IDLE = "IDLE"
    THINKING = "THINKING"
    WORKING = "WORKING"
    WAITING = "WAITING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"


class AgentExecutionStatus(StrEnum):
    """Execution outcome statuses returned by agents."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NEEDS_FIX = "NEEDS_FIX"
    BLOCKED = "BLOCKED"
    WAITING = "WAITING"


class EventType(StrEnum):
    """Categories of events emitted across the system event bus."""

    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    TASK_CREATED = "TASK_CREATED"
    TASK_UPDATED = "TASK_UPDATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    ERROR = "ERROR"