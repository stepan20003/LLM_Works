"""Tester agent implementation responsible for executing test suites and verifying code behavior."""

import logging
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)


class TesterAgent(BaseWorkerAgent):
    """Specialized quality engineering agent that executes automated tests and analyzes outcomes."""

    role: AgentRole = AgentRole.TESTER
    component_id: str = "tester-agent"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Execute automated tests via ShellTool, analyze output, and report test outcomes."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        logger.info(f"TesterAgent starting test execution for task {task_id}")
        content = context_payload.get("content", "")

        try:
            shell_tool = self.tools.get("shell_tool")
            if not shell_tool:
                self.state = AgentState.IDLE
                self.current_task_id = None
                return AgentResponse(
                    status=AgentExecutionStatus.FAILED,
                    message="TesterAgent execution failed: 'shell_tool' is not registered to the agent.",
                    next_agent=AgentRole.MANAGER,
                    metadata=Metadata(source_component="tester-agent"),
                )

            # Determine test command (default to pytest, or extract from context if provided)
            test_command = context_payload.get("command", "pytest")
            logger.info(f"Running test suite command: '{test_command}'")

            tool_result = await shell_tool.execute(command=test_command)

            self.state = AgentState.IDLE
            self.current_task_id = None

            if tool_result.success:
                return AgentResponse(
                    status=AgentExecutionStatus.SUCCESS,
                    message=f"TesterAgent verified task {task_id}: All tests passed successfully.\nStdout: {tool_result.stdout}",
                    artifacts=tool_result.artifacts,
                    next_agent=AgentRole.REVIEWER,
                    metadata=Metadata(source_component="tester-agent"),
                )
            else:
                return AgentResponse(
                    status=AgentExecutionStatus.NEEDS_FIX,
                    message=f"TesterAgent found failing tests for task {task_id}.\nStderr: {tool_result.stderr}\nStdout: {tool_result.stdout}",
                    artifacts=tool_result.artifacts,
                    next_agent=AgentRole.DEVELOPER,
                    metadata=Metadata(source_component="tester-agent"),
                )

        except Exception as e:
            logger.error(f"TesterAgent encountered unexpected exception on task {task_id}: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.current_task_id = None
            return AgentResponse(
                status=AgentExecutionStatus.FAILED,
                message=f"TesterAgent encountered exception during test run: {str(e)}",
                next_agent=AgentRole.MANAGER,
                metadata=Metadata(source_component="tester-agent"),
            )