"""Manager agent implementation overseeing project epics, task delegation, and workflow routing."""

import logging
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)


class ManagerAgent(BaseWorkerAgent):
    """Executive oversight agent that interprets project epics, breaks down tasks, and routes workflows."""

    role: AgentRole = AgentRole.MANAGER
    component_id: str = "manager-agent"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Manage workflow direction and delegate high-level objectives."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        logger.info(f"ManagerAgent processing control directive for task {task_id}")
        content = context_payload.get("content", "")

        self.state = AgentState.IDLE
        self.current_task_id = None

        return AgentResponse(
            status=AgentExecutionStatus.SUCCESS,
            message=f"ManagerAgent orchestrated task {task_id} successfully.",
            next_agent=AgentRole.DEVELOPER,
            metadata=Metadata(source_component="manager-agent"),
        )