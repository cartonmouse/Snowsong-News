from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.models import Brief, Subscription, User


class RepositoryError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dump_list(value: list[str] | tuple[str, ...]) -> str:
    return json.dumps(list(value), ensure_ascii=False)


def _load_list(value: str) -> list[str]:
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


class NewsRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def create_or_update_user(self, name: str, role: str = "") -> User:
        if not name.strip():
            raise RepositoryError("user name must not be empty")
        with self.session_factory() as session:
            user = session.scalar(select(User).where(User.name == name))
            if user is None:
                user = User(name=name.strip(), role=role.strip())
                session.add(user)
            else:
                user.role = role.strip()
                user.updated_at = _now()
            session.commit()
            session.refresh(user)
            return user

    def save_subscription(
        self,
        user_id: int,
        *,
        topics: list[str],
        keywords: list[str],
        sources: list[str],
        push_channel: str = "history",
    ) -> Subscription:
        with self.session_factory() as session:
            if session.get(User, user_id) is None:
                raise RepositoryError(f"user does not exist: {user_id}")
            subscription = session.scalar(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            if subscription is None:
                subscription = Subscription(user_id=user_id)
                session.add(subscription)
            subscription.topics = _dump_list(topics)
            subscription.keywords = _dump_list(keywords)
            subscription.sources = _dump_list(sources)
            subscription.push_channel = push_channel
            subscription.updated_at = _now()
            session.commit()
            session.refresh(subscription)
            return subscription

    def get_preferences(self, user_id: int) -> dict[str, Any]:
        with self.session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                raise RepositoryError(f"user does not exist: {user_id}")
            subscription = session.scalar(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            if subscription is None:
                return {
                    "user_id": user_id,
                    "name": user.name,
                    "role": user.role,
                    "topics": [],
                    "keywords": [],
                    "sources": [],
                    "push_channel": "history",
                }
            return {
                "user_id": user_id,
                "name": user.name,
                "role": user.role,
                "topics": _load_list(subscription.topics),
                "keywords": _load_list(subscription.keywords),
                "sources": _load_list(subscription.sources),
                "push_channel": subscription.push_channel,
            }

    def save_brief(
        self,
        user_id: int,
        *,
        title: str,
        content: str,
        source_count: int = 0,
        status: str = "created",
    ) -> Brief:
        if not title.strip() or not content.strip():
            raise RepositoryError("brief title and content must not be empty")
        with self.session_factory() as session:
            if session.get(User, user_id) is None:
                raise RepositoryError(f"user does not exist: {user_id}")
            brief = Brief(
                user_id=user_id,
                title=title.strip(),
                content=content,
                source_count=source_count,
                status=status,
            )
            session.add(brief)
            session.commit()
            session.refresh(brief)
            return brief

    def list_users(self) -> list[User]:
        with self.session_factory() as session:
            return list(
                session.scalars(
                    select(User).order_by(User.id.asc())
                )
            )

    def list_briefs(self, user_id: int, limit: int = 20) -> list[Brief]:
        safe_limit = max(1, min(limit, 100))
        with self.session_factory() as session:
            return list(
                session.scalars(
                    select(Brief)
                    .where(Brief.user_id == user_id)
                    .order_by(Brief.created_at.desc())
                    .limit(safe_limit)
                )
            )

