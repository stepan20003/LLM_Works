"""WebSocket integration tests for live event streaming."""

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.websocket import websocket_router, set_websocket_event_bus
from app.messaging.event_bus import EventBus
from app.schemas.entities.event import Event
from app.schemas.enums import AgentRole, EventType


def _build_app(event_bus: EventBus) -> FastAPI:
    app = FastAPI()
    app.include_router(websocket_router)
    set_websocket_event_bus(event_bus)
    return app


def _create_event_bus() -> EventBus:
    event_bus = EventBus()
    asyncio.run(event_bus.initialize())
    return event_bus


def test_websocket_connects_and_receives_event() -> None:
    event_bus = _create_event_bus()
    app = _build_app(event_bus)

    try:
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                assert websocket.receive_json()["status"] == "connected"

                asyncio.run(
                    event_bus.publish(
                        Event(
                            event_type=EventType.MESSAGE_SENT,
                            source_agent=AgentRole.SYSTEM,
                            destination_agent=AgentRole.DEVELOPER,
                            payload={"message": "hello"},
                        )
                    )
                )

                delivered = websocket.receive_json()
                assert delivered["event_type"] == EventType.MESSAGE_SENT
                assert delivered["payload"]["message"] == "hello"
    finally:
        asyncio.run(event_bus.shutdown())


def test_multiple_clients_receive_events() -> None:
    event_bus = _create_event_bus()
    app = _build_app(event_bus)

    try:
        with TestClient(app) as client_one, TestClient(app) as client_two:
            with client_one.websocket_connect("/ws") as websocket_one, client_two.websocket_connect("/ws") as websocket_two:
                assert websocket_one.receive_json()["status"] == "connected"
                assert websocket_two.receive_json()["status"] == "connected"

                asyncio.run(
                    event_bus.publish(
                        Event(
                            event_type=EventType.TASK_UPDATED,
                            source_agent=AgentRole.SYSTEM,
                            destination_agent=AgentRole.MANAGER,
                            payload={"status": "IN_PROGRESS"},
                        )
                    )
                )

                first_delivery = websocket_one.receive_json()
                second_delivery = websocket_two.receive_json()
                assert first_delivery["event_type"] == EventType.TASK_UPDATED
                assert second_delivery["event_type"] == EventType.TASK_UPDATED
    finally:
        asyncio.run(event_bus.shutdown())


def test_disconnected_client_is_removed_without_breaking_others() -> None:
    event_bus = _create_event_bus()
    app = _build_app(event_bus)

    try:
        with TestClient(app) as client_one, TestClient(app) as client_two:
            with client_one.websocket_connect("/ws") as websocket_one, client_two.websocket_connect("/ws") as websocket_two:
                assert websocket_one.receive_json()["status"] == "connected"
                assert websocket_two.receive_json()["status"] == "connected"

                websocket_one.close()

                asyncio.run(
                    event_bus.publish(
                        Event(
                            event_type=EventType.ERROR,
                            source_agent=AgentRole.TESTER,
                            destination_agent=AgentRole.SYSTEM,
                            payload={"error": "boom"},
                        )
                    )
                )

                second_delivery = websocket_two.receive_json()
                assert second_delivery["event_type"] == EventType.ERROR
                assert second_delivery["payload"]["error"] == "boom"
    finally:
        asyncio.run(event_bus.shutdown())


def test_disconnect_cleans_up_subscriptions() -> None:
    event_bus = _create_event_bus()
    app = _build_app(event_bus)

    try:
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                assert websocket.receive_json()["status"] == "connected"

        assert not event_bus.listeners.get(EventType.MESSAGE_SENT)
        assert not event_bus.listeners.get(EventType.TASK_UPDATED)
        assert not event_bus.listeners.get(EventType.ERROR)
    finally:
        asyncio.run(event_bus.shutdown())
