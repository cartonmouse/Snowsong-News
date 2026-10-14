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
    webhook_url: str | None = None
    max_agent_steps: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()

