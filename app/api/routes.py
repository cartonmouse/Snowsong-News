from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException

from app.agent.factory import build_provider
from app.agent.runner import AgentRunner
from app.api.schemas import SubscriptionUpdate, UserCreate
from app.core.config import Settings
from app.news.service import NewsService
from app.storage.database import Database
from app.storage.repository import NewsRepository, RepositoryError
from app.tools.business import NewsBusinessTools
from app.tools.registry import build_default_registry


def _brief_to_dict(brief: Any) -> dict[str, Any]:
    return {
        "id": brief.id,
        "user_id": brief.user_id,
        "title": brief.title,
        "content": brief.content,
        "source_count": brief.source_count,
        "status": brief.status,
        "created_at": brief.created_at.isoformat(),
    }


def _build_business_tools(
    settings: Settings,
    database: Database,
    repository: NewsRepository,
) -> NewsBusinessTools:
    feeds = tuple(
        feed.strip()
        for feed in settings.news_feeds.split(",")
        if feed.strip()
    )
    return NewsBusinessTools(
        repository,
        NewsService(
            mode=settings.news_mode,
            feeds=feeds,
            timeout_seconds=settings.news_timeout_seconds,
        ),
        webhook_url=settings.webhook_url,
        timeout_seconds=settings.news_timeout_seconds,
    )


def create_router(settings: Settings, database: Database) -> APIRouter:
    router = APIRouter(prefix="/api")
    repository = NewsRepository(database.session_factory)

    @router.post("/users")
    def create_user(payload: UserCreate) -> dict[str, Any]:
        try:
            user = repository.create_or_update_user(
                payload.name,
                payload.role,
            )
        except RepositoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"id": user.id, "name": user.name, "role": user.role}

    @router.put("/users/{user_id}/subscription")
    def update_subscription(
        user_id: int,
        payload: SubscriptionUpdate,
    ) -> dict[str, Any]:
        try:
            subscription = repository.save_subscription(
                user_id,
                topics=payload.topics,
                keywords=payload.keywords,
                sources=payload.sources,
                push_channel=payload.push_channel,
            )
        except RepositoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "push_channel": subscription.push_channel,
        }

    @router.get("/users/{user_id}/preferences")
    def get_preferences(user_id: int) -> dict[str, Any]:
        try:
            return repository.get_preferences(user_id)
        except RepositoryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/users/{user_id}/briefs")
    def list_briefs(user_id: int) -> dict[str, Any]:
        try:
            briefs = repository.list_briefs(user_id)
        except RepositoryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"items": [_brief_to_dict(brief) for brief in briefs]}

    @router.post("/users/{user_id}/generate")
    def generate_brief(user_id: int) -> dict[str, Any]:
        try:
            repository.get_preferences(user_id)
        except RepositoryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        business_tools = _build_business_tools(
            settings,
            database,
            repository,
        )
        registry = build_default_registry(
            business_tools=business_tools,
        )
        provider = build_provider(settings, user_id)
        runner = AgentRunner(
            provider,
            registry,
            max_steps=settings.max_agent_steps,
        )
        result = runner.run(
            "Generate a personalized AI news brief for the user. "
            f"The user_id is {user_id}. Use the user's preferences, "
            "save the completed brief, and deliver it through the configured "
            "channel.",
        )
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

    return router

