from __future__ import annotations

from typing import Any

import httpx

from app.news.service import NewsService
from app.storage.repository import NewsRepository, RepositoryError
from app.tools.base import ToolError


class NewsBusinessTools:
    def __init__(
        self,
        repository: NewsRepository,
        news_service: NewsService,
        *,
        webhook_url: str | None = None,
        timeout_seconds: float = 10,
    ) -> None:
        self.repository = repository
        self.news_service = news_service
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def get_user_preferences(self, user_id: int) -> dict[str, Any]:
        try:
            return {
                "ok": True,
                "preferences": self.repository.get_preferences(user_id),
            }
        except RepositoryError as exc:
            raise ToolError(str(exc)) from exc

    def fetch_news(self, query: str = "", limit: int = 10) -> dict[str, Any]:
        items = self.news_service.fetch(query=query, limit=limit)
        return {
            "ok": True,
            "query": query,
            "count": len(items),
            "items": [item.to_dict() for item in items],
        }

    def save_brief(
        self,
        user_id: int,
        title: str,
        content: str,
        source_count: int = 0,
    ) -> dict[str, Any]:
        try:
            brief = self.repository.save_brief(
                user_id,
                title=title,
                content=content,
                source_count=source_count,
            )
        except RepositoryError as exc:
            raise ToolError(str(exc)) from exc
        return {
            "ok": True,
            "brief_id": brief.id,
            "title": brief.title,
            "created_at": brief.created_at.isoformat(),
        }

    def deliver_brief(
        self,
        user_id: int,
        content: str,
        channel: str = "history",
    ) -> dict[str, Any]:
        normalized_channel = channel.casefold()
        if normalized_channel in {"history", "web"}:
            return {
                "ok": True,
                "user_id": user_id,
                "channel": "history",
                "delivered": True,
            }
        if normalized_channel != "webhook":
            raise ToolError(f"unsupported delivery channel: {channel}")
        if not self.webhook_url:
            raise ToolError("WEBHOOK_URL is not configured")

        try:
            response = httpx.post(
                self.webhook_url,
                json={"user_id": user_id, "content": content},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ToolError(f"webhook delivery failed: {exc}") from exc
        return {
            "ok": True,
            "user_id": user_id,
            "channel": "webhook",
            "delivered": True,
            "status_code": response.status_code,
        }

