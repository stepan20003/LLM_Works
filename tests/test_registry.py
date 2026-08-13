"""Tests for Model Registry and Agent Registry integration."""

import pytest
from app.llm.model_registry import ModelRegistry, ModelDefinition
from app.llm.router import LLMRouter
from app.agents.registry import AgentRegistry
from app.schemas.enums import AgentRole


def test_model_registry_custom_model():
    registry = ModelRegistry()
    registry.register_model(
        ModelDefinition(
            model_id="custom/test-model",
            provider="openai",
            model_name="test-model-name",
            temperature=0.5,
        )
    )
    defn = registry.get_model_definition("custom/test-model")
    assert defn.model_name == "test-model-name"
    assert defn.temperature == 0.5


def test_model_registry_fallback():
    registry = ModelRegistry()
    defn = registry.get_model_definition("non-existent-model")
    assert defn.model_id == "default"


@pytest.mark.asyncio
async def test_agent_registry_instantiation():
    model_reg = ModelRegistry()
    router = LLMRouter.from_settings()
    await router.initialize()  # Կարևոր է՝ ակտիվացնում ենք ռոութերը նախքան օգտագործելը

    agent_reg = AgentRegistry(llm_router=router)

    # Instantiate manager agent
    manager = agent_reg.create_agent(AgentRole.MANAGER)
    assert manager is not None
    assert manager.role == AgentRole.MANAGER
    assert agent_reg.get_agent(AgentRole.MANAGER) == manager

    # Մաքրման համար
    await router.shutdown()