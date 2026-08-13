"""In-memory project manager handling project lifecycle, planning, and task linkage."""

import os
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.core.base_component import BaseComponent
from app.settings.settings import settings
from app.schemas.enums import AgentRole, ProjectStatus
from app.schemas.entities.project import Project
from app.schemas.value_objects.project_plan import ProjectPlan
from app.exceptions.base import WorkflowError

logger = logging.getLogger(__name__)


class ProjectManager(BaseComponent):
    """Manages the creation, state transitions, planning, and task linkage of Projects."""

    component_id: str = "project-manager"
    projects: dict[UUID, Project] = {}

    def _get_storage_path(self) -> Path:
        data_dir = Path(settings.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "projects.json"

    def _load_state(self) -> None:
        path = self._get_storage_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for pid_str, p_data in data.items():
                    project = Project(**p_data)
                    self.projects[project.id] = project
                logger.info(f"Loaded {len(self.projects)} projects from {path}.")
            except Exception as e:
                logger.error(f"Failed to load project state: {e}")

    def _save_state(self) -> None:
        if not self.is_initialized:
            return
        path = self._get_storage_path()
        try:
            data = {str(k): v.model_dump(mode="json") for k, v in self.projects.items()}
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save project state: {e}")

    async def initialize(self) -> None:
        """Initialize the project manager."""
        self.projects = {}
        self._load_state()
        self.is_initialized = True
        logger.info("ProjectManager initialized successfully.")

    async def shutdown(self) -> None:
        """Shutdown and clear all managed projects from memory."""
        self.projects.clear()
        self.is_initialized = False
        logger.info("ProjectManager shut down and project memory cleared.")

    async def health_check(self) -> bool:
        """Verify operational health of the project manager."""
        return self.is_initialized

    def create_project(self, prompt: str, workspace_path: Optional[str] = None) -> Project:
        """Create a new Project from a user prompt and register it with an isolated workspace."""
        self.validate_state()

        temp_project_id = uuid4()
        if not workspace_path:
            workspace_dir = Path(settings.workspace_dir) / "projects" / str(temp_project_id)
            workspace_dir.mkdir(parents=True, exist_ok=True)
            workspace_path = str(workspace_dir)

        project = Project(id=temp_project_id, prompt=prompt, workspace_path=workspace_path)
        self.projects[project.id] = project
        logger.info(f"Project created: [{project.id}] (workspace: {workspace_path})")
        self._save_state()
        return project

    def get_project(self, project_id: UUID) -> Project:
        """Retrieve a project by its UUID; raise WorkflowError if not found."""
        self.validate_state()
        if project_id not in self.projects:
            raise WorkflowError(f"Project with ID {project_id} not found in ProjectManager.")
        return self.projects[project_id]

    def get_project_by_task_id(self, task_id: UUID) -> Optional[Project]:
        """Find a project that contains the given task UUID."""
        self.validate_state()
        for project in self.projects.values():
            if task_id in project.tasks:
                return project
        return None

    def get_all_projects(self) -> list[Project]:
        """Return all registered projects."""
        self.validate_state()
        return list(self.projects.values())

    def update_project_status(self, project_id: UUID, new_status: ProjectStatus) -> Project:
        """Update the status of a project with timestamp side-effects."""
        self.validate_state()
        project = self.get_project(project_id)

        old_status = project.status
        project.status = new_status

        # Set completed_at when transitioning to terminal success states
        if new_status in {ProjectStatus.DONE, ProjectStatus.APPROVED} and project.completed_at is None:
            object.__setattr__(project, "completed_at", datetime.now(timezone.utc))

        # Set failed_at when transitioning to FAILED
        if new_status == ProjectStatus.FAILED and project.failed_at is None:
            object.__setattr__(project, "failed_at", datetime.now(timezone.utc))

        self.projects[project_id] = project
        logger.info(f"Project {project_id} status updated: {old_status} -> {new_status}")
        self._save_state()
        return project

    def update_project_phase(
        self, project_id: UUID, phase: str, current_agent: Optional[AgentRole] = None
    ) -> Project:
        """Update active phase and active agent role for a project."""
        self.validate_state()
        project = self.get_project(project_id)
        project.current_phase = phase
        if current_agent is not None:
            project.current_agent = current_agent

        self.add_timeline_event(
            project_id=project_id,
            event_type="PROJECT_PHASE_CHANGED",
            agent=current_agent or project.current_agent,
            message=f"Project entered phase: {phase}",
            details={"phase": phase, "agent": current_agent.value if current_agent else None},
        )
        self.projects[project_id] = project
        self._save_state()
        return project

    def add_timeline_event(
        self,
        project_id: UUID,
        event_type: str,
        agent: Optional[AgentRole],
        message: str,
        details: Optional[dict] = None,
        task_id: Optional[UUID] = None,
    ) -> Project:
        """Append an event entry to a project's timeline log."""
        self.validate_state()
        project = self.get_project(project_id)

        event_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "agent": agent.value if agent else (project.current_agent.value if project.current_agent else None),
            "phase": project.current_phase,
            "message": message,
            "task_id": str(task_id) if task_id else None,
            "details": details or {},
        }
        project.timeline_events.append(event_entry)
        self.projects[project_id] = project
        self._save_state()
        return project

    def record_file_change(self, project_id: UUID, filepath: str, action: str = "modified") -> Project:
        """Track created and modified files in project state."""
        self.validate_state()
        project = self.get_project(project_id)

        if action in {"created", "NEW"} and filepath not in project.created_files:
            project.created_files.append(filepath)
        elif filepath not in project.modified_files and filepath not in project.created_files:
            project.modified_files.append(filepath)

        self.add_timeline_event(
            project_id=project_id,
            event_type="FILE_CHANGED",
            agent=project.current_agent,
            message=f"File {action}: {filepath}",
            details={"filepath": filepath, "action": action},
        )
        self.projects[project_id] = project
        self._save_state()
        return project

    def record_test_result(self, project_id: UUID, test_info: dict) -> Project:
        """Record test execution outcomes in project state."""
        self.validate_state()
        project = self.get_project(project_id)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": test_info.get("status", "UNKNOWN"),
            "passed": test_info.get("passed", 0),
            "failed": test_info.get("failed", 0),
            "output": test_info.get("output", ""),
        }
        project.test_results.append(record)

        self.add_timeline_event(
            project_id=project_id,
            event_type="TEST_FINISHED",
            agent=AgentRole.TESTER,
            message=f"Test finished: {test_info.get('status', 'UNKNOWN')} ({test_info.get('passed', 0)} passed, {test_info.get('failed', 0)} failed)",
            details=record,
        )
        self.projects[project_id] = project
        self._save_state()
        return project

    def record_review_result(self, project_id: UUID, review_info: dict) -> Project:
        """Record code review outcomes in project state."""
        self.validate_state()
        project = self.get_project(project_id)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": review_info.get("status", "APPROVED"),
            "comments": review_info.get("comments", ""),
            "reviewer": review_info.get("reviewer", AgentRole.REVIEWER.value),
        }
        project.review_results.append(record)

        self.add_timeline_event(
            project_id=project_id,
            event_type="REVIEW_RESULT",
            agent=AgentRole.REVIEWER,
            message=f"Review result: {review_info.get('status', 'APPROVED')}",
            details=record,
        )
        self.projects[project_id] = project
        self._save_state()
        return project

    def record_error_retry(self, project_id: UUID, error_info: dict) -> Project:
        """Record error details and retries attempted."""
        self.validate_state()
        project = self.get_project(project_id)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": error_info.get("agent", project.current_agent.value if project.current_agent else "UNKNOWN"),
            "error": error_info.get("error", "Unknown error"),
            "retry_count": error_info.get("retry_count", 0),
        }
        project.errors_and_retries.append(record)

        self.add_timeline_event(
            project_id=project_id,
            event_type="ERROR",
            agent=project.current_agent,
            message=f"Error encountered: {error_info.get('error')}",
            details=record,
        )
        self.projects[project_id] = project
        self._save_state()
        return project

    def update_project_plan(self, project_id: UUID, plan: ProjectPlan) -> Project:
        """Attach a structured ProjectPlan to a project."""
        self.validate_state()
        project = self.get_project(project_id)

        project.plan = plan
        project.summary = plan.summary

        # Move to PLANNING status if still in CREATED
        if project.status == ProjectStatus.CREATED:
            project.status = ProjectStatus.PLANNING

        self.update_project_phase(project_id, phase="Manager: Requirements & Planning", current_agent=AgentRole.MANAGER)

        self.projects[project_id] = project
        logger.info(f"Project {project_id} plan attached ({len(plan.subtasks)} subtasks).")
        self._save_state()
        return project

    def link_task(self, project_id: UUID, task_id: UUID) -> Project:
        """Link a task UUID to a project."""
        self.validate_state()
        project = self.get_project(project_id)

        if task_id not in project.tasks:
            project.tasks.append(task_id)
            self.projects[project_id] = project
            logger.info(f"Task {task_id} linked to project {project_id}.")
            self._save_state()

        return project

    def sync_project_workspace_files(self, project_id: UUID) -> Project:
        """Scan project workspace directory and sync all generated files into created_files."""
        self.validate_state()
        project = self.get_project(project_id)
        if not project.workspace_path:
            return project

        ws_dir = Path(project.workspace_path)
        if not ws_dir.exists():
            return project

        ignored_patterns = {".git", "__pycache__", ".pytest_cache", ".venv", ".DS_Store"}
        for root, dirs, files in os.walk(ws_dir):
            dirs[:] = [d for d in dirs if d not in ignored_patterns]
            for f in files:
                file_path = Path(root) / f
                try:
                    rel_p = str(file_path.relative_to(ws_dir))
                except ValueError:
                    rel_p = f
                if rel_p not in project.created_files and rel_p not in project.modified_files:
                    project.created_files.append(rel_p)

        self.projects[project_id] = project
        self._save_state()
        return project

    def update_progress(self, project_id: UUID, task_statuses: dict[UUID, str]) -> Project:
        """Recalculate project progress from linked task statuses.

        Args:
            project_id: The project to update.
            task_statuses: Mapping of task_id -> status string for all linked tasks.
        """
        self.validate_state()
        project = self.get_project(project_id)

        if project.status in {ProjectStatus.APPROVED, ProjectStatus.DONE}:
            project.progress = 100.0
            self.projects[project_id] = project
            self._save_state()
            return project

        if not project.tasks:
            project.progress = 0.0
            self.projects[project_id] = project
            self._save_state()
            return project

        done_count = sum(
            1 for tid in project.tasks
            if task_statuses.get(tid, "").upper() == "DONE"
        )
        project.progress = round((done_count / len(project.tasks)) * 100.0, 2)

        self.projects[project_id] = project
        logger.info(f"Project {project_id} progress updated to {project.progress}%.")
        self._save_state()
        return project

    def fail_project(self, project_id: UUID, error_message: str) -> Project:
        """Mark a project as FAILED with an error message."""
        self.validate_state()
        project = self.get_project(project_id)

        project.status = ProjectStatus.FAILED
        project.error_message = error_message
        if project.failed_at is None:
            object.__setattr__(project, "failed_at", datetime.now(timezone.utc))

        self.add_timeline_event(
            project_id=project_id,
            event_type="PROJECT_FAILED",
            agent=project.current_agent,
            message=f"Project failed: {error_message}",
        )
        self.projects[project_id] = project
        logger.error(f"Project {project_id} FAILED: {error_message}")
        self._save_state()
        return project

    def delete_project(self, project_id: UUID) -> None:
        """Remove a project from the manager storage."""
        self.validate_state()
        if project_id not in self.projects:
            raise WorkflowError(f"Project with ID {project_id} not found in ProjectManager.")
        del self.projects[project_id]
        logger.info(f"Project {project_id} deleted from ProjectManager.")
        self._save_state()

    def validate_project_workspace(self, project_id: UUID) -> bool:
        """Perform pre-approval validation on the project workspace to ensure a runnable software project."""
        self.validate_state()
        project = self.get_project(project_id)
        if not project.workspace_path:
            raise WorkflowError("Project has no workspace path allocated.")

        ws_dir = Path(project.workspace_path)
        if not ws_dir.exists():
            raise WorkflowError(f"Workspace directory {ws_dir} does not exist.")

        self.sync_project_workspace_files(project_id)
        project = self.get_project(project_id)

        source_exts = {".py", ".js", ".ts", ".go", ".java", ".c", ".cpp", ".html", ".css", ".rs", ".php", ".rb"}
        has_source = any(Path(f).suffix.lower() in source_exts for f in project.created_files)
        if not has_source:
            raise WorkflowError("Workspace validation failed: No runnable source code files were created in the project workspace.")

        has_readme = any(f.lower().endswith("readme.md") for f in project.created_files)
        if not has_readme:
            raise WorkflowError("Workspace validation failed: README.md is missing from the project workspace.")

        return True

    def validate_against_manifest(self, project_id: UUID, required_files: list) -> dict:
        """Validate workspace files against the architect's required_files manifest."""
        self.validate_state()
        project = self.get_project(project_id)
        self.sync_project_workspace_files(project_id)

        existing = set(project.created_files + project.modified_files)
        missing = []

        for req in required_files:
            path = req.get("path") if isinstance(req, dict) else str(req)
            if path and path not in existing:
                req_name = Path(path).name
                if not any(Path(e).name == req_name for e in existing):
                    missing.append(path)

        return {
            "valid": len(missing) == 0,
            "missing_files": missing,
            "total_required": len(required_files),
            "existing_count": len(existing),
        }

    def validate_project_zip(self, zip_path: Path) -> dict:
        """Programmatically open ZIP archive and validate file contents, root structure, and security."""
        import zipfile

        if not zip_path.exists():
            raise WorkflowError(f"ZIP archive {zip_path} does not exist.")

        with zipfile.ZipFile(zip_path, mode="r") as zf:
            file_list = zf.namelist()
            if not file_list:
                raise WorkflowError("ZIP archive is empty.")

            source_extensions = {".py", ".js", ".ts", ".go", ".java", ".c", ".cpp", ".html", ".css", ".rs", ".php", ".rb"}
            has_source_file = any(
                Path(f).suffix.lower() in source_extensions for f in file_list
            )
            if not has_source_file:
                raise WorkflowError("ZIP validation failed: Archive contains only documentation and no runnable source code files.")

            for fname in file_list:
                if fname.startswith("/") or ".." in fname:
                    raise WorkflowError(f"ZIP validation failed: Path traversal detected in archive entry '{fname}'.")

            secret_keywords = {"sk-proj-", "AWS_SECRET_ACCESS_KEY", "-----BEGIN PRIVATE KEY-----"}
            for fname in file_list:
                if not fname.endswith((".py", ".env", ".toml", ".json", ".yaml", ".yml", ".md", ".txt")):
                    continue
                try:
                    content = zf.read(fname).decode("utf-8", errors="ignore")
                    for secret in secret_keywords:
                        if secret in content:
                            raise WorkflowError(f"ZIP validation failed: Possible secret key found in '{fname}'.")
                except Exception:
                    pass

            size_bytes = zip_path.stat().st_size
            file_count = len(file_list)
            
            return {
                "file_count": file_count,
                "size_bytes": size_bytes,
                "file_list": file_list,
                "has_source_file": has_source_file,
            }

    def create_project_zip(self, project_id: UUID) -> Path:
        """Package the completed project workspace and documentation into a ZIP file."""
        import zipfile
        from app.projects.report_generator import ReportGenerator

        self.validate_state()
        project = self.get_project(project_id)

        # 1. Ensure all documentation reports are generated in the project workspace
        generator = ReportGenerator(project)
        generator.generate_all_reports()
        self.sync_project_workspace_files(project_id)

        # 2. Prepare ZIP archive location
        data_dir = Path(settings.data_dir) / "projects" / str(project_id)
        data_dir.mkdir(parents=True, exist_ok=True)
        zip_path = data_dir / f"project_{project_id}.zip"

        workspace_dir = Path(project.workspace_path) if project.workspace_path else Path(".")

        # Clean root folder name inside archive based on project prompt
        project_slug = "".join(c if c.isalnum() or c in "_-" else "" for c in project.prompt.lower().replace(" ", "_")[:30]) or "project"

        ignored_patterns = {"__pycache__", ".pytest_cache", ".git", ".venv", ".DS_Store"}

        # 3. Create ZIP archive containing all files in workspace
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(workspace_dir):
                dirs[:] = [d for d in dirs if d not in ignored_patterns]
                for file in files:
                    if file.endswith(".pyc") or file in ignored_patterns:
                        continue
                    file_path = Path(root) / file
                    if file_path.resolve() == zip_path.resolve():
                        continue
                    rel_p = file_path.relative_to(workspace_dir)
                    arcname = f"{project_slug}/{rel_p}"
                    zip_file.write(file_path, arcname=arcname)

        # 4. Programmatic ZIP validation
        zip_info = self.validate_project_zip(zip_path)
        self.add_timeline_event(
            project_id=project_id,
            event_type="ZIP_CREATED",
            agent=project.current_agent,
            message=f"ZIP archive packaged and validated ({zip_info['file_count']} files, {zip_info['size_bytes']} bytes).",
        )
        self.projects[project_id] = project
        self._save_state()

        logger.info(f"Created ZIP archive for project {project_id} at {zip_path} ({zip_info['file_count']} files, {zip_info['size_bytes']} bytes)")
        return zip_path


