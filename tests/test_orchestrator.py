import pytest
import pytest_asyncio
from uuid import uuid4
from pydantic import Field

from app.orchestrator.orchestrator import Orchestrator
from app.tasks.task_manager import TaskManager
from app.messaging.message_bus import MessageBus
from app.messaging.event_bus import EventBus
from app.agents.base_worker_agent import BaseWorkerAgent
from app.schemas.enums import (
    AgentExecutionStatus,
    AgentRole,
    TaskStatus,
    EventType,
)
from app.schemas.value_objects.agent_response import AgentResponse


class FakeAgent(BaseWorkerAgent):
    response_status: AgentExecutionStatus = Field(default=AgentExecutionStatus.SUCCESS)

    def __init__(
        self,
        role: AgentRole = AgentRole.DEVELOPER,
        response_status: AgentExecutionStatus = AgentExecutionStatus.SUCCESS,
    ):
        super().__init__(
            component_id=f"fake-{role.value.lower()}",
            role=role,
            response_status=response_status,
        )

    async def process_task(self, task_id, context_payload):
        return AgentResponse(
            status=self.response_status,
            message="Fake agent response",
        )


@pytest_asyncio.fixture
async def orchestrator():
    task_manager = TaskManager()
    message_bus = MessageBus()
    event_bus = EventBus()

    orchestrator_instance = Orchestrator(
        task_manager=task_manager,
        message_bus=message_bus,
        event_bus=event_bus,
    )

    await orchestrator_instance.initialize()

    yield orchestrator_instance

    await orchestrator_instance.shutdown()


@pytest.mark.asyncio
async def test_orchestrator_initializes(orchestrator):
    assert orchestrator.is_initialized is True
    assert await orchestrator.health_check() is True


@pytest.mark.asyncio
async def test_run_iteration_with_no_tasks(orchestrator):
    processed = await orchestrator.run_iteration()
    assert processed == 0


@pytest.mark.asyncio
async def test_successful_task_execution(orchestrator):
    agent = FakeAgent(
        role=AgentRole.DEVELOPER,
        response_status=AgentExecutionStatus.SUCCESS,
    )
    await agent.initialize()

    orchestrator.message_bus.register_agent(agent)

    task = orchestrator.task_manager.create_task(
        title="Test task",
        description="Execute test task",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
    )

    processed = await orchestrator.run_iteration()

    assert processed == 1

    final_task = orchestrator.task_manager.get_task(task.id)

    assert final_task.status == TaskStatus.DONE


@pytest.mark.asyncio
async def test_failed_task_execution(orchestrator):
    agent = FakeAgent(
        role=AgentRole.DEVELOPER,
        response_status=AgentExecutionStatus.FAILED,
    )
    await agent.initialize()

    orchestrator.message_bus.register_agent(agent)

    task = orchestrator.task_manager.create_task(
        title="Failing task",
        description="This task should fail",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
    )

    await orchestrator.run_iteration()

    final_task = orchestrator.task_manager.get_task(task.id)

    assert final_task.status == TaskStatus.READY
    assert final_task.retry_count == 1


@pytest.mark.asyncio
async def test_agent_needs_fix(orchestrator):
    agent = FakeAgent(
        role=AgentRole.DEVELOPER,
        response_status=AgentExecutionStatus.NEEDS_FIX,
    )
    await agent.initialize()

    orchestrator.message_bus.register_agent(agent)

    task = orchestrator.task_manager.create_task(
        title="Needs fix",
        description="Task requiring correction",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
    )

    await orchestrator.run_iteration()

    final_task = orchestrator.task_manager.get_task(task.id)

    assert final_task.status == TaskStatus.READY
    assert final_task.retry_count == 1


@pytest.mark.asyncio
async def test_unregistered_agent_fails_task(orchestrator):
    task = orchestrator.task_manager.create_task(
        title="Unregistered agent",
        description="No agent is registered",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
    )

    await orchestrator.run_iteration()

    final_task = orchestrator.task_manager.get_task(task.id)

    assert final_task.status == TaskStatus.RETRYING
    assert final_task.retry_count == 1


@pytest.mark.asyncio
async def test_task_dependencies_are_respected(orchestrator):
    agent = FakeAgent(
        role=AgentRole.DEVELOPER,
        response_status=AgentExecutionStatus.SUCCESS,
    )
    await agent.initialize()

    orchestrator.message_bus.register_agent(agent)

    first_task = orchestrator.task_manager.create_task(
        title="First task",
        description="First task",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
    )

    second_task = orchestrator.task_manager.create_task(
        title="Second task",
        description="Depends on first",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
        dependencies=[first_task.id],
    )

    # 1-ին իտերացիան գտնում և կատարում է first_task-ը
    await orchestrator.run_iteration()

    assert orchestrator.task_manager.get_task(first_task.id).status == TaskStatus.DONE
    assert orchestrator.task_manager.get_task(second_task.id).status == TaskStatus.CREATED

    # 2-րդ իտերացիան հասկանում է, որ first_task-ն արդեն DONE է, 
    # second_task-ը սարքում է READY և միանգամից կատարում:
    await orchestrator.run_iteration()

    assert orchestrator.task_manager.get_task(second_task.id).status == TaskStatus.DONE

@pytest.mark.asyncio
async def test_events_are_published(orchestrator):
    agent = FakeAgent(
        role=AgentRole.DEVELOPER,
        response_status=AgentExecutionStatus.SUCCESS,
    )
    await agent.initialize()

    orchestrator.message_bus.register_agent(agent)

    received_events = []

    async def listener(event):
        received_events.append(event)

    orchestrator.event_bus.subscribe(
        EventType.TASK_UPDATED,
        listener,
    )

    task = orchestrator.task_manager.create_task(
        title="Event test",
        description="Check events",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
    )

    await orchestrator.run_iteration()

    assert len(received_events) >= 1
    assert received_events[0].task_id == task.id