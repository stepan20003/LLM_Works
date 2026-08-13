"""Pydantic settings for global application configuration and environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings loaded from environment variables or defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Development Team"
    environment: str = "development"
    debug: bool = True
    
    # LLM Settings
    provider: str = "openai"
    llm_model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    openai_api_key: str = ""
    base_url: str | None = None

    # Agent-to-Model configuration mapping
    agent_models: dict[str, str] = Field(
        default_factory=lambda: {
            "manager": "default",
            "architect": "default",
            "developer": "default",
            "reviewer": "default",
            "tester": "default",
            "debugger": "default",
        },
        description="Mapping of agent roles to model IDs from the ModelRegistry."
    )

    # Execution & Workflow Settings
    max_debug_iterations: int = 5
    max_retries: int = 5
    workspace_dir: str = "./workspace_sandbox"
    data_dir: str = "./data"
    orchestrator_auto_run: bool = True
    orchestrator_poll_interval_seconds: float = 0.5


settings = Settings()