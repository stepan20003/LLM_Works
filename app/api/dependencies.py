"""FastAPI dependency injection module using request.app.state."""

from fastapi import Request
from app.tasks.task_manager import TaskManager
from app.orchestrator.orchestrator import Orchestrator


def get_task_manager(request: Request) -> TaskManager:
    """Retrieve TaskManager instance from app state."""
    return request.app.state.task_manager


def get_orchestrator(request: Request) -> Orchestrator:
    """Retrieve Orchestrator instance from app state."""
    return request.app.state.orchestrator