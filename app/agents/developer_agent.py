"""Developer agent implementation responsible for writing code and running tests via tools."""

import logging
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata
from app.schemas.value_objects.attachment import Attachment

logger = logging.getLogger(__name__)


class DeveloperAgent(BaseWorkerAgent):
    """Specialized engineering agent that writes code (FileTool) and runs verification (ShellTool)."""

    role: AgentRole = AgentRole.DEVELOPER
    component_id: str = "developer-agent"

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Execute software development tasks by interacting with filesystem and shell execution."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        content = context_payload.get("content", "")
        logger.info(f"DeveloperAgent starting execution for task {task_id}")

        artifacts: list[Attachment] = []
        execution_messages: list[str] = []

        try:
            file_tool = self.tools.get("file_tool")
            shell_tool = self.tools.get("shell_tool")

            # 1. ԳԵՆԵՐԱՑՆՈՒՄ ԵՆՔ ԻՐԱԿԱՆ ԿՈԴ LLM-Ի ՄԻՋՈՑՈՎ
            if self.llm and file_tool:
                # Օգնական ֆունկցիա՝ միայն մաքուր կոդը վերցնելու համար
                def extract_code(text: str) -> str:
                    if "```python" in text:
                        return text.split("```python")[1].split("```")[0].strip()
                    elif "```" in text:
                        return text.split("```")[1].split("```")[0].strip()
                    # Եթե բլոկ չկա, կտրում ենք տերմինալի հրամանները
                    lines = [l for l in text.split('\n') if not l.strip().startswith('pytest')]
                    return '\n'.join(lines).strip()

                logger.info("DeveloperAgent is generating code using Groq LLM...")
                sys_prompt = "You are an expert Python developer. Write the solution inside ```python ... ``` markdown blocks. NO explanations."
                
                # Գրում ենք հիմնական կոդը
                raw_code = await self.llm.generate_completion(prompt=content, system_prompt=sys_prompt)
                code = extract_code(raw_code)
                await file_tool.execute(action="write", path="calculator.py", content=code)
                execution_messages.append("Created calculator.py.")
                
                # Գրում ենք թեստերը
                logger.info("DeveloperAgent is generating pytest tests...")
                test_prompt = f"Write a pytest file for this code:\n\n{code}\n\nOutput MUST be inside ```python ... ``` blocks. Import from calculator. No explanations."
                raw_test_code = await self.llm.generate_completion(prompt=test_prompt, system_prompt=sys_prompt)
                test_code = extract_code(raw_test_code)
                await file_tool.execute(action="write", path="test_calculator.py", content=test_code)
                execution_messages.append("Created test_calculator.py.")

            # 2. ԱՇԽԱՏԱՑՆՈՒՄ ԵՆՔ ԹԵՍՏԵՐԸ ՏԵՐՄԻՆԱԼՈՒՄ (ShellTool)
            if shell_tool and "test" in content.lower():
                logger.info("DeveloperAgent running test suite via ShellTool...")
                tool_result = await shell_tool.execute(command="pytest -v -c /dev/null --rootdir=. -p no:cacheprovider")
                if not tool_result.success:
                    self.state = AgentState.IDLE
                    self.current_task_id = None
                    return AgentResponse(
                        status=AgentExecutionStatus.FAILED,
                        message=f"Test execution failed:\n{tool_result.stderr}\nStdout:\n{tool_result.stdout}",
                        artifacts=artifacts,
                        next_agent=AgentRole.REVIEWER,
                        metadata=Metadata(source_component="developer-agent"),
                    )
                execution_messages.append("Pytest verification passed perfectly!")

            self.state = AgentState.IDLE
            self.current_task_id = None

            return AgentResponse(
                status=AgentExecutionStatus.SUCCESS,
                message=f"DeveloperAgent successfully implemented task {task_id}.\n" + "\n".join(execution_messages),
                artifacts=artifacts,
                next_agent=AgentRole.REVIEWER,
                metadata=Metadata(source_component="developer-agent"),
            )

        except Exception as e:
            logger.error(f"DeveloperAgent execution error on task {task_id}: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.current_task_id = None
            return AgentResponse(
                status=AgentExecutionStatus.FAILED,
                message=f"DeveloperAgent encountered exception: {str(e)}",
                next_agent=AgentRole.MANAGER,
                metadata=Metadata(source_component="developer-agent"),
            )