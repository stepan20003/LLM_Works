"""FastAPI application initialization with lifespan management for framework subsystems."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.router import router as api_router, set_api_dependencies
from app.api.websocket import websocket_router, set_websocket_event_bus
from app.tasks.task_manager import TaskManager
from app.messaging.message_bus import MessageBus
from app.messaging.event_bus import EventBus
from app.orchestrator.orchestrator import Orchestrator
from app.workspace.local_workspace import LocalWorkspace
from app.settings.settings import settings
from app.settings.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Global component instances
task_manager = TaskManager()
message_bus = MessageBus()
event_bus = EventBus()
workspace = LocalWorkspace(component_id="api-sandbox", root_path=settings.workspace_dir)
orchestrator = Orchestrator(
    task_manager=task_manager,
    message_bus=message_bus,
    event_bus=event_bus,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to initialize and shutdown framework components cleanly."""
    logger.info("Initializing AI Development Team API subsystems...")
    
    await workspace.initialize()
    await task_manager.initialize()
    await message_bus.initialize()
    await event_bus.initialize()
    await orchestrator.initialize()

    # Wire dependencies into routers
    set_api_dependencies(task_manager, orchestrator)
    set_websocket_event_bus(event_bus)

    # Expose the initialized components on app.state for dependency helpers and tests.
    app.state.task_manager = task_manager
    app.state.orchestrator = orchestrator
    app.state.message_bus = message_bus
    app.state.event_bus = event_bus
    app.state.workspace = workspace
    app.state.api_dependencies_ready = True

    logger.info("All subsystems initialized successfully. API is ready.")
    yield

    logger.info("Shutting down AI Development Team API subsystems...")
    await orchestrator.shutdown()
    await event_bus.shutdown()
    await message_bus.shutdown()
    await task_manager.shutdown()
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
async def run_orchestrator_iteration():
    """Manually trigger an orchestrator iteration to process ready tasks."""
    try:
        processed_count = await orchestrator.run_iteration()
        return {
            "status": "success",
            "processed_tasks": processed_count,
            "message": f"Orchestrator processed {processed_count} tasks."
        }
    except Exception as e:
        logger.error(f"Error running orchestrator iteration: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500