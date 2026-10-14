from __future__ import annotations

import re
from typing import Sequence

from app.news.models import NewsItem
from app.news.source import MockNewsSource, NewsSourceError, RssNewsSource


def _terms(query: str) -> list[str]:
    return [
        item.casefold()
        for item in re.split(r"[,，、\s]+", query)
        if item.strip()
    ]


def filter_news(
    items: Sequence[NewsItem],
    query: str = "",
    limit: int = 20,
) -> list[NewsItem]:
    safe_limit = max(0, min(limit, 100))
    if safe_limit == 0:
        return []

    terms = _terms(query)
    if not terms:
        return list(items[:safe_limit])

    scored: list[tuple[int, int, NewsItem]] = []
    for index, item in enumerate(items):
        searchable = item.searchable_text.casefold()
        score = sum(term in searchable for term in terms)
        if score:
            scored.append((score, -index, item))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [row[2] for row in scored[:safe_limit]]


class NewsService:
    def __init__(
        self,
        *,
        mode: str = "mock",
        feeds: Sequence[str] = (),
        timeout_seconds: float = 10,
        mock_source: MockNewsSource | None = None,
        rss_source: RssNewsSource | None = None,
        fallback_to_mock: bool = True,
    ) -> None:
        self.mode = mode
        self.feeds = tuple(feed for feed in feeds if feed)
        self.mock_source = mock_source or MockNewsSource()
        self.rss_source = rss_source or RssNewsSource(timeout_seconds)
        self.fallback_to_mock = fallback_to_mock
        self.last_source_mode = "mock"

    def fetch(self, query: str = "", limit: int = 20) -> list[NewsItem]:
        if self.mode.casefold() == "rss" and self.feeds:
            try:
                items = self.rss_source.fetch(self.feeds, limit=limit * 2)
            except NewsSourceError:
                if not self.fallback_to_mock:
                    raise
                items = self.mock_source.fetch(limit=limit * 2)
                self.last_source_mode = "mock"
            else:
                self.last_source_mode = "rss"
        else:
            items = self.mock_source.fetch(limit=limit * 2)
            self.last_source_mode = "mock"
        return filter_news(items, query=query, limit=limit)

