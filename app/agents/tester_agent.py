"""Tester agent implementation responsible for executing test suites and verifying code behavior."""

import json
import logging
import re
import sys
import time
from typing import Any
from uuid import UUID

from app.agents.base_worker_agent import BaseWorkerAgent
from app.workspace.local_workspace import LocalWorkspace
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState, EventType
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata
from app.schemas.value_objects.test_result import TestResult

logger = logging.getLogger(__name__)


class TesterAgent(BaseWorkerAgent):
    """Specialized quality engineering agent that executes automated tests and analyzes outcomes."""

    role: AgentRole = AgentRole.TESTER
    component_id: str = "tester-agent"

    @staticmethod
    def _parse_pytest_counts(stdout: str) -> dict[str, int]:
        """Extract collected/passed/failed/error counts from pytest output."""
        counts = {"collected": 0, "passed": 0, "failed": 0, "errors": 0}
        
        # Match 'collected N items' or 'collected N item'
        collected_match = re.search(r'collected\s+(\d+)\s+items?', stdout)
        if collected_match:
            counts["collected"] = int(collected_match.group(1))
        
        # Match 'N passed' in summary line  
        passed_match = re.search(r'(\d+)\s+passed', stdout)
        if passed_match:
            counts["passed"] = int(passed_match.group(1))
        
        # Match 'N failed' in summary line
        failed_match = re.search(r'(\d+)\s+failed', stdout)
        if failed_match:
            counts["failed"] = int(failed_match.group(1))
        
        # Match 'N error' in summary line
        error_match = re.search(r'(\d+)\s+errors?', stdout)
        if error_match:
            counts["errors"] = int(error_match.group(1))
        
        return counts

    async def _parse_test_result(self, stdout: str, stderr: str, success: bool) -> TestResult:
        """Use LLM to parse test output into a structured TestResult."""
        if not self.llm:
            return TestResult(
                passed=success,
                failed_test_names=[],
                error_summary="Raw test execution result.",
                stdout=stdout,
                stderr=stderr,
            )

        prompt = (
            f"Analyze the following test execution logs and extract the test result.\n\n"
            f"Command Success: {success}\n"
            f"STDOUT:\n{stdout}\n\n"
            f"STDERR:\n{stderr}\n"
        )
        system_prompt = (
            "You are a QA automation expert. Parse the test runner output and return a JSON object matching the requested schema. "
            "Identify if tests passed, list any failed test names, and provide a concise summary of errors."
        )

        try:
            return await self.llm.generate_structured(
                prompt=prompt,
                response_schema=TestResult,
                system_prompt=system_prompt,
            )
        except Exception as e:
            logger.warning(f"Failed to generate structured test result via LLM ({e}), using fallback parser.")
            passed = success and ("FAILED" not in stdout and "ERROR" not in stdout)
            return TestResult(
                passed=passed,
                failed_test_names=[],
                error_summary="Parsed via rule fallback." if passed else "Tests failed in execution logs.",
                stdout=stdout,
                stderr=stderr,
            )

    async def process_task(
        self, task_id: UUID, context_payload: dict[str, Any]
    ) -> AgentResponse:
        """Execute automated tests via ShellTool, analyze output, and report test outcomes."""
        self.validate_state()
        self.state = AgentState.WORKING
        self.current_task_id = task_id

        logger.info(f"TesterAgent starting test execution for task {task_id}")
        await self.publish_telemetry(EventType.AGENT_STARTED, {"message": f"TesterAgent starting test execution for task {task_id}"})

        workspace_path = context_payload.get("workspace_path")
        project_id = context_payload.get("project_id")
        if not workspace_path and project_id:
            from pathlib import Path
            from app.settings.settings import settings
            workspace_path = str(Path(settings.workspace_dir) / "projects" / str(project_id))

        shell_tool = self.tools.get("shell_tool")

        try:
            if not shell_tool:
                self.state = AgentState.IDLE
                self.current_task_id = None
                return AgentResponse(
                    status=AgentExecutionStatus.FAILED,
                    message="TesterAgent execution failed: 'shell_tool' is not registered.",
                    next_agent=AgentRole.MANAGER,
                    metadata=Metadata(source_component="tester-agent"),
                )

            if workspace_path:
                shell_tool.workspace = LocalWorkspace(root_path=workspace_path, component_id=f"ws-test-{task_id}")
                await shell_tool.workspace.initialize()

            default_cmd = f"{sys.executable} -m pytest -v -c /dev/null --rootdir=. -p no:cacheprovider"
            test_command = context_payload.get("command", default_cmd)
            logger.info(f"Running test suite command: '{test_command}' in workspace: {workspace_path}")
            await self.publish_telemetry(EventType.TEST_STARTED, {"command": test_command})
            await self.publish_telemetry(EventType.AGENT_ACTION, {"message": f"Running automated test suite: {test_command}"})

            start_t = time.time()
            tool_result = await shell_tool.execute(command=test_command)
            duration = round(time.time() - start_t, 2)

            await self.publish_telemetry(EventType.AGENT_THINKING, {"message": "Parsing test execution logs..."})
            test_result = await self._parse_test_result(
                stdout=tool_result.stdout,
                stderr=tool_result.stderr,
                success=tool_result.success,
            )

            # Strict verification gate: If process exit code != 0, tests did not pass
            if not tool_result.success:
                test_result.passed = False
                if not test_result.error_summary or test_result.error_summary == "Raw test execution result.":
                    test_result.error_summary = tool_result.stderr or tool_result.stdout[:500] or "Pytest process exited with non-zero status."

            # Parse real pytest counts from stdout
            pytest_counts = self._parse_pytest_counts(tool_result.stdout)
            test_result.tests_collected = pytest_counts["collected"]
            test_result.tests_passed = pytest_counts["passed"]
            test_result.tests_failed = pytest_counts["failed"]
            
            # Zero-test gate: 0 tests collected means tests need to be written
            if pytest_counts["collected"] == 0:
                test_result.passed = False
                test_result.error_summary = "No tests were collected by pytest. Test files may be missing or contain no test functions."

            await self.publish_telemetry(EventType.TEST_FINISHED, {
                "passed": test_result.passed,
                "error_summary": test_result.error_summary,
                "duration": duration,
                "tests_collected": test_result.tests_collected,
                "tests_passed": test_result.tests_passed,
                "tests_failed": test_result.tests_failed,
            })

            test_result.stdout = tool_result.stdout
            test_result.stderr = tool_result.stderr

            self.state = AgentState.IDLE
            self.current_task_id = None

            metadata = Metadata(source_component="tester-agent")
            test_data = test_result.model_dump()
            test_data["command"] = test_command
            test_data["exit_code"] = tool_result.exit_code
            test_data["duration"] = duration
            test_data["tests_collected"] = test_result.tests_collected
            test_data["tests_passed"] = test_result.tests_passed
            test_data["tests_failed"] = test_result.tests_failed
            metadata.extra["test_result"] = test_data

            if test_result.passed:
                return AgentResponse(
                    status=AgentExecutionStatus.SUCCESS,
                    message=f"TesterAgent verified task {task_id}: All tests passed successfully.",
                    artifacts=tool_result.artifacts,
                    next_agent=None,
                    metadata=metadata,
                )
            else:
                # Route to DEVELOPER if no tests exist, DEBUGGER if tests fail
                next_role = AgentRole.DEVELOPER if test_result.tests_collected == 0 else AgentRole.DEBUGGER
                return AgentResponse(
                    status=AgentExecutionStatus.NEEDS_FIX,
                    message=f"TesterAgent found issues for task {task_id}: {test_result.error_summary}",
                    artifacts=tool_result.artifacts,
                    next_agent=next_role,
                    metadata=metadata,
                )

        except Exception as e:
            logger.error(f"TesterAgent encountered unexpected exception on task {task_id}: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.current_task_id = None
            return AgentResponse(
                status=AgentExecutionStatus.FAILED,
                message=f"TesterAgent encountered exception during test run: {str(e)}",
                next_agent=AgentRole.MANAGER,
                metadata=Metadata(source_component="tester-agent"),
            )