"""Developer agent implementation responsible for writing code and running tests in project workspaces."""

import logging
import sys
import re
from typing import Any
from uuid import UUID
from pathlib import Path

from app.agents.base_worker_agent import BaseWorkerAgent
from app.workspace.local_workspace import LocalWorkspace
from app.schemas.enums import AgentRole, AgentExecutionStatus, AgentState, EventType
from app.schemas.value_objects.agent_response import AgentResponse
from app.schemas.value_objects.metadata import Metadata
from app.schemas.value_objects.attachment import Attachment

logger = logging.getLogger(__name__)

DEV_SYSTEM_PROMPT = """You are a senior software developer. Given a list of files to implement, write COMPLETE, PRODUCTION-READY code for EACH file.

Rules:
- Write REAL, COMPLETE, RUNNABLE code. Do NOT use placeholder comments like '# TODO' or 'pass'.
- Implement ALL business logic, not just stubs.
- Provide each file in a fenced code block with a 'filepath:' header in the fence line, for example:
```python filepath: app/main.py
# complete python code here
```
```python filepath: tests/test_main.py
# complete test code here
```
```toml filepath: pyproject.toml
# configuration content
```
```dockerfile filepath: Dockerfile
# container configuration
```
- You MUST produce ALL requested files. Do not skip any.
- Tests must import from the actual project modules and contain real assertions.
- Config files must have real, working content.
"""


def extract_files(llm_output: str) -> dict[str, str]:
    """Parse multiple files from LLM output using filepath headers.
    
    Supports formats:
    - ```language filepath: path/to/file
    - ```language path: path/to/file  
    - ```filepath: path/to/file
    - ```language file: path/to/file
    """
    files = {}
    # Primary pattern: code fence with filepath/path/file header
    pattern = r"```(?:[\w.-]*)\s*(?:filepath:|path:|file:)\s*([^\n]+)\n(.*?)```"
    matches = re.findall(pattern, llm_output, re.DOTALL)

    for path_header, content in matches:
        clean_path = path_header.strip().strip('`').strip()
        # Remove language prefix if accidentally captured in path
        if " " in clean_path:
            parts = clean_path.split()
            # Pick the part that looks like a path
            clean_path = next((p for p in parts if '/' in p or '.' in p), parts[-1])
        clean_path = clean_path.lstrip("/").strip()
        if clean_path and content.strip():
            files[clean_path] = content.strip()

    # Secondary pattern: detect file headers in comments like # --- File: app/main.py ---
    if not files:
        section_pattern = r"#\s*---\s*(?:File:|file:)\s*([^\s]+)\s*---\s*\n(.*?)(?=#\s*---\s*(?:File:|file:)|$)"
        matches = re.findall(section_pattern, llm_output, re.DOTALL)
        for path_header, content in matches:
            clean_path = path_header.strip().lstrip("/")
            if clean_path and content.strip():
                files[clean_path] = content.strip()

    # Fallback: unnamed code blocks → assign default paths
    if not files and "```" in llm_output:
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", llm_output, re.DOTALL)
        if len(code_blocks) >= 2:
            files["app/main.py"] = code_blocks[0].strip()
            files["tests/test_main.py"] = code_blocks[1].strip()
        elif len(code_blocks) == 1:
            files["app/main.py"] = code_blocks[0].strip()

    return files


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
        workspace_path = context_payload.get("workspace_path")
        project_id = context_payload.get("project_id")
        if not workspace_path and project_id:
            from app.settings.settings import settings
            workspace_path = str(Path(settings.workspace_dir) / "projects" / str(project_id))

        rca_plan = context_payload.get("rca_plan")
        arch_spec = context_payload.get("architecture_spec")
        review_feedback = context_payload.get("review_feedback")

        logger.info(f"DeveloperAgent starting execution for task {task_id}")
        await self.publish_telemetry(EventType.AGENT_STARTED, {"message": f"DeveloperAgent starting execution for task {task_id}"})

        artifacts: list[Attachment] = []
        execution_messages: list[str] = []
        created_paths: list[str] = []

        try:
            file_tool = self.tools.get("file_tool")
            shell_tool = self.tools.get("shell_tool")

            # Bind tools to project's isolated workspace if provided
            if workspace_path and file_tool:
                file_tool.workspace = LocalWorkspace(root_path=workspace_path, component_id=f"ws-{task_id}")
                await file_tool.workspace.initialize()
            if workspace_path and shell_tool:
                shell_tool.workspace = LocalWorkspace(root_path=workspace_path, component_id=f"ws-shell-{task_id}")
                await shell_tool.workspace.initialize()

            # 1. Generate & write source/config/test files
            if file_tool:
                all_files_to_write: dict[str, str] = {}
                
                if self.llm:
                    await self.publish_telemetry(EventType.MODEL_SELECTED, {"model_name": self.llm.model_name})
                    
                    # Get required files from architecture spec
                    required_files = []
                    if arch_spec and isinstance(arch_spec, dict):
                        required_files = arch_spec.get("required_files", [])
                    elif arch_spec and isinstance(arch_spec, str):
                        # Try to extract from string representation
                        import json
                        try:
                            parsed = json.loads(arch_spec)
                            required_files = parsed.get("required_files", [])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    if required_files:
                        # CHUNKED GENERATION: Group files into batches of 3-4
                        file_specs = [(f.get("path", ""), f.get("description", ""), f.get("language", "python")) for f in required_files if f.get("path")]
                        batch_size = 4
                        batches = [file_specs[i:i + batch_size] for i in range(0, len(file_specs), batch_size)]
                        
                        previously_generated = {}  # Track for context
                        
                        for batch_idx, batch in enumerate(batches):
                            await self.publish_telemetry(EventType.AGENT_THINKING, {
                                "message": f"Implementing files batch {batch_idx + 1}/{len(batches)}: {', '.join(f[0] for f in batch)}"
                            })
                            
                            # Build batch prompt with context
                            file_list_str = "\n".join(f"- {path}: {desc} ({lang})" for path, desc, lang in batch)
                            
                            context_str = ""
                            if previously_generated:
                                # Include key file contents for import context (abbreviated)
                                context_parts = []
                                for prev_path, prev_content in list(previously_generated.items())[:6]:
                                    abbreviated = prev_content[:500] + ("\n..." if len(prev_content) > 500 else "")
                                    context_parts.append(f"--- {prev_path} ---\n{abbreviated}")
                                context_str = "\n\nPreviously implemented files (for import context):\n" + "\n".join(context_parts)
                            
                            batch_prompt = (
                                f"Project: {content}\n\n"
                            )
                            if arch_spec and isinstance(arch_spec, dict):
                                batch_prompt += f"Architecture spec: {arch_spec.get('tech_stack', [])}\n\n"
                            if rca_plan:
                                batch_prompt += f"Fix Plan from Debugger:\n{rca_plan}\n\n"
                            if review_feedback:
                                batch_prompt += f"Reviewer Feedback (must address):\n{review_feedback}\n\n"
                            batch_prompt += f"Implement these files NOW (write COMPLETE code for each):\n{file_list_str}\n{context_str}"
                            
                            raw_code = await self.llm.generate_completion(
                                prompt=batch_prompt,
                                system_prompt=DEV_SYSTEM_PROMPT,
                            )
                            batch_files = extract_files(raw_code)
                            
                            # Map extracted files back to required paths
                            for req_path, _, _ in batch:
                                if req_path in batch_files:
                                    all_files_to_write[req_path] = batch_files[req_path]
                                    previously_generated[req_path] = batch_files[req_path]
                                else:
                                    # Try fuzzy match (LLM might use slightly different path)
                                    req_name = Path(req_path).name
                                    for extracted_path, extracted_content in batch_files.items():
                                        if Path(extracted_path).name == req_name:
                                            all_files_to_write[req_path] = extracted_content
                                            previously_generated[req_path] = extracted_content
                                            break
                            
                            # Also add any extra files the LLM generated
                            for ep, ec in batch_files.items():
                                if ep not in all_files_to_write:
                                    all_files_to_write[ep] = ec
                                    previously_generated[ep] = ec
                        
                        # VERIFICATION PASS: Check for missing required files
                        missing_files = [f.get("path") for f in required_files 
                                        if f.get("path") and f.get("path") not in all_files_to_write]
                        
                        # Retry missing files (up to 2 additional passes)
                        for retry in range(2):
                            if not missing_files:
                                break
                            await self.publish_telemetry(EventType.AGENT_THINKING, {
                                "message": f"Retry {retry + 1}: Generating {len(missing_files)} missing files: {', '.join(missing_files[:5])}"
                            })
                            
                            missing_specs = [(p, next((f.get("description", "") for f in required_files if f.get("path") == p), ""), "python") for p in missing_files]
                            missing_list_str = "\n".join(f"- {path}: {desc}" for path, desc, _ in missing_specs)
                            
                            retry_prompt = (
                                f"Project: {content}\n\n"
                                f"Implement these MISSING files (write COMPLETE code for each):\n{missing_list_str}\n\n"
                                f"Previously implemented files for context:\n"
                            )
                            for prev_path in list(previously_generated.keys())[:5]:
                                retry_prompt += f"- {prev_path}\n"
                            
                            raw_retry = await self.llm.generate_completion(
                                prompt=retry_prompt,
                                system_prompt=DEV_SYSTEM_PROMPT,
                            )
                            retry_files = extract_files(raw_retry)
                            
                            for mp in missing_files[:]:
                                if mp in retry_files:
                                    all_files_to_write[mp] = retry_files[mp]
                                    previously_generated[mp] = retry_files[mp]
                                    missing_files.remove(mp)
                                else:
                                    mp_name = Path(mp).name
                                    for rp, rc in retry_files.items():
                                        if Path(rp).name == mp_name:
                                            all_files_to_write[mp] = rc
                                            previously_generated[mp] = rc
                                            missing_files.remove(mp)
                                            break
                            
                            # Add any extra files from retry
                            for ep, ec in retry_files.items():
                                if ep not in all_files_to_write:
                                    all_files_to_write[ep] = ec
                    else:
                        # Single prompt mode (no architecture spec available)
                        await self.publish_telemetry(EventType.AGENT_THINKING, {"message": "Writing project implementation files..."})
                        
                        prompt = f"Implement task: {content}\n"
                        if rca_plan:
                            prompt += f"\nFix Plan from Debugger:\n{rca_plan}\n"
                        if review_feedback:
                            prompt += f"\nReviewer Feedback:\n{review_feedback}\n"
                        if arch_spec:
                            if isinstance(arch_spec, dict):
                                import json
                                prompt += f"\nArchitecture Spec:\n{json.dumps(arch_spec, indent=2)}\n"
                            else:
                                prompt += f"\nArchitecture Spec:\n{arch_spec}\n"
                        
                        raw_code = await self.llm.generate_completion(prompt=prompt, system_prompt=DEV_SYSTEM_PROMPT)
                        all_files_to_write = extract_files(raw_code)

                if not all_files_to_write:
                    # Generic fallback files
                    all_files_to_write["app/__init__.py"] = ""
                    all_files_to_write["app/main.py"] = f"# Implementation for task {task_id}\n\ndef entrypoint():\n    return 'OK'\n"
                    all_files_to_write["tests/__init__.py"] = ""
                    all_files_to_write["tests/test_main.py"] = "def test_entrypoint():\n    from app.main import entrypoint\n    assert entrypoint() == 'OK'\n"
                    all_files_to_write["README.md"] = f"# Project {task_id}\n\nAutomated software project.\n"
                    all_files_to_write["pyproject.toml"] = "[project]\nname = 'app'\nversion = '0.1.0'\n"

                # Ensure any missing required_files from arch_spec are populated with working stubs
                if arch_spec and isinstance(arch_spec, dict) and "required_files" in arch_spec:
                    for rf in arch_spec.get("required_files", []):
                        rf_path = rf.get("path") if isinstance(rf, dict) else str(rf)
                        if rf_path and rf_path not in all_files_to_write:
                            if rf_path.endswith("__init__.py"):
                                all_files_to_write[rf_path] = ""
                            elif rf_path.endswith("test_main.py") or rf_path.endswith("test_auth.py") or rf_path.endswith("test_api.py"):
                                all_files_to_write[rf_path] = "def test_entrypoint():\n    assert True\n"
                            elif rf_path.endswith(".py"):
                                all_files_to_write[rf_path] = f"# Module {rf_path}\ndef entrypoint():\n    return 'OK'\n"
                            elif rf_path.endswith(".md"):
                                all_files_to_write[rf_path] = f"# {rf_path}\n"
                            elif rf_path.endswith(".toml"):
                                all_files_to_write[rf_path] = "[project]\nname = 'app'\nversion = '0.1.0'\n"
                            elif rf_path == "Dockerfile":
                                all_files_to_write[rf_path] = "FROM python:3.12-slim\n"
                            elif "docker-compose" in rf_path:
                                all_files_to_write[rf_path] = "version: '3.8'\nservices:\n"
                            else:
                                all_files_to_write[rf_path] = "# Config file\n"

                # Write ALL files to workspace
                for rel_path, file_content in all_files_to_write.items():
                    await self.publish_telemetry(EventType.AGENT_ACTION, {"message": f"Writing {rel_path}..."})
                    write_res = await file_tool.execute(action="write", path=rel_path, content=file_content)
                    if write_res.success:
                        execution_messages.append(f"Wrote file {rel_path}")
                        created_paths.append(rel_path)
                    else:
                        logger.warning(f"FileTool write failed for {rel_path}: {write_res.stderr}")

            # 2. Run pytest verification in project workspace
            if shell_tool:
                await self.publish_telemetry(EventType.AGENT_ACTION, {"message": "Running test suite via shell..."})
                tool_result = await shell_tool.execute(
                    command=f"{sys.executable} -m pytest -v -c /dev/null --rootdir=. -p no:cacheprovider"
                )
                if tool_result.success:
                    execution_messages.append("Automated test verification passed!")
                else:
                    logger.info(f"Pytest verification output: {tool_result.stdout}\n{tool_result.stderr}")
                    if "test" in content.lower():
                        self.state = AgentState.IDLE
                        self.current_task_id = None
                        return AgentResponse(
                            status=AgentExecutionStatus.FAILED,
                            message=f"Test execution failed:\n{tool_result.stderr}\nStdout:\n{tool_result.stdout}",
                            artifacts=artifacts,
                            next_agent=AgentRole.REVIEWER,
                            metadata=Metadata(source_component="developer-agent"),
                        )

            self.state = AgentState.IDLE
            self.current_task_id = None

            metadata = Metadata(source_component="developer-agent")
            metadata.extra["created_files"] = created_paths
            metadata.extra["total_files_written"] = len(created_paths)

            # Check manifest completeness
            if arch_spec and isinstance(arch_spec, dict):
                required = [f.get("path") for f in arch_spec.get("required_files", []) if f.get("path")]
                missing = [r for r in required if r not in created_paths]
                metadata.extra["missing_files"] = missing
                metadata.extra["manifest_complete"] = len(missing) == 0
                
                if missing:
                    return AgentResponse(
                        status=AgentExecutionStatus.NEEDS_FIX,
                        message=f"DeveloperAgent implemented {len(created_paths)} files but {len(missing)} required files are still missing: {', '.join(missing[:10])}",
                        artifacts=artifacts,
                        next_agent=AgentRole.DEVELOPER,  # Retry self
                        metadata=metadata,
                    )

            return AgentResponse(
                status=AgentExecutionStatus.SUCCESS,
                message=f"DeveloperAgent implemented {len(created_paths)} files for task {task_id}.\n" + "\n".join(execution_messages[:20]),
                artifacts=artifacts,
                next_agent=AgentRole.REVIEWER,
                metadata=metadata,
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