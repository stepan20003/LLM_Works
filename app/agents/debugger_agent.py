"""Debugger agent implementation responsible for Root Cause Analysis (RCA) and applying fixes to failing source files."""

import logging
import re
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.workspace.local_workspace import LocalWorkspace
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState, EventType
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata

logger = logging.getLogger(__name__)

DEBUG_SYSTEM_PROMPT = """You are an expert debugging AI. Analyze test failure logs, stack traces, and project files.
Identify the root cause of failure and provide fixed, production-ready code files.

Rules:
- Provide fixed files using filepath headers:
```python filepath: app/main.py
# fixed code here
```
```python filepath: tests/test_main.py
# fixed test code here if needed
```
- Provide complete code, no '# TODO' or placeholders.
"""


def extract_fixed_files(llm_output: str) -> dict[str, str]:
    """Parse fixed files from Debugger LLM output."""
    files = {}
    pattern = r"```(?:\w+)?\s*(?:filepath:|path:)?\s*([^\n]+)\n(.*?)```"
    matches = re.findall(pattern, llm_output, re.DOTALL)

    for path_header, content in matches:
        clean_path = path_header.strip()
        if " " in clean_path:
            clean_path = clean_path.split()[-1]
        clean_path = clean_path.lstrip("/").strip()
        if clean_path and content.strip():
            files[clean_path] = content.strip()

    return files


class DebuggerAgent(BaseWorkerAgent):
    """Specialized debugging agent that analyzes test failures and directly fixes source files."""

    role: AgentRole = AgentRole.DEBUGGER
    component_id: str = "debugger-agent"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Analyze test outputs, fix actual project files, and route back to TESTER."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        logger.info(f"DebuggerAgent starting root cause analysis for task {task_id}")
        await self.publish_telemetry(EventType.AGENT_STARTED, {"message": f"DebuggerAgent starting RCA for task {task_id}"})
        await self.publish_telemetry(EventType.DEBUG_STARTED, {"task_id": str(task_id)})

        workspace_path = context_payload.get("workspace_path")
        project_id = context_payload.get("project_id")
        if not workspace_path and project_id:
            from pathlib import Path
            from app.settings.settings import settings
            workspace_path = str(Path(settings.workspace_dir) / "projects" / str(project_id))

        file_tool = self.tools.get("file_tool")
        test_result = context_payload.get("test_result", {})

        try:
            if workspace_path and file_tool:
                file_tool.workspace = LocalWorkspace(root_path=workspace_path, component_id=f"ws-dbg-{task_id}")
                await file_tool.workspace.initialize()

            stdout = test_result.get("stdout", "")
            stderr = test_result.get("stderr", "")
            summary = test_result.get("error_summary", "")

            # Read existing project files to give Debugger context
            existing_code = ""
            if file_tool and workspace_path:
                list_res = await file_tool.execute(action="list")
                if list_res.success and list_res.stdout:
                    file_snippets = []
                    for fname in list_res.stdout.splitlines()[:10]:
                        if fname.endswith((".py", ".json", ".toml", "Dockerfile")):
                            f_read = await file_tool.execute(action="read", path=fname)
                            if f_read.success:
                                file_snippets.append(f"--- File: {fname} ---\n{f_read.stdout}")
                    if file_snippets:
                        existing_code = "\n\nExisting Source Files:\n" + "\n\n".join(file_snippets)

            rca_plan = "Performed root cause analysis."
            fixed_files = {}

            if self.llm:
                await self.publish_telemetry(EventType.MODEL_SELECTED, {"model_name": self.llm.model_name})
                await self.publish_telemetry(EventType.AGENT_THINKING, {"message": "Analyzing test failure stack traces and code..."})

                prompt = (
                    f"Analyze test failure for task {task_id}:\n"
                    f"Summary: {summary}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}\n"
                    f"{existing_code}\n\nProvide root cause and fixed files."
                )

                raw_output = await self.llm.generate_completion(prompt=prompt, system_prompt=DEBUG_SYSTEM_PROMPT)
                rca_plan = raw_output
                fixed_files = extract_fixed_files(raw_output)

            # Apply fixed files to project workspace
            if file_tool and fixed_files:
                for rel_p, code in fixed_files.items():
                    await self.publish_telemetry(EventType.AGENT_ACTION, {"message": f"Applying debug fix to {rel_p}..."})
                    await file_tool.execute(action="write", path=rel_p, content=code)

            self.state = AgentState.IDLE
            self.current_task_id = None

            metadata = Metadata(source_component="debugger-agent")
            metadata.extra["rca_plan"] = rca_plan
            metadata.extra["fixed_files"] = list(fixed_files.keys())

            return AgentResponse(
                status=AgentExecutionStatus.SUCCESS,
                message=f"DebuggerAgent completed RCA and applied fixes to {len(fixed_files)} files.\n\nRCA:\n{rca_plan[:300]}",
                next_agent=AgentRole.TESTER,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"DebuggerAgent encountered exception on task {task_id}: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.current_task_id = None
            return AgentResponse(
                status=AgentExecutionStatus.FAILED,
                message=f"DebuggerAgent encountered exception during analysis: {str(e)}",
                next_agent=AgentRole.MANAGER,
                metadata=Metadata(source_component="debugger-agent"),
            )
