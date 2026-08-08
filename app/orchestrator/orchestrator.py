"""Orchestrator engine managing the autonomous multi-agent execution loop and task dispatching."""

import asyncio
import logging
from typing import Optional
from uuid import uuid4
from pydantic import Field
from app.core.base_component import BaseComponent
from app.tasks.task_manager import TaskManager
from app.messaging.message_bus import MessageBus
from app.messaging.event_bus import EventBus
from app.schemas.enums import AgentRole, AgentExecutionStatus, EventType, MessageStatus, TaskStatus, TaskPriority
from app.schemas.entities.message import Message
from app.schemas.entities.event import Event
from app.schemas.entities.task import Task
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)


class Orchestrator(BaseComponent):
    """Orchestrator managing multi-agent workflows and task execution."""
    
    task_manager: TaskManager = Field(default_factory=TaskManager)
    message_bus: MessageBus = Field(default_factory=MessageBus)
    event_bus: EventBus = Field(default_factory=EventBus)

    def __init__(
        self,
        task_manager: Optional[TaskManager] = None,
        message_bus: Optional[MessageBus] = None,
        event_bus: Optional[EventBus] = None,
        component_id: str = "orchestrator",
        metadata: Optional[Metadata] = None,
    ) -> None:
        """Initialize the Orchestrator with its core dependent subsystems."""
        super().__init__(
            component_id=component_id,
            metadata=metadata or Metadata(source_component="orchestrator"),
        )
        self.task_manager = task_manager or TaskManager()
        self.message_bus = message_bus or MessageBus()
        self.event_bus = event_bus or EventBus()

    async def initialize(self) -> None:
        """Initialize the orchestrator and verify dependent subsystems."""
        if not await self.task_manager.health_check():
            await self.task_manager.initialize()
        if not await self.message_bus.health_check():
            await self.message_bus.initialize()
        if not await self.event_bus.health_check():
            await self.event_bus.initialize()

        self.is_initialized = True
        logger.info("Orchestrator initialized successfully.")

    async def shutdown(self) -> None:
        """Shutdown the orchestrator and cascade shutdowns to dependencies if needed."""
        self.is_initialized = False
        logger.info("Orchestrator shut down.")

    async def health_check(self) -> bool:
        """Verify operational health of the orchestrator and its subcomponents."""
        if not self.is_initialized:
            return False
        return (
            await self.task_manager.health_check()
            and await self.message_bus.health_check()
            and await self.event_bus.health_check()
        )

    async def _prepare_message(self, task: Task, target_role: AgentRole) -> Message:
        """Construct a Message to send to the given agent role for the provided task.

        This method is only responsible for creating the Message object. It does not
        publish events or dispatch the message.
        """
        return Message(
            sender=AgentRole.SYSTEM,
            receiver=target_role,
            task_id=task.id,
            status=MessageStatus.REQUEST,
            priority=task.priority,
            content=f"Execute task [{task.id}]: {task.title}\nDescription: {task.description}",
            correlation_id=uuid4(),
            metadata=Metadata(source_component="orchestrator"),
        )

    async def _publish_task_event(
        self,
        event_type: EventType,
        task: Task,
        source: AgentRole,
        destination: AgentRole,
        payload: dict,
    ) -> None:
        """Publish a task-related Event to the event bus.

        Keeps construction of task events in a single place to avoid duplication.
        """
        event_kwargs = dict(
            event_type=event_type,
            source_agent=source,
            destination_agent=destination,
            task_id=task.id,
            payload=payload,
        )
        # Preserve existing behavior: initial TASK_UPDATED had orchestrator metadata
        if event_type == EventType.TASK_UPDATED:
            event_kwargs["metadata"] = Metadata(source_component="orchestrator")

        await self.event_bus.publish(Event(**event_kwargs))

    async def _publish_message_event(self, message: Message, event_type: EventType) -> None:
        """Publish message-related events (e.g., MESSAGE_SENT) to the event bus.

        Uses existing Message fields to populate the Event payload.
        """
        payload = {"content": message.content}
        if message.correlation_id is not None:
            payload["correlation_id"] = str(message.correlation_id)

        await self.event_bus.publish(
            Event(
                event_type=event_type,
                source_agent=message.sender,
                destination_agent=message.receiver,
                task_id=message.task_id,
                payload=payload,
            )
        )

    def _process_agent_response(self, task: Task, response: Optional[AgentResponse]) -> None:
        """Interpret an AgentResponse and update task state accordingly.

        Rules:
        - None -> treat as success and mark DONE
        - SUCCESS -> mark DONE
        - NEEDS_FIX or FAILED -> delegate to TaskManager.fail_task
        - WAITING -> leave unchanged

        This method does NOT publish events; it only mutates task state.
        """
        if response is None:
            self.task_manager.update_task_status(task.id, TaskStatus.DONE)
            logger.info(f"Task {task.id} completed with null response (assumed DONE).")
            return

        status = response.status
        if status == AgentExecutionStatus.SUCCESS:
            self.task_manager.update_task_status(task.id, TaskStatus.DONE)
            logger.info(f"Task {task.id} marked as DONE by agent response.")
        elif status in {AgentExecutionStatus.NEEDS_FIX, AgentExecutionStatus.FAILED}:
            self.task_manager.fail_task(task.id, error_message=response.message)
            logger.warning(f"Task {task.id} failed or requested fix: {response.message}")
        else:
            # WAITING or other non-terminal statuses: leave as-is
            logger.info(f"Task {task.id} returned status: {status}")

    async def _handle_task_failure(self, task: Task, target_role: AgentRole, exc: Exception) -> None:
        """Handle exceptions that occur when dispatching/processing a task.

        Responsibilities:
        - Log the exception with traceback
        - Mark the task as failed via TaskManager
        - Publish an ERROR event for observability
        """
        logger.error(f"Error executing task {task.id} via agent {target_role}: {exc}", exc_info=True)
        self.task_manager.fail_task(task.id, error_message=str(exc))
        await self.event_bus.publish(
            Event(
                event_type=EventType.ERROR,
                source_agent=target_role,
                destination_agent=AgentRole.SYSTEM,
                task_id=task.id,
                payload={"error": str(exc)},
            )
        )

    async def run_iteration(self) -> int:
        """Execute a single workflow iteration: fetch ready tasks, dispatch, and process responses.

        High-level workflow:
        1. Fetch ready tasks
        2. Determine target agent
        3. Update task status to IN_PROGRESS
        4. Publish a TASK_UPDATED started event
        5. Prepare and publish the MESSAGE_SENT event
        6. Dispatch the message and process the response
        7. Publish a final TASK_COMPLETED or TASK_UPDATED event
        8. Handle exceptions via a dedicated handler
        """
        self.validate_state()
        ready_tasks = self.task_manager.get_ready_tasks()
        if not ready_tasks:
            return 0

        processed_count = 0

        for task in ready_tasks:
            target_role = task.assigned_to or AgentRole.DEVELOPER

            # Move task to IN_PROGRESS and publish the start event
            self.task_manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)
            await self._publish_task_event(
                EventType.TASK_UPDATED,
                task,
                source=AgentRole.SYSTEM,
                destination=target_role,
                payload={"status": TaskStatus.IN_PROGRESS, "title": task.title},
            )

            # Build and publish message
            message = await self._prepare_message(task, target_role)
            await self._publish_message_event(message, EventType.MESSAGE_SENT)

            response: Optional[AgentResponse] = None
            try:
                response = await self.message_bus.dispatch(message)
                # Process response and mutate task state accordingly
                self._process_agent_response(task, response)

                # Publish final task event reflecting end state
                final_task = self.task_manager.get_task(task.id)
                final_event = (
                    EventType.TASK_COMPLETED
                    if final_task.status == TaskStatus.DONE
                    else EventType.TASK_UPDATED
                )
                await self._publish_task_event(
                    final_event,
                    final_task,
                    source=target_role,
                    destination=AgentRole.SYSTEM,
                    payload={"status": final_task.status, "message": response.message if response else ""},
                )

            except Exception as exc:
                await self._handle_task_failure(task, target_role, exc)

            processed_count += 1

        return processed_count

    async def run_until_complete(
        self, max_iterations: int = 100, sleep_interval: float = 1.0
    ) -> None:
        """Run the orchestrator loop continuously until all tasks reach terminal states or max iterations are met."""
        self.validate_state()
        logger.info(f"Starting orchestration loop (Max Iterations: {max_iterations}, Interval: {sleep_interval}s)")

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            processed = await self.run_iteration()

            # Check if there are any pending, ready, in-progress, or retrying tasks left
            active_tasks = [
                t for t in self.task_manager.tasks.values()
                if t.status in {
                    TaskStatus.CREATED,
                    TaskStatus.WAITING,
                    TaskStatus.READY,
                    TaskStatus.IN_PROGRESS,
                    TaskStatus.REVIEW,
                    TaskStatus.TESTING,
                    TaskStatus.RETRYING,
                }
            ]

            if not active_tasks:
                logger.info("All tasks have reached terminal states. Orchestration loop finished successfully.")
                break

            if processed == 0:
                # No tasks processed in this iteration, sleep to prevent busy-waiting
                await asyncio.sleep(sleep_interval)

        if iteration >= max_iterations:
            logger.warning(f"Orchestrator reached maximum iteration limit ({max_iterations}) before completion.")