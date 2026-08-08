"""LLM Router managing model selection and client routing based on task complexity or agent role."""

import logging
from typing import Optional
from pydantic import Field

from app.core.base_component import BaseComponent
from app.core.base_llm import BaseLLM
from app.schemas.enums import AgentRole

logger = logging.getLogger(__name__)


class LLMRouter(BaseComponent):
    """Routes LLM requests to specific model clients depending on agent roles or task complexity."""

    component_id: str = "llm-router"
    default_client: BaseLLM = Field(..., description="Default fallback LLM client instance.")
    role_clients: dict[AgentRole, BaseLLM] = Field(
        default_factory=dict, description="Mapping of specialized agent roles to dedicated LLM clients."
    )

    async def initialize(self) -> None:
        """Initialize router and all managed LLM clients."""
        if not await self.default_client.health_check():
            await self.default_client.initialize()

        for role, client in self.role_clients.items():
            if not await client.health_check():
                await client.initialize()

        self.is_initialized = True
        logger.info("LLMRouter initialized successfully.")

    async def shutdown(self) -> None:
        """Shutdown default client and all role-specific clients."""
        await self.default_client.shutdown()
        for client in self.role_clients.values():
            await client.shutdown()
        self.is_initialized = False
        logger.info("LLMRouter shut down.")

    async def health_check(self) -> bool:
        """Verify health of router and registered clients."""
        if not self.is_initialized:
            return False
        if not await self.default_client.health_check():
            return False
        for client in self.role_clients.values():
            if not await client.health_check():
                return False
        return True

    def register_role_client(self, role: AgentRole, client: BaseLLM) -> None:
        """Register a specialized LLM client for a specific agent role."""
        self.validate_state()
        self.role_clients[role] = client
        logger.info(f"Registered dedicated LLM client for role: {role} (Model: {client.model_name})")

    def get_client_for_role(self, role: AgentRole) -> BaseLLM:
        """Retrieve the appropriate LLM client for an agent role, falling back to default if unassigned."""
        self.validate_state()
        client = self.role_clients.get(role, self.default_client)
        logger.debug(f"Routing LLM request for role '{role}' to model '{client.model_name}'")
        return client