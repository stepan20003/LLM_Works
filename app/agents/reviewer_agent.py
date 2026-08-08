"""Reviewer agent implementation responsible for code review, quality gates, and correctness checks."""

import logging
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseWorkerAgent):
    """Specialized quality assurance agent that performs code reviews and approves or requests fixes."""

    role: AgentRole = AgentRole.REVIEWER
    component_id: str = "reviewer-agent"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Review implementation artifacts or test outputs and determine approval or required fixes."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        logger.info(f"ReviewerAgent evaluating task {task_id}")
        content = context_payload.get("content", "")

        # Simulate code review evaluation logic
        # In a fully connected setup, Reviewer checks file diffs or test logs.
        requires_fix = "error" in content.lower() or "fail" in content.lower()

        self.state = AgentState.IDLE
        self.current_task_id = None

        if requires_fix:
            return AgentResponse(
                status=AgentExecutionStatus.NEEDS_FIX,
                message=f"ReviewerAgent found code quality issues or test failures in task {task_id}. Fix required.",
                next_agent=AgentRole.DEVELOPER,
                metadata=Metadata(source_component="reviewer-agent"),
            )

        return AgentResponse(
            status=AgentExecutionStatus.SUCCESS,
            message=f"ReviewerAgent successfully approved task {task_id}.",
            next_agent=AgentRole.MANAGER,
            metadata=Metadata(source_component="reviewer-agent"),
        )