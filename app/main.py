"""End-to-end integration demo runner executing a complete multi-agent workflow loop."""

import asyncio
import logging
import sys
from pydantic import SecretStr

from app.workspace.local_workspace import LocalWorkspace
from app.tasks.task_manager import TaskManager
from app.messaging.message_bus import MessageBus
from app.messaging.event_bus import EventBus
from app.orchestrator.orchestrator import Orchestrator
from app.tools.file_tools import FileTool
from app.tools.shell_tool import ShellTool
from app.agents.developer_agent import DeveloperAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.manager_agent import ManagerAgent
from app.llm.openai_client import OpenAIClient
from app.settings.settings import settings
from app.schemas.enums import AgentRole, TaskPriority, EventType
from app.schemas.entities.event import Event

# Configure logging to output clear execution steps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("AI-Dev-Team-Demo")


async def event_logger_listener(event: Event) -> None:
    """Global event listener callback printing telemetry events in real-time."""
    print(f"   [EVENT BUS TELEMETRY] Type: {event.event_type.value} | Source: {event.source_agent} -> Target: {event.destination_agent} | Task: {event.task_id}")


async def main() -> None:
    """Initialize all subsystems, register agents and tools, create a task, and run the orchestrator loop."""
    logger.info("=== Starting AI Development Team Framework Demo ===")

    # 1. Initialize Core Subsystems
    workspace = LocalWorkspace(component_id="sandbox-workspace", root_path="./workspace_sandbox")
    await workspace.initialize()

    task_manager = TaskManager()
    await task_manager.initialize()

    message_bus = MessageBus()
    await message_bus.initialize()

    event_bus = EventBus()
    await event_bus.initialize()

    # Subscribe telemetry logger to all key event types
    for ev_type in EventType:
        event_bus.subscribe(ev_type, event_logger_listener)

    # 1.5 Initialize LLM Client
    logger.info(f"Initializing LLM with model: {settings.llm_model} at {settings.base_url}")
    llm = OpenAIClient(
        component_id="groq-llm",
        model_name=settings.llm_model,
        api_key=SecretStr(settings.openai_api_key),
        base_url=settings.base_url
    )
    await llm.initialize()

    # 2. Initialize Tools
    file_tool = FileTool(workspace=workspace)
    await file_tool.initialize()

    shell_tool = ShellTool(workspace=workspace)
    await shell_tool.initialize()

    # 3. Initialize Specialized Agents and Register Tools (Passing LLM to Developer)
    developer = DeveloperAgent(component_id="dev-1", llm=llm)
    developer.register_tool("file_tool", file_tool)
    developer.register_tool("shell_tool", shell_tool)
    await developer.initialize()

    reviewer = ReviewerAgent(component_id="reviewer-1")
    await reviewer.initialize()

    manager = ManagerAgent(component_id="manager-1")
    await manager.initialize()

    # 4. Register Agents into MessageBus
    message_bus.register_agent(developer)
    message_bus.register_agent(reviewer)
    message_bus.register_agent(manager)

    # 5. Initialize Orchestrator
    orchestrator = Orchestrator(
        task_manager=task_manager,
        message_bus=message_bus,
        event_bus=event_bus,
    )
    await orchestrator.initialize()

    logger.info("=== Subsystems initialized and wired successfully ===")

    # 6. Create an Initial Engineering Task
    initial_task = task_manager.create_task(
        title="Implement Calculator Module",
        description="Write a python calculator module and run pytest verification tests.",
        created_by=AgentRole.MANAGER,
        assigned_to=AgentRole.DEVELOPER,
        priority=TaskPriority.HIGH,
    )

    logger.info(f"Created initial task: [{initial_task.id}] '{initial_task.title}'")

    # 7. Run Orchestration Loop
    logger.info("=== Launching Orchestrator Execution Loop ===")
    await orchestrator.run_until_complete(max_iterations=5, sleep_interval=0.5)

    # 8. Graceful Shutdown
    logger.info("=== Shutting Down Subsystems ===" )
    await orchestrator.shutdown()
    await developer.shutdown()
    await reviewer.shutdown()
    await manager.shutdown()
    await file_tool.shutdown()
    await shell_tool.shutdown()
    await llm.shutdown()
    await event_bus.shutdown()
    await message_bus.shutdown()
    await task_manager.shutdown()
    await workspace.shutdown()

    logger.info("=== AI Development Team Demo Completed Successfully ===")


if __name__ == "__main__":
    asyncio.run(main())