"""Manager agent implementation responsible for project planning and task decomposition."""

import json
import logging
from typing import Any, Optional
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState, EventType
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata
from app.schemas.value_objects.project_plan import ProjectPlan

logger = logging.getLogger(__name__)

# System prompt instructing the LLM to return a structured JSON plan
PLANNING_SYSTEM_PROMPT = """You are a senior software engineering manager. 
Given a project description, produce a structured JSON plan with this exact schema:

{
  "summary": "One-paragraph project overview",
  "requirements": ["requirement 1", "requirement 2", ...],
  "architecture": "High-level architecture description",
  "subtasks": [
    {
      "title": "Subtask title",
      "description": "Detailed description",
      "assigned_role": "DEVELOPER",
      "dependencies": [],
      "priority": "NORMAL",
      "estimated_duration": 0.0
    }
  ],
  "acceptance_criteria": ["criterion 1", "criterion 2", ...]
}

Rules:
- assigned_role must be one of: MANAGER, DEVELOPER, REVIEWER, TESTER
- priority must be one of: LOW, NORMAL, HIGH, CRITICAL  
- dependencies is a list of subtask titles that must complete first
- Order subtasks logically (dependencies before dependents)
- Output ONLY valid JSON, no explanations or markdown
"""


class ManagerAgent(BaseWorkerAgent):
    """Executive agent that interprets project prompts and produces structured plans."""

    role: AgentRole = AgentRole.MANAGER
    component_id: str = "manager-agent"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Process a task — if it contains a project_prompt, generate a structured plan."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        content = context_payload.get("content", "")
        project_prompt = context_payload.get("project_prompt")

        await self.publish_telemetry(EventType.AGENT_STARTED, {"message": f"ManagerAgent analyzing task {task_id}"})

        try:
            # If this is a planning request, generate a structured plan
            if project_prompt and self.llm:
                logger.info(f"ManagerAgent generating structured plan for task {task_id}")
                await self.publish_telemetry(EventType.MODEL_SELECTED, {"model_name": self.llm.model_name})
                await self.publish_telemetry(EventType.AGENT_THINKING, {"message": "Decomposing requirements into a structured project plan..."})
                
                plan = await self._generate_plan(project_prompt)
                await self.publish_telemetry(EventType.PROJECT_PLANNED, {"subtasks_count": len(plan.subtasks), "plan_summary": plan.summary})

                self.state = AgentState.IDLE
                self.current_task_id = None

                return AgentResponse(
                    status=AgentExecutionStatus.SUCCESS,
                    message=f"ManagerAgent produced a structured plan with {len(plan.subtasks)} subtasks.",
                    next_agent=AgentRole.DEVELOPER,
                    metadata=Metadata(
                        source_component="manager-agent",
                        extra={"plan": plan.model_dump()},
                    ),
                )

            # Default behavior: acknowledge and route to developer
            logger.info(f"ManagerAgent processing control directive for task {task_id}")
            await self.publish_telemetry(EventType.AGENT_ACTION, {"message": "Processing generic control directive and delegating..."})
            
            self.state = AgentState.IDLE
            self.current_task_id = None

            return AgentResponse(
                status=AgentExecutionStatus.SUCCESS,
                message=f"ManagerAgent orchestrated task {task_id} successfully.",
                next_agent=AgentRole.DEVELOPER,
                metadata=Metadata(source_component="manager-agent"),
            )

        except Exception as e:
            logger.error(f"ManagerAgent error on task {task_id}: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.current_task_id = None
            return AgentResponse(
                status=AgentExecutionStatus.FAILED,
                message=f"ManagerAgent encountered exception: {str(e)}",
                next_agent=None,
                metadata=Metadata(source_component="manager-agent"),
            )

    async def _generate_plan(self, project_prompt: str) -> ProjectPlan:
        """Generate a structured ProjectPlan using the LLM.

        Tries generate_structured first (if the LLM supports it),
        then falls back to generate_completion with JSON parsing.
        """
        # Attempt structured generation first
        try:
            plan = await self.llm.generate_structured(
                prompt=project_prompt,
                response_schema=ProjectPlan,
                system_prompt=PLANNING_SYSTEM_PROMPT,
            )
            if isinstance(plan, ProjectPlan):
                logger.info("ManagerAgent used generate_structured successfully.")
                return plan
        except (NotImplementedError, TypeError, Exception) as e:
            logger.info(f"generate_structured not available or failed ({e}), falling back to completion.")

        # Fallback: generate raw text and parse as JSON
        raw_response = await self.llm.generate_completion(
            prompt=project_prompt,
            system_prompt=PLANNING_SYSTEM_PROMPT,
        )
        plan = self._parse_plan_from_text(raw_response)
        return plan

    @staticmethod
    def _parse_plan_from_text(raw_text: str) -> ProjectPlan:
        """Parse a ProjectPlan from raw LLM text output.

        Handles JSON embedded in markdown code blocks or plain JSON.
        """
        text = raw_text.strip()

        # Strip markdown code fences if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            return ProjectPlan(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM output as ProjectPlan: {e}")
            # Return a minimal plan with the raw text as summary
            return ProjectPlan(
                summary=raw_text[:500] if raw_text else "Planning failed — could not parse LLM output.",
                requirements=[],
                architecture="",
                subtasks=[],
                acceptance_criteria=[],
            )