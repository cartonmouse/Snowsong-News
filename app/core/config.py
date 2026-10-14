from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "News Agent"
    environment: str = "development"
    database_url: str = "sqlite:///./data/news_agent.db"
    openai_base_url: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "mock"
    news_mode: str = "mock"
    news_feeds: str = ""
    news_timeout_seconds: int = 10
    news_fallback_to_mock: bool = False
    webhook_url: str | None = None
    max_agent_steps: int = 8
    tool_workspace_root: str = "data/agent_workspace"
    bash_timeout_seconds: int = 10
    tool_output_max_chars: int = 4000
    scheduler_enabled: bool = False
    schedule_hour: int = 8
    schedule_minute: int = 0
    schedule_timezone: str = "Asia/Shanghai"
    tool_workspace_root: str = "data/agent_workspace"
    bash_timeout_seconds: int = 10
    tool_output_max_chars: int = 4000


@lru_cache
def get_settings() -> Settings:
    return Settings()

