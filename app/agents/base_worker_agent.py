"""Base worker agent providing tool management and lifecycle capabilities for specialized agents."""

import logging
from typing import Any, Optional
from uuid import UUID
from pydantic import Field
from app.core.base_llm import BaseLLM  # <--- Ավելացված է
from app.core.base_agent import BaseAgent
from app.core.base_tool import BaseTool
from app.schemas.enums import AgentRole, AgentState
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.entities.message import Message

logger = logging.getLogger(__name__)


class BaseWorkerAgent(BaseAgent):
    """Abstract foundation for worker agents, managing registered tools and lifecycle hooks."""

    tools: dict[str, BaseTool] = Field(
        default_factory=dict, description="Registry of tools available to the agent."
    )
    llm: Optional[BaseLLM] = Field(  # <--- Ավելացված է
        default=None, description="Dedicated LLM client for this agent."
    )
    def register_tool(self, name: str, tool: BaseTool) -> None:
        """Register an executable tool into the agent's capability set."""
        self.tools[name] = tool
        logger.debug(f"Agent '{self.component_id}' registered tool: '{name}'")

    async def initialize(self) -> None:
        """Initialize the agent and all its registered tools."""
        for name, tool in self.tools.items():
            if not await tool.health_check():
                await tool.initialize()
        self.is_initialized = True
        logger.info(f"Worker agent '{self.component_id}' ({self.role}) initialized with {len(self.tools)} tools.")

    async def shutdown(self) -> None:
        """Shutdown the agent and cleanup tools."""
        for tool in self.tools.values():
            await tool.shutdown()
        self.tools.clear()
        self.is_initialized = False
        logger.info(f"Worker agent '{self.component_id}' shut down.")

    async def health_check(self) -> bool:
        """Verify operational health of the agent and its tools."""
        if not self.is_initialized:
            return False
        for tool in self.tools.values():
            if not await tool.health_check():
                return False
        return True

    async def handle_message(self, message: Message) -> Optional[AgentResponse]:
        """Process an incoming message by invoking process_task if task_id is present."""
        self.validate_state()
        self.state = AgentState.THINKING
        logger.info(f"Agent {self.role} received message from {message.sender} regarding task {message.task_id}")

        try:
            # Delegate handling to process_task using message content as context payload
            response = await self.process_task(
                task_id=message.task_id,
                context_payload={"content": message.content, "metadata": message.metadata},
            )
            self.state = AgentState.IDLE
            return response
        except Exception as e:
            logger.error(f"Agent {self.role} failed to handle message: {e}", exc_info=True)
            self.state = AgentState.FAILED
            raise