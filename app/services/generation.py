from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.agent.factory import build_provider
from app.agent.runner import AgentRunner
from app.core.config import Settings
from app.news.service import NewsService
from app.storage.database import Database
from app.storage.repository import NewsRepository, RepositoryError
from app.tools.business import NewsBusinessTools
from app.tools.registry import build_default_registry


def run_news_agent(
    settings: Settings,
    database: Database,
    user_id: int,
) -> dict[str, Any]:
    repository = NewsRepository(database.session_factory)
    try:
        repository.get_preferences(user_id)
    except RepositoryError as exc:
        return {
            "status": "failed",
            "content": "",
            "brief_id": None,
            "steps": 0,
            "error": str(exc),
            "trace": [],
        }

    feeds = tuple(
        feed.strip()
        for feed in settings.news_feeds.split(",")
        if feed.strip()
    )
    business_tools = NewsBusinessTools(
        repository,
        NewsService(
            mode=settings.news_mode,
            feeds=feeds,
            timeout_seconds=settings.news_timeout_seconds,
            fallback_to_mock=settings.news_fallback_to_mock,
        ),
        webhook_url=settings.webhook_url,
        timeout_seconds=settings.news_timeout_seconds,
    )
    registry = build_default_registry(business_tools=business_tools)
    provider = build_provider(settings, user_id)
    try:
        result = AgentRunner(
            provider,
            registry,
            max_steps=settings.max_agent_steps,
        ).run(
            "Generate a personalized AI news brief for the user. "
            f"The user_id is {user_id}. Use the user's preferences, "
            "save the completed brief, and deliver it through the configured "
            "channel.",
        )
    finally:
        close = getattr(provider, "close", None)
        if close is not None:
            close()

    brief_id = None
    for record in result.trace:
        if record.name == "save_brief" and record.result.get("ok"):
            brief_id = record.result.get("brief_id")
            break
    return {
        "status": result.status,
        "content": result.content,
        "brief_id": brief_id,
        "steps": result.steps,
        "error": result.error,
        "trace": [asdict(record) for record in result.trace],
    }

