"""Tests for ManagerAgent structured planning capabilities."""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.agents.manager_agent import ManagerAgent
from app.core.base_llm import BaseLLM
from app.schemas.enums import AgentExecutionStatus, AgentRole
from app.schemas.value_objects.project_plan import ProjectPlan


# ---------------------------------------------------------------------------
# Fake LLM for testing
# ---------------------------------------------------------------------------

class FakeLLM(BaseLLM):
    """A fake LLM that returns pre-configured responses."""

    model_config = {"arbitrary_types_allowed": True}

    component_id: str = "fake-llm"
    model_name: str = "fake-model"
    _completion_response: str = ""
    _structured_response: object = None
    _structured_raises: bool = False

    def set_completion_response(self, text: str) -> None:
        object.__setattr__(self, "_completion_response", text)

    def set_structured_response(self, response: object) -> None:
        object.__setattr__(self, "_structured_response", response)

    def set_structured_raises(self, should_raise: bool) -> None:
        object.__setattr__(self, "_structured_raises", should_raise)

    async def generate_completion(self, prompt, system_prompt=None, **kwargs):
        return self._completion_response

    async def generate_structured(self, prompt, response_schema=None, system_prompt=None, **kwargs):
        if self._structured_raises:
            raise NotImplementedError("Structured generation not supported")
        if self._structured_response is not None:
            return self._structured_response
        raise NotImplementedError("No structured response configured")

    async def initialize(self):
        self.is_initialized = True

    async def shutdown(self):
        self.is_initialized = False

    async def health_check(self):
        return self.is_initialized


VALID_PLAN_JSON = json.dumps({
    "summary": "E-commerce platform with authentication and payments",
    "requirements": ["User auth", "Product catalog", "Payment processing"],
    "architecture": "Monolith with PostgreSQL",
    "subtasks": [
        {
            "title": "Setup database",
            "description": "Create PostgreSQL schema and models",
            "assigned_role": "DEVELOPER",
            "dependencies": [],
            "priority": "HIGH",
            "estimated_duration": 3600.0,
        },
        {
            "title": "Implement auth",
            "description": "JWT-based authentication module",
            "assigned_role": "DEVELOPER",
            "dependencies": ["Setup database"],
            "priority": "HIGH",
            "estimated_duration": 7200.0,
        },
        {
            "title": "Write tests",
            "description": "Unit and integration tests",
            "assigned_role": "TESTER",
            "dependencies": ["Setup database", "Implement auth"],
            "priority": "NORMAL",
            "estimated_duration": 3600.0,
        },
    ],
    "acceptance_criteria": ["All tests pass", "Docker deployment works"],
})


# ---------------------------------------------------------------------------
# ManagerAgent planning tests
# ---------------------------------------------------------------------------

class TestManagerAgentPlanning:
    """Test structured planning capabilities of the ManagerAgent."""

    @pytest_asyncio.fixture
    async def fake_llm(self):
        llm = FakeLLM()
        await llm.initialize()
        yield llm
        await llm.shutdown()

    @pytest_asyncio.fixture
    async def manager(self, fake_llm):
        agent = ManagerAgent(component_id="test-manager", llm=fake_llm)
        await agent.initialize()
        yield agent
        await agent.shutdown()

    @pytest.mark.asyncio
    async def test_planning_with_structured_generation(self, manager, fake_llm):
        """When generate_structured works, the plan should come from it."""
        expected_plan = ProjectPlan(**json.loads(VALID_PLAN_JSON))
        fake_llm.set_structured_response(expected_plan)

        response = await manager.process_task(
            task_id=uuid4(),
            context_payload={"project_prompt": "Build an e-commerce platform", "content": ""},
        )

        assert response.status == AgentExecutionStatus.SUCCESS
        assert "3 subtasks" in response.message
        plan_data = response.metadata.extra.get("plan")
        assert plan_data is not None
        assert plan_data["summary"] == "E-commerce platform with authentication and payments"
        assert len(plan_data["subtasks"]) == 3

    @pytest.mark.asyncio
    async def test_planning_falls_back_to_completion(self, manager, fake_llm):
        """When generate_structured raises, fallback to generate_completion + JSON parse."""
        fake_llm.set_structured_raises(True)
        fake_llm.set_completion_response(VALID_PLAN_JSON)

        response = await manager.process_task(
            task_id=uuid4(),
            context_payload={"project_prompt": "Build a blog", "content": ""},
        )

        assert response.status == AgentExecutionStatus.SUCCESS
        plan_data = response.metadata.extra.get("plan")
        assert plan_data is not None
        assert len(plan_data["subtasks"]) == 3

    @pytest.mark.asyncio
    async def test_planning_fallback_with_markdown_fences(self, manager, fake_llm):
        """Handle LLM output wrapped in markdown code blocks."""
        fake_llm.set_structured_raises(True)
        fake_llm.set_completion_response(f"```json\n{VALID_PLAN_JSON}\n```")

        response = await manager.process_task(
            task_id=uuid4(),
            context_payload={"project_prompt": "Build a blog", "content": ""},
        )

        assert response.status == AgentExecutionStatus.SUCCESS
        plan_data = response.metadata.extra.get("plan")
        assert plan_data is not None
        assert plan_data["summary"] == "E-commerce platform with authentication and payments"

    @pytest.mark.asyncio
    async def test_planning_handles_malformed_output(self, manager, fake_llm):
        """When the LLM returns unparseable text, a minimal fallback plan is produced."""
        fake_llm.set_structured_raises(True)
        fake_llm.set_completion_response("I'm sorry, I can't help with that.")

        response = await manager.process_task(
            task_id=uuid4(),
            context_payload={"project_prompt": "Build something", "content": ""},
        )

        # Should still succeed — the fallback plan has no subtasks but a summary
        assert response.status == AgentExecutionStatus.SUCCESS
        plan_data = response.metadata.extra.get("plan")
        assert plan_data is not None
        assert len(plan_data["subtasks"]) == 0
        assert "sorry" in plan_data["summary"].lower()

    @pytest.mark.asyncio
    async def test_default_behavior_without_project_prompt(self, manager):
        """Without project_prompt, the ManagerAgent uses the default pass-through behavior."""
        response = await manager.process_task(
            task_id=uuid4(),
            context_payload={"content": "Just a regular task"},
        )

        assert response.status == AgentExecutionStatus.SUCCESS
        assert "orchestrated" in response.message.lower()
        # No plan in metadata
        assert response.metadata.extra == {}

    @pytest.mark.asyncio
    async def test_planning_without_llm_uses_default_behavior(self):
        """If no LLM is attached, even with a project_prompt, default behavior is used."""
        agent = ManagerAgent(component_id="no-llm-manager", llm=None)
        await agent.initialize()

        response = await agent.process_task(
            task_id=uuid4(),
            context_payload={"project_prompt": "Build something", "content": ""},
        )

        assert response.status == AgentExecutionStatus.SUCCESS
        assert "orchestrated" in response.message.lower()
        await agent.shutdown()
