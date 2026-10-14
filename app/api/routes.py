from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.schemas import SubscriptionUpdate, UserCreate
from app.core.config import Settings
from app.storage.database import Database
from app.storage.repository import NewsRepository, RepositoryError
from app.services.generation import run_news_agent


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

        return run_news_agent(settings, database, user_id)

    return router

