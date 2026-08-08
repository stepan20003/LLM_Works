"""Pydantic settings for global application configuration and environment variables."""

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
    base_url: str | None = None  # Ավելացրու այս տողը

    # Execution & Workflow Settings
    max_debug_iterations: int = 5
    max_retries: int = 5
    workspace_dir: str = "./workspace_sandbox"


settings = Settings()