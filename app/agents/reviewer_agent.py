"""Reviewer agent implementation responsible for code review, quality gates, and correctness checks."""

import logging
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.workspace.local_workspace import LocalWorkspace
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState, EventType
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseWorkerAgent):
    """Specialized quality assurance agent that performs code reviews and approves or requests fixes."""

    role: AgentRole = AgentRole.REVIEWER
    component_id: str = "reviewer-agent"

    async def _evaluate_review(self, content: str, task_id: UUID) -> tuple[bool, str]:
        """Use the LLM to evaluate the task content and decide if it needs fixes."""
        if not self.llm:
            requires_fix = "error" in content.lower() or "fail" in content.lower()
            return requires_fix, "Rule-based fallback check (no LLM)."

        prompt = (
            f"Review the following work produced for task {task_id}.\n\n"
            f"PROJECT FILES:\n{content[:8000]}\n\n"
            "Perform a thorough code review checking:\n"
            "1. Architecture: Is the code well-structured with proper separation of concerns?\n"
            "2. Completeness: Are all required features implemented (not just stubs)?\n"
            "3. Security: Are there obvious security issues (hardcoded secrets, SQL injection, missing auth)?\n"
            "4. Imports: Are all imports valid and modules properly referenced?\n"
            "5. Tests: Do test files contain real assertions testing actual functionality?\n"
            "6. Configuration: Are config files (pyproject.toml, Dockerfile, etc.) properly structured?\n"
            "7. Code quality: No TODO/FIXME/pass placeholders in production code?\n\n"
            "If the work is complete, high quality, and correct, reply starting with 'APPROVED'.\n"
            "If there are critical issues, reply starting with 'REJECTED' followed by a numbered list of required fixes."
        )

        system_prompt = (
            "You are a strict, senior code reviewer. You analyze source code, configuration files, and tests. "
            "Ensure high quality, completeness, and correctness."
        )

        await self.publish_telemetry(EventType.MODEL_SELECTED, {"model_name": self.llm.model_name})
        await self.publish_telemetry(EventType.AGENT_THINKING, {"message": "Reviewing implementation logic, security, and tests..."})
        await self.publish_telemetry(EventType.AGENT_ACTION, {"message": "Formulating review feedback..."})

        try:
            response = await self.llm.generate_completion(prompt=prompt, system_prompt=system_prompt)
            requires_fix = response.strip().upper().startswith("REJECTED")
            return requires_fix, response
        except Exception as e:
            logger.error(f"Reviewer LLM evaluation failed: {e}")
            requires_fix = "error" in content.lower() or "fail" in content.lower()
            return requires_fix, f"Fallback check triggered due to LLM error: {e}"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Review implementation artifacts or test outputs and determine approval or required fixes."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        logger.info(f"ReviewerAgent evaluating task {task_id}")
        await self.publish_telemetry(EventType.AGENT_STARTED, {"message": f"ReviewerAgent evaluating task {task_id}"})
        await self.publish_telemetry(EventType.REVIEW_STARTED, {"task_id": str(task_id)})

        workspace_path = context_payload.get("workspace_path")
        project_id = context_payload.get("project_id")
        if not workspace_path and project_id:
            from pathlib import Path
            from app.settings.settings import settings
            workspace_path = str(Path(settings.workspace_dir) / "projects" / str(project_id))

        file_tool = self.tools.get("file_tool")
        
        content = context_payload.get("content", "")
        if workspace_path and file_tool:
            file_tool.workspace = LocalWorkspace(root_path=workspace_path, component_id=f"ws-rev-{task_id}")
            await file_tool.workspace.initialize()
            
            # Read actual project files for review
            list_res = await file_tool.execute(action="list")
            if list_res.success and list_res.stdout:
                file_snippets = []
                all_workspace_files = list_res.stdout.splitlines()
                reviewable_extensions = (".py", ".json", ".toml", ".yml", ".yaml", ".md", ".cfg", ".ini", ".sql", ".sh")
                reviewable_filenames = ("Dockerfile", ".env.example", "Makefile", "docker-compose.yml", "docker-compose.yaml")
                for fname in all_workspace_files:
                    fname_stripped = fname.strip()
                    if not fname_stripped:
                        continue
                    if fname_stripped.endswith(reviewable_extensions) or fname_stripped in reviewable_filenames or any(fname_stripped.endswith(n) for n in reviewable_filenames):
                        f_read = await file_tool.execute(action="read", path=fname)
                        if f_read.success:
                            file_snippets.append(f"--- File: {fname} ---\n{f_read.stdout}")
                if file_snippets:
                    content += "\n\nActual Project Files:\n" + "\n\n".join(file_snippets)
                # Check against architect manifest if available
                arch_spec = context_payload.get("architecture_spec")
                if arch_spec and isinstance(arch_spec, dict):
                    required_files = [f.get("path") for f in arch_spec.get("required_files", []) if f.get("path")]
                    workspace_file_list = [f.strip() for f in (list_res.stdout.splitlines() if list_res.success else [])]
                    missing_from_manifest = [rf for rf in required_files if rf not in workspace_file_list]
                    if missing_from_manifest:
                        content += f"\n\nWARNING: {len(missing_from_manifest)} files from architect manifest are MISSING: {', '.join(missing_from_manifest)}"

        requires_fix, feedback = await self._evaluate_review(content, task_id)
        
        await self.publish_telemetry(EventType.REVIEW_RESULT, {
            "approved": not requires_fix,
            "feedback": feedback
        })

        self.state = AgentState.IDLE
        self.current_task_id = None

        if requires_fix:
            return AgentResponse(
                status=AgentExecutionStatus.NEEDS_FIX,
                message=f"ReviewerAgent requested fixes for task {task_id}.\nFeedback: {feedback}",
                next_agent=AgentRole.DEVELOPER,
                metadata=Metadata(source_component="reviewer-agent"),
            )

        return AgentResponse(
            status=AgentExecutionStatus.SUCCESS,
            message=f"ReviewerAgent approved task {task_id}.\nFeedback: {feedback}",
            next_agent=AgentRole.TESTER,
            metadata=Metadata(source_component="reviewer-agent"),
        )