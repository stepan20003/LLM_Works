"""WebSocket router managing real-time event streaming to the dashboard."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.messaging.event_bus import EventBus
from app.schemas.entities.event import Event
from app.schemas.enums import EventType

logger = logging.getLogger(__name__)
websocket_router = APIRouter()

_event_bus: EventBus | None = None


def set_websocket_event_bus(event_bus: EventBus) -> None:
    """Inject EventBus dependency into the WebSocket module."""
    global _event_bus
    _event_bus = event_bus


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle live telemetry WebSocket connection and stream events to clients."""
    await websocket.accept()
    logger.info("WebSocket client connected successfully.")

    if _event_bus is None:
        await websocket.close(code=1011)
        return

    async def event_listener(event: Event) -> None:
        """Forward a published system event to the connected WebSocket client."""
        try:
            await websocket.send_json(event.model_dump(mode="json"))
        except (RuntimeError, WebSocketDisconnect):
            logger.info("WebSocket client disconnected while delivering an event.")
            for event_type in EventType:
                _event_bus.unsubscribe(event_type, event_listener)
        except Exception as exc:
            logger.error(f"Failed to forward event {event.id} to WebSocket client: {exc}", exc_info=True)
            for event_type in EventType:
                _event_bus.unsubscribe(event_type, event_listener)

    try:
        for event_type in EventType:
            _event_bus.subscribe(event_type, event_listener)

        await websocket.send_json({"status": "connected", "message": "Subscribed to event stream."})

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}", exc_info=True)
    finally:
        for event_type in EventType:
            if _event_bus is not None:
                _event_bus.unsubscribe(event_type, event_listener)
        logger.info("WebSocket session closed.")