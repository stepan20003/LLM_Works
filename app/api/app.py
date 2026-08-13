"""FastAPI application initialization with lifespan management for framework subsystems."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from pydantic import SecretStr
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse

from app.api.router import router as api_router, set_api_dependencies
from app.api.websocket import websocket_router, set_websocket_event_bus
from app.agents.developer_agent import DeveloperAgent
from app.agents.manager_agent import ManagerAgent
from app.agents.architect_agent import ArchitectAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.tester_agent import TesterAgent
from app.agents.debugger_agent import DebuggerAgent
from app.llm.openai_client import OpenAIClient
from app.tasks.task_manager import TaskManager
from app.projects.project_manager import ProjectManager
from app.messaging.message_bus import MessageBus
from app.messaging.event_bus import EventBus
from app.orchestrator.orchestrator import Orchestrator
from app.tools.file_tools import FileTool
from app.tools.shell_tool import ShellTool
from app.workspace.local_workspace import LocalWorkspace
from app.settings.settings import settings
from app.settings.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Global component instances
task_manager = TaskManager()
project_manager = ProjectManager()
message_bus = MessageBus()
event_bus = EventBus()
workspace = LocalWorkspace(component_id="api-sandbox", root_path=settings.workspace_dir)
llm_client = OpenAIClient(
    component_id="groq-llm",
    model_name=settings.llm_model,
    api_key=SecretStr(settings.openai_api_key),
    base_url=settings.base_url,
)
file_tool = FileTool(workspace=workspace, event_bus=event_bus)
shell_tool = ShellTool(workspace=workspace, event_bus=event_bus)
developer_agent = DeveloperAgent(component_id="dev-1", llm=llm_client, event_bus=event_bus)
architect_agent = ArchitectAgent(component_id="architect-1", llm=llm_client, event_bus=event_bus)
reviewer_agent = ReviewerAgent(component_id="reviewer-1", llm=llm_client, event_bus=event_bus)
manager_agent = ManagerAgent(component_id="manager-1", llm=llm_client, event_bus=event_bus)
tester_agent = TesterAgent(component_id="tester-1", llm=llm_client, event_bus=event_bus)
debugger_agent = DebuggerAgent(component_id="debugger-1", llm=llm_client, event_bus=event_bus)
orchestrator = Orchestrator(
    task_manager=task_manager,
    message_bus=message_bus,
    event_bus=event_bus,
)
orchestrator_loop_task: asyncio.Task | None = None
orchestrator_stop_event: asyncio.Event | None = None


async def _orchestrator_loop(stop_event: asyncio.Event, poll_interval: float) -> None:
    """Continuously process ready tasks while the API is running."""
    while not stop_event.is_set():
        await orchestrator.run_iteration()
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval)
        except asyncio.TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to initialize and shutdown framework components cleanly."""
    logger.info("Initializing AI Development Team API subsystems...")
    
    await workspace.initialize()
    await task_manager.initialize()
    await message_bus.initialize()
    await event_bus.initialize()
    await project_manager.initialize()
    file_tool.workspace = workspace
    shell_tool.workspace = workspace
    developer_agent.llm = llm_client
    await llm_client.initialize()
    await file_tool.initialize()
    await shell_tool.initialize()

    developer_agent.register_tool("file_tool", file_tool)
    developer_agent.register_tool("shell_tool", shell_tool)
    architect_agent.register_tool("file_tool", file_tool)
    tester_agent.register_tool("file_tool", file_tool)
    tester_agent.register_tool("shell_tool", shell_tool)
    debugger_agent.register_tool("file_tool", file_tool)

    await developer_agent.initialize()
    await architect_agent.initialize()
    await reviewer_agent.initialize()
    await manager_agent.initialize()
    await tester_agent.initialize()
    await debugger_agent.initialize()

    message_bus.register_agent(developer_agent)
    message_bus.register_agent(architect_agent)
    message_bus.register_agent(reviewer_agent)
    message_bus.register_agent(manager_agent)
    message_bus.register_agent(tester_agent)
    message_bus.register_agent(debugger_agent)

    await orchestrator.initialize()

    # Wire dependencies into routers
    set_api_dependencies(task_manager, orchestrator, project_manager)
    set_websocket_event_bus(event_bus)

    # Expose the initialized components on app.state for dependency helpers and tests.
    app.state.task_manager = task_manager
    app.state.orchestrator = orchestrator
    app.state.message_bus = message_bus
    app.state.event_bus = event_bus
    app.state.workspace = workspace
    app.state.llm_client = llm_client
    app.state.developer_agent = developer_agent
    app.state.architect_agent = architect_agent
    app.state.reviewer_agent = reviewer_agent
    app.state.manager_agent = manager_agent
    app.state.tester_agent = tester_agent
    app.state.debugger_agent = debugger_agent
    app.state.project_manager = project_manager
    app.state.api_dependencies_ready = True

    global orchestrator_loop_task, orchestrator_stop_event
    orchestrator_loop_task = None
    orchestrator_stop_event = None
    if settings.orchestrator_auto_run:
        orchestrator_stop_event = asyncio.Event()
        orchestrator_loop_task = asyncio.create_task(
            _orchestrator_loop(
                stop_event=orchestrator_stop_event,
                poll_interval=settings.orchestrator_poll_interval_seconds,
            )
        )
        app.state.orchestrator_loop_task = orchestrator_loop_task

    logger.info("All subsystems initialized successfully. API is ready.")
    yield

    logger.info("Shutting down AI Development Team API subsystems...")
    if orchestrator_stop_event is not None:
        orchestrator_stop_event.set()
    if orchestrator_loop_task is not None:
        orchestrator_loop_task.cancel()
        with suppress(asyncio.CancelledError):
            await orchestrator_loop_task

    await orchestrator.shutdown()
    await developer_agent.shutdown()
    await architect_agent.shutdown()
    await reviewer_agent.shutdown()
    await manager_agent.shutdown()
    await tester_agent.shutdown()
    await debugger_agent.shutdown()
    await llm_client.shutdown()
    await event_bus.shutdown()
    await message_bus.shutdown()
    await task_manager.shutdown()
    await project_manager.shutdown()
    await workspace.shutdown()
    logger.info("Subsystems shut down gracefully.")


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Autonomous multi-agent software engineering framework API & Real-time Telemetry",
        lifespan=lifespan,
    )

    # Include routers
    application.include_router(api_router)
    application.include_router(websocket_router)

    return application


# Create app instance
app = create_app()

# Static HTML dashboard file path
BASE_DIR = Path(__file__).resolve().parent.parent  # /workspace/app
HTML_FILE_PATH = BASE_DIR / "static" / "index.html"


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the modern web dashboard interface from a separate HTML file."""
    if HTML_FILE_PATH.exists():
        return FileResponse(HTML_FILE_PATH)
    return {"error": "Dashboard index.html not found"}, 404


@app.post("/orchestrator/run")
async def run_orchestrator_iteration(request: Request):
    """Manually trigger an orchestrator iteration to process ready tasks."""
    try:
        active_orchestrator = request.app.state.orchestrator
        processed_count = await active_orchestrator.run_iteration()
        return {
            "status": "success",
            "processed_tasks": processed_count,
            "message": f"Orchestrator processed {processed_count} tasks."
        }
    except Exception as e:
        logger.error(f"Error running orchestrator iteration: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500