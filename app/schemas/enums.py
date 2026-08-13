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
    ARCHITECT = "ARCHITECT"
    DEVELOPER = "DEVELOPER"
    REVIEWER = "REVIEWER"
    TESTER = "TESTER"
    DEBUGGER = "DEBUGGER"


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

    # Messaging and core task lifecycle
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    TASK_CREATED = "TASK_CREATED"
    TASK_UPDATED = "TASK_UPDATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    ERROR = "ERROR"
    
    # Project planning & timeline
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_PLANNED = "PROJECT_PLANNED"
    PROJECT_PHASE_CHANGED = "PROJECT_PHASE_CHANGED"
    PROJECT_TIMELINE_EVENT = "PROJECT_TIMELINE_EVENT"
    PROJECT_APPROVED = "PROJECT_APPROVED"
    PROJECT_FAILED = "PROJECT_FAILED"

    # Agent execution loop
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_THINKING = "AGENT_THINKING"
    AGENT_ACTION = "AGENT_ACTION"
    MODEL_SELECTED = "MODEL_SELECTED"

    # Tools and workspace
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_FINISHED = "TOOL_FINISHED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    FILE_CHANGED = "FILE_CHANGED"

    # Verification and testing
    TEST_STARTED = "TEST_STARTED"
    TEST_FINISHED = "TEST_FINISHED"
    DEBUG_STARTED = "DEBUG_STARTED"
    REVIEW_STARTED = "REVIEW_STARTED"
    REVIEW_RESULT = "REVIEW_RESULT"
    RETRY_STARTED = "RETRY_STARTED"


class ProjectStatus(StrEnum):
    """Lifecycle statuses for a high-level software engineering project."""
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    TESTING = "TESTING"
    REVIEWING = "REVIEWING"
    BLOCKED = "BLOCKED"
    APPROVED = "APPROVED"
    FAILED = "FAILED"
    DONE = "DONE"