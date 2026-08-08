"""Centralized exception hierarchy for the AI Development Team platform."""


class FrameworkError(Exception):
    """Base exception for all platform-specific errors."""

    pass


class AgentError(FrameworkError):
    """Raised when an agent encounters an unrecoverable execution or operational error."""

    pass


class WorkflowError(FrameworkError):
    """Raised when orchestrator, task workflow, or dependency evaluation fails."""

    pass


class ToolError(FrameworkError):
    """Raised when a tool execution (FileTool, ShellTool, etc.) fails."""

    pass


class ConfigurationError(FrameworkError):
    """Raised when application settings, environment variables, or schema configs are invalid."""

    pass