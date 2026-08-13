"""TestResult value object for structured test outcome reporting."""

from pydantic import Field
from app.schemas.base import BaseSchema


class TestResult(BaseSchema):
    """Structured result from a test execution suite."""

    passed: bool = Field(
        ..., description="True if all tests passed, False otherwise."
    )
    tests_collected: int = Field(default=0, description="Total number of tests collected by the test runner.")
    tests_passed: int = Field(default=0, description="Number of tests that passed.")
    tests_failed: int = Field(default=0, description="Number of tests that failed.")
    failed_test_names: list[str] = Field(
        default_factory=list, description="List of the names of tests that failed."
    )
    error_summary: str = Field(
        default="", description="A concise summary of the errors encountered during testing."
    )
    stdout: str = Field(
        default="", description="Standard output from the test runner."
    )
    stderr: str = Field(
        default="", description="Standard error from the test runner."
    )
