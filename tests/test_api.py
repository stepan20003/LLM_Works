"""Comprehensive REST API tests for the FastAPI application."""

import importlib
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

api_app_module = importlib.import_module("app.api.app")
from app.api.router import router as api_router
from app.messaging.event_bus import EventBus
from app.messaging.message_bus import MessageBus
from app.orchestrator.orchestrator import Orchestrator
from app.schemas.enums import AgentRole, TaskPriority, TaskStatus
from app.tasks.task_manager import TaskManager
from app.workspace.local_workspace import LocalWorkspace
from app.settings.settings import settings


@pytest.fixture
def api_client(monkeypatch):
    """Create a fresh FastAPI app with fresh subsystem instances for each test."""
    task_manager = TaskManager()
    message_bus = MessageBus()
    event_bus = EventBus()
    workspace = LocalWorkspace(component_id="api-test-sandbox", root_path=settings.workspace_dir)
    orchestrator = Orchestrator(
        task_manager=task_manager,
        message_bus=message_bus,
        event_bus=event_bus,
    )

    monkeypatch.setattr(api_app_module, "task_manager", task_manager)
    monkeypatch.setattr(api_app_module, "message_bus", message_bus)
    monkeypatch.setattr(api_app_module, "event_bus", event_bus)
    monkeypatch.setattr(api_app_module, "workspace", workspace)
    monkeypatch.setattr(api_app_module, "orchestrator", orchestrator)

    app = api_app_module.create_app()

    with TestClient(app) as client:
        yield client, task_manager, orchestrator


def test_health_endpoint_returns_healthy_when_initialized(api_client):
    client, _, _ = api_client

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ai-development-team"}


def test_health_endpoint_returns_degraded_when_router_is_not_initialized():
    app = FastAPI()
    app.include_router(api_router)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "detail": "Subsystems not fully initialized."}


def test_create_task_accepts_valid_payload_and_defaults(api_client):
    client, _, _ = api_client

    response = client.post(
        "/tasks/",
        json={"title": "Implement parser", "description": "Add a parser for the request payload."},
    )

    assert response.status_code == 201
    body = response.json()
    assert UUID(body["id"])
    assert body["title"] == "Implement parser"
    assert body["description"] == "Add a parser for the request payload."
    assert body["status"] == TaskStatus.CREATED.value
    assert body["priority"] == TaskPriority.NORMAL.value
    assert body["created_by"] == AgentRole.MANAGER.value
    assert body["assigned_to"] is None
    assert body["max_retries"] == 5
    assert body["estimated_duration"] == 0.0
    assert body["dependencies"] == []
    assert body["tags"] == []
    assert body["retry_count"] == 0
    assert body["metadata"]["source_component"] == "system"
    assert body["started_at"] is None
    assert body["completed_at"] is None
    assert body["failed_at"] is None


def test_create_task_accepts_assigned_agent_and_custom_priority(api_client):
    client, _, _ = api_client

    response = client.post(
        "/tasks/",
        json={
            "title": "Ship release",
            "description": "Coordinate the release checklist.",
            "created_by": AgentRole.MANAGER.value,
            "assigned_to": AgentRole.DEVELOPER.value,
            "priority": TaskPriority.CRITICAL.value,
            "max_retries": 7,
            "estimated_duration": 12.5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["assigned_to"] == AgentRole.DEVELOPER.value
    assert body["priority"] == TaskPriority.CRITICAL.value
    assert body["max_retries"] == 7
    assert body["estimated_duration"] == 12.5
    assert body["created_by"] == AgentRole.MANAGER.value


@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"title": "", "description": "desc"}, 422),
        ({"title": "title", "description": ""}, 422),
        ({"title": "title", "description": "desc", "priority": "MEDIUM"}, 422),
        ({"title": "title", "description": "desc", "created_by": "INVALID"}, 422),
        ({"title": "title", "description": "desc", "max_retries": -1}, 422),
        ({"title": "title", "description": "desc", "estimated_duration": -1.5}, 422),
    ],
)
def test_create_task_rejects_invalid_payloads(api_client, payload, expected_status):
    client, _, _ = api_client

    response = client.post("/tasks/", json=payload)

    assert response.status_code == expected_status


def test_list_tasks_returns_current_task_manager_state(api_client):
    client, task_manager, _ = api_client

    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []

    created_task = task_manager.create_task(
        title="First task",
        description="A task for the API.",
        created_by=AgentRole.MANAGER,
    )

    response = client.get("/tasks/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(created_task.id)
    assert body[0]["status"] == TaskStatus.CREATED.value

    second_task = task_manager.create_task(
        title="Second task",
        description="Another task for the API.",
        created_by=AgentRole.DEVELOPER,
        assigned_to=AgentRole.TESTER,
        priority=TaskPriority.HIGH,
    )

    response = client.get("/tasks/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {task["id"] for task in body} == {str(created_task.id), str(second_task.id)}


def test_get_task_returns_existing_task_and_handles_missing_or_malformed_ids(api_client):
    client, task_manager, _ = api_client

    created_task = task_manager.create_task(
        title="Lookup task",
        description="Find me through the API.",
        created_by=AgentRole.REVIEWER,
    )

    response = client.get(f"/tasks/{created_task.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(created_task.id)
    assert body["title"] == "Lookup task"

    missing_response = client.get(f"/tasks/{uuid4()}")
    assert missing_response.status_code == 404
    assert "not found" in missing_response.json()["detail"].lower()

    malformed_response = client.get("/tasks/not-a-uuid")
    assert malformed_response.status_code == 422


def test_task_state_reflects_task_manager_changes(api_client):
    client, task_manager, _ = api_client

    created_task = task_manager.create_task(
        title="State task",
        description="Track state changes through the API.",
        created_by=AgentRole.MANAGER,
    )

    task_manager.update_task_status(created_task.id, TaskStatus.IN_PROGRESS)

    response = client.get(f"/tasks/{created_task.id}")

    assert response.status_code == 200
    assert response.json()["status"] == TaskStatus.IN_PROGRESS.value


def test_error_handling_returns_stable_http_responses(api_client):
    client, _, _ = api_client

    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []

    missing_task_response = client.get(f"/tasks/{uuid4()}")
    assert missing_task_response.status_code == 404

    invalid_payload_response = client.post(
        "/tasks/",
        json={"title": "", "description": "bad"},
    )
    assert invalid_payload_response.status_code == 422


def test_task_response_serializes_uuid_datetime_and_optional_fields(api_client):
    client, _, _ = api_client

    response = client.post(
        "/tasks/",
        json={
            "title": "Serialization task",
            "description": "Ensure the API response is JSON-serializable.",
            "created_by": AgentRole.TESTER.value,
            "assigned_to": AgentRole.DEVELOPER.value,
            "priority": TaskPriority.HIGH.value,
            "max_retries": 3,
            "estimated_duration": 8.25,
        },
    )

    assert response.status_code == 201
    body = response.json()

    assert UUID(body["id"])
    assert isinstance(body["created_at"], str)
    assert isinstance(body["updated_at"], str)
    datetime.fromisoformat(body["created_at"].replace("Z", "+00:00"))
    datetime.fromisoformat(body["updated_at"].replace("Z", "+00:00"))
    assert body["status"] == TaskStatus.CREATED.value
    assert body["assigned_to"] == AgentRole.DEVELOPER.value
    assert body["dependencies"] == []
    assert body["metadata"]["version"] == "1.0.0"
    assert body["metadata"]["extra"] == {}


def test_dependency_wiring_uses_initialized_instances_from_app_state(api_client):
    client, task_manager, orchestrator = api_client

    response = client.post(
        "/tasks/",
        json={"title": "Wiring task", "description": "Verify the API uses the injected state."},
    )

    assert response.status_code == 201
    task_id = UUID(response.json()["id"])

    assert client.app.state.task_manager is task_manager
    assert client.app.state.orchestrator is orchestrator
    assert task_id in task_manager.tasks
    assert task_manager.get_task(task_id).title == "Wiring task"


def test_openapi_exposes_health_and_task_routes(api_client):
    client, _, _ = api_client

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/tasks/" in paths
    assert "/tasks/{task_id}" in paths
