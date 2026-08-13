"""Agent Registry for managing and instantiating specialized agent workers with dynamic model routing."""

import logging
from typing import Dict, Type, Optional, Any

from app.core.base_agent import BaseAgent
from app.llm.router import LLMRouter
from app.schemas.enums import AgentRole
from app.agents.manager_agent import ManagerAgent
from app.agents.architect_agent import ArchitectAgent
from app.agents.developer_agent import DeveloperAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.tester_agent import TesterAgent
from app.agents.debugger_agent import DebuggerAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry to register, configure, and instantiate agent workers."""

    def __init__(self, llm_router: LLMRouter, event_bus: Optional[Any] = None):
        self.llm_router = llm_router
        self.event_bus = event_bus
        self._agent_classes: Dict[AgentRole, Type[BaseAgent]] = {
            AgentRole.MANAGER: ManagerAgent,
            AgentRole.ARCHITECT: ArchitectAgent,
            AgentRole.DEVELOPER: DeveloperAgent,
            AgentRole.REVIEWER: ReviewerAgent,
            AgentRole.TESTER: TesterAgent,
            AgentRole.DEBUGGER: DebuggerAgent,
        }
        self._active_agents: Dict[AgentRole, BaseAgent] = {}

    def register_agent_class(self, role: AgentRole, agent_class: Type[BaseAgent]) -> None:
        """Register a new agent class for a given role (allows extending with Debugger, Architect, etc.)."""
        self._agent_classes[role] = agent_class
        logger.info(f"Registered agent class for role: {role}")

    def create_agent(self, role: AgentRole, component_id: Optional[str] = None, **kwargs) -> BaseAgent:
        """Instantiate an agent of a specific role, attaching the appropriate LLM client from the router."""
        if role not in self._agent_classes:
            raise ValueError(f"No agent class registered for role: {role}")

        agent_class = self._agent_classes[role]
        llm_client = self.llm_router.get_client_for_role(role)
        resolved_id = component_id or f"{role.value.lower()}-agent-1"

        # Most BaseWorkerAgents accept llm/llm_client or similar parameters depending on implementation.
        # Let's instantiate safely based on standard signature or kwargs.
        try:
            agent = agent_class(
                component_id=resolved_id,
                role=role,
                llm=llm_client,
                event_bus=self.event_bus,
                **kwargs
            )
        except TypeError:
            # Fallback if initialization signature differs slightly
            agent = agent_class(
                component_id=resolved_id,
                role=role,
                event_bus=self.event_bus,
                **kwargs
            )

        self._active_agents[role] = agent
        logger.info(f"Instantiated agent '{resolved_id}' for role '{role}' using model '{llm_client.model_name}'")
        return agent

    def get_agent(self, role: AgentRole) -> Optional[BaseAgent]:
        """Retrieve an already instantiated active agent by role."""
        return self._active_agents.get(role)

    def get_all_active_agents(self) -> Dict[AgentRole, BaseAgent]:
        """Return all currently active agents."""
        return self._active_agents