from __future__ import annotations

from typing import Any

from app.agent.demo import DemoNewsProvider
from app.agent.provider import LLMProvider, OpenAICompatibleProvider


def build_provider(settings: Any, user_id: int) -> LLMProvider:
    if (
        settings.llm_model.casefold() != "mock"
        and settings.openai_base_url
        and settings.openai_api_key
    ):
        return OpenAICompatibleProvider(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.llm_model,
        )
    return DemoNewsProvider(user_id)

