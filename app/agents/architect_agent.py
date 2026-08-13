"""Architect agent implementation responsible for designing concrete project architecture and file layouts."""

import json
import logging
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState, EventType
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)

ARCHITECT_SYSTEM_PROMPT = """You are a Principal Software Architect.
Given a project description and high-level requirements, produce a comprehensive, concrete software architecture specification as a JSON object with this exact schema:

{
  "project_name": "slugified-project-name",
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker", "pytest"],
  "requirements_map": {
    "JWT authentication": ["app/core/security.py", "app/api/routes/auth.py"],
    "PostgreSQL database": ["app/db/database.py", "app/db/models.py"],
    "User CRUD": ["app/api/routes/users.py", "app/schemas/user.py"]
  },
  "directory_structure": ["app/", "app/core/", "app/db/", "app/api/", "app/api/routes/", "app/schemas/", "tests/"],
  "required_files": [
    {
      "path": "app/__init__.py",
      "description": "Package initializer",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "app/main.py",
      "description": "FastAPI application entrypoint with routes and middleware",
      "language": "python",
      "is_test": false,
      "is_config": false
    },
    {
      "path": "tests/test_main.py",
      "description": "Unit tests for application endpoints",
      "language": "python",
      "is_test": true,
      "is_config": false
    },
    {
      "path": "Dockerfile",
      "description": "Container build configuration",
      "language": "dockerfile",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "pyproject.toml",
      "description": "Project dependencies and metadata",
      "language": "toml",
      "is_test": false,
      "is_config": true
    },
    {
      "path": "README.md",
      "description": "Project setup and run instructions",
      "language": "markdown",
      "is_test": false,
      "is_config": false
    }
  ],
  "env_variables": ["DATABASE_URL", "SECRET_KEY"],
  "run_instructions": "Command to launch and test the project"
}

Rules:
- Provide explicit file paths for ALL necessary source files, configuration files, test files, and Dockerfiles needed for a complete runnable software project.
- The required_files list must contain EVERY file the developer needs to implement. Include __init__.py files for all packages.
- Include at least one test file per major module.
- Include Dockerfile and docker-compose.yml if Docker is mentioned in the requirements.
- Include configuration files (.env.example, pyproject.toml/requirements.txt).
- The requirements_map must map each user requirement to the files that implement it.
- Output ONLY valid JSON, no explanations or markdown blocks.
"""


class ArchitectAgent(BaseWorkerAgent):
    """Specialized architecture agent that designs concrete system structures and file specifications."""

    role: AgentRole = AgentRole.ARCHITECT
    component_id: str = "architect-agent"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Process architecture design task and return concrete file layout specification."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        prompt = context_payload.get("project_prompt") or context_payload.get("content", "")
        logger.info(f"ArchitectAgent generating architecture specification for task {task_id}")
        await self.publish_telemetry(EventType.AGENT_STARTED, {"message": f"ArchitectAgent starting design for task {task_id}"})

        try:
            if not self.llm:
                # Rule-based fallback architecture
                spec = {
                    "project_name": "autonomous-app",
                    "tech_stack": ["Python", "pytest"],
                    "requirements_map": {"Core application": ["app/main.py"], "Tests": ["tests/test_main.py"]},
                    "directory_structure": ["app/", "tests/", "pyproject.toml", "README.md"],
                    "required_files": [
                        {"path": "app/__init__.py", "description": "Package init", "language": "python", "is_test": False, "is_config": False},
                        {"path": "app/main.py", "description": "Main application code", "language": "python", "is_test": False, "is_config": False},
                        {"path": "tests/__init__.py", "description": "Test init", "language": "python", "is_test": False, "is_config": False},
                        {"path": "tests/test_main.py", "description": "Pytest verification suite", "language": "python", "is_test": True, "is_config": False},
                        {"path": "pyproject.toml", "description": "Project dependencies", "language": "toml", "is_test": False, "is_config": True},
                        {"path": "README.md", "description": "Run instructions", "language": "markdown", "is_test": False, "is_config": False}
                    ],
                    "env_variables": [],
                    "run_instructions": "pytest"
                }
            else:
                await self.publish_telemetry(EventType.MODEL_SELECTED, {"model_name": self.llm.model_name})
                await self.publish_telemetry(EventType.AGENT_THINKING, {"message": "Designing modular component architecture and file layout..."})
                
                raw_response = await self.llm.generate_completion(
                    prompt=f"Design complete runnable project architecture for:\n{prompt}",
                    system_prompt=ARCHITECT_SYSTEM_PROMPT,
                )
                text = raw_response.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                try:
                    spec = json.loads(text)
                except Exception as e:
                    logger.warning(f"Failed to parse LLM architecture JSON ({e}), using default layout.")
                    spec = {
                        "project_name": "app",
                        "tech_stack": ["Python"],
                        "requirements_map": {"Core application": ["app/main.py"]},
                        "required_files": [
                            {"path": "app/main.py", "description": "Main application code", "language": "python", "is_test": False, "is_config": False},
                            {"path": "tests/test_main.py", "description": "Unit tests", "language": "python", "is_test": True, "is_config": False},
                            {"path": "README.md", "description": "Documentation", "language": "markdown", "is_test": False, "is_config": False}
                        ],
                        "run_instructions": "pytest"
                    }

            # Validate minimum file count and filter example paths against prompt
            required_files = spec.get("required_files", [])
            prompt_lower = prompt.lower()
            
            # Filter out unrequested example routes if raw completion returned system prompt text
            filtered_files = []
            for rf in required_files:
                p = rf.get("path") if isinstance(rf, dict) else str(rf)
                if not p:
                    continue
                # Core files always retained
                if p in {"app/__init__.py", "app/main.py", "tests/__init__.py", "tests/test_main.py", "pyproject.toml", "README.md", "Dockerfile", "docker-compose.yml"}:
                    filtered_files.append(rf)
                elif "auth" in p and not any(k in prompt_lower for k in ["auth", "jwt", "login", "password"]):
                    continue
                elif "db" in p and not any(k in prompt_lower for k in ["db", "postgres", "sql", "database", "orm", "crud"]):
                    continue
                elif any(domain in p for domain in ["product", "order", "payment", "zipcode"]) and not any(k in prompt_lower for k in ["product", "order", "payment", "e-commerce", "shop", "store"]):
                    continue
                else:
                    filtered_files.append(rf)

            if len(filtered_files) < 3:
                filtered_files = required_files
            if not any((f.get("path") if isinstance(f, dict) else str(f)) == "README.md" for f in filtered_files):
                filtered_files.append({"path": "README.md", "description": "Project documentation", "language": "markdown", "is_test": False, "is_config": False})

            spec["required_files"] = filtered_files

            self.state = AgentState.IDLE
            self.current_task_id = None

            metadata = Metadata(source_component="architect-agent")
            metadata.extra["architecture_spec"] = spec

            return AgentResponse(
                status=AgentExecutionStatus.SUCCESS,
                message=f"ArchitectAgent finalized system design with {len(spec.get('required_files', []))} required project files.",
                next_agent=AgentRole.DEVELOPER,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"ArchitectAgent encountered exception on task {task_id}: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.current_task_id = None
            return AgentResponse(
                status=AgentExecutionStatus.FAILED,
                message=f"ArchitectAgent failed: {str(e)}",
                next_agent=AgentRole.MANAGER,
                metadata=Metadata(source_component="architect-agent"),
            )
