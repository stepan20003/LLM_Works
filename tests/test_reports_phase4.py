"""Tests for Phase 4: Documentation & Report Generation."""

import pytest
from pathlib import Path
from app.schemas.entities.project import Project
from app.schemas.enums import ProjectStatus, AgentRole
from app.projects.report_generator import ReportGenerator


def test_report_generator(tmp_path):
    """Verify that ReportGenerator creates all 6 required documentation markdown files."""
    workspace = tmp_path / "project_workspace"
    workspace.mkdir()

    project = Project(
        prompt="Build a payment microservice",
        summary="Payment processing API",
        status=ProjectStatus.APPROVED,
        workspace_path=str(workspace),
        created_files=["app/main.py", "app/models.py"],
        test_results=[{"timestamp": "2026-08-09T19:00:00Z", "status": "PASSED", "passed": 3, "failed": 0}],
        review_results=[{"timestamp": "2026-08-09T19:05:00Z", "status": "APPROVED", "comments": "LGT2M"}],
    )

    generator = ReportGenerator(project)
    generated_files = generator.generate_all_reports()

    expected_names = [
        "README.md",
        "REQUIREMENTS.md",
        "ARCHITECTURE.md",
        "TEST_REPORT.md",
        "PROJECT_REPORT.md",
        "CHANGELOG.md",
    ]

    for name in expected_names:
        assert name in generated_files
        file_path = Path(generated_files[name])
        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert len(content) > 50

    # Verify PROJECT_REPORT.md contains all required sections
    report_content = (workspace / "PROJECT_REPORT.md").read_text(encoding="utf-8")
    assert "Original User Request" in report_content
    assert "Requirements Analysis" in report_content
    assert "Architecture Overview" in report_content
    assert "Implementation Details" in report_content
    assert "Test Execution & Verification Results" in report_content
    assert "Review & Quality Assurance Findings" in report_content
    assert "Encountered Errors" in report_content
    assert "Final Status" in report_content
    assert "Known Limitations" in report_content
    assert "Run & Setup Instructions" in report_content
