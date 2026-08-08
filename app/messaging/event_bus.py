"""Publish-Subscribe event broker for system-wide telemetry and event distribution."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Optional

from app.core.base_component import BaseComponent
from app.schemas.enums import EventType
from app.schemas.entities.event import Event

logger = logging.getLogger(__name__)


class EventBus(BaseComponent):
    """Asynchronous publish-subscribe event broker with error isolation."""

    component_id: str = "event-bus"
    listeners: dict[EventType, list[Callable[[Event], Awaitable[None]]]] = {}

    async def initialize(self) -> None:
        """Initialize the event bus pub/sub channels."""
        self.listeners = {}
        self.is_initialized = True
        logger.info("EventBus initialized successfully.")

    async def shutdown(self) -> None:
        """Clear all active pub/sub listeners."""
        self.listeners.clear()
        self.is_initialized = False
        logger.info("EventBus shut down and listeners cleared.")

    async def health_check(self) -> bool:
        """Verify operational health of the event bus."""
        return self.is_initialized

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], Awaitable[None]]
    ) -> None:
        """Register an asynchronous listener callback for a specific EventType."""
        self.validate_state()
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
        logger.debug(f"Subscribed callback to event type: {event_type}")

    def unsubscribe(
        self, event_type: EventType, callback: Callable[[Event], Awaitable[None]]
    ) -> None:
        """Remove a previously registered listener callback from an event type."""
        callbacks = self.listeners.get(event_type)
        if not callbacks:
            return

        try:
            callbacks.remove(callback)
        except ValueError:
            return

        if not callbacks:
            self.listeners.pop(event_type, None)
        logger.debug(f"Unsubscribed callback from event type: {event_type}")

    async def publish(self, event: Event) -> None:
        """Publish an event asynchronously to all registered listeners with error isolation."""
        self.validate_state()
        event_type = event.event_type

        if event_type not in self.listeners or not self.listeners[event_type]:
            logger.debug(f"No active listeners for event type: {event_type}")
            return

        callbacks = self.listeners[event_type]
        logger.debug(f"Publishing event {event.id} ({event_type}) to {len(callbacks)} listeners.")

        async def _safe_invoke(cb: Callable[[Event], Awaitable[None]], ev: Event) -> None:
            try:
                await cb(ev)
            except Exception as exc:
                logger.error(
                    f"Error in event listener callback for {ev.event_type} (Event ID: {ev.id}): {exc}",
                    exc_info=True,
                )

        # Execute all listeners concurrently while isolating failures
        await asyncio.gather(*[_safe_invoke(cb, event) for cb in callbacks])