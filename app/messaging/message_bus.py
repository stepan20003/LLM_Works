"""Point-to-point asynchronous message broker for agent-to-agent communication."""

import logging
from typing import Optional

from app.core.base_component import BaseComponent
from app.core.base_agent import BaseAgent
from app.schemas.enums import AgentRole, MessageStatus
from app.schemas.entities.message import Message
from app.schemas.value_objects.agent_response import AgentResponse
from app.exceptions.base import AgentError

logger = logging.getLogger(__name__)


class MessageBus(BaseComponent):
    """Manages agent registration, validation, and point-to-point message routing."""

    component_id: str = "message-bus"
    agents: dict[AgentRole, BaseAgent] = {}

    async def initialize(self) -> None:
        """Initialize the message bus framework."""
        self.agents = {}
        self.is_initialized = True
        logger.info("MessageBus initialized successfully.")

    async def shutdown(self) -> None:
        """Shutdown and clear all registered agent mappings."""
        self.agents.clear()
        self.is_initialized = False
        logger.info("MessageBus shut down and agent registry cleared.")

    async def health_check(self) -> bool:
        """Verify operational health of the message bus."""
        return self.is_initialized

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent instance into the system by its specialized role."""
        self.validate_state()
        if agent.role in self.agents:
            logger.warning(f"Overwriting existing agent registration for role: {agent.role}")
        self.agents[agent.role] = agent
        logger.info(f"Agent '{agent.component_id}' registered with role '{agent.role}'.")

    async def dispatch(self, message: Message) -> Optional[AgentResponse]:
        """Route an asynchronous message from sender to target receiver agent."""
        self.validate_state()

        receiver_role = message.receiver
        if receiver_role == AgentRole.SYSTEM:
            logger.info(f"System-targeted message processed: {message.content}")
            return None

        if receiver_role not in self.agents:
            raise AgentError(
                f"Message dispatch failed: Target receiver role '{receiver_role}' is not registered."
            )

        target_agent = self.agents[receiver_role]
        logger.debug(f"Dispatching message {message.id} from {message.sender} to {receiver_role}")

        try:
            response = await target_agent.handle_message(message)
            return response
        except Exception as e:
            logger.error(f"Error handling message {message.id} at agent {receiver_role}: {e}")
            raise AgentError(f"Agent {receiver_role} failed to process message: {e}") from e