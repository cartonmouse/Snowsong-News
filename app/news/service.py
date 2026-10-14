from __future__ import annotations

import re
from typing import Sequence

from app.news.models import NewsItem
from app.news.source import MockNewsSource, NewsSourceError, RssNewsSource


_QUERY_ALIASES: dict[str, tuple[str, ...]] = {
    "人工智能": ("ai", "artificial intelligence"),
    "大语言模型": (
        "llm",
        "large language model",
        "large language models",
        "foundation model",
        "foundation models",
    ),
    "大模型": (
        "llm",
        "large language model",
        "large language models",
        "foundation model",
        "foundation models",
    ),
    "生成式人工智能": ("generative ai", "genai"),
    "智能体": ("ai agent", "ai agents", "agentic ai", "agentic", "agents"),
    "函数调用": ("function calling", "tool calling", "tool use"),
    "工具调用": ("function calling", "tool calling", "tool use"),
    "检索增强生成": (
        "rag",
        "retrieval augmented generation",
        "retrieval-augmented generation",
    ),
    "向量数据库": ("vector database", "vector db"),
    "多模态": ("multimodal", "vision-language", "vision language"),
    "机器学习": ("machine learning", "ml"),
    "深度学习": ("deep learning",),
    "自然语言处理": ("natural language processing", "nlp"),
    "计算机视觉": ("computer vision",),
    "语音": ("speech", "voice"),
    "机器人": ("robotics", "humanoid robot", "robot"),
    "自动驾驶": ("autonomous driving", "self-driving"),
    "芯片": ("chip", "chips", "semiconductor", "gpu"),
    "科技股票": (
        "ai stocks",
        "tech stocks",
        "technology stocks",
        "semiconductor stocks",
        "stock",
        "stocks",
        "shares",
        "stock market",
        "markets",
        "earnings",
    ),
    "科技股": (
        "ai stocks",
        "tech stocks",
        "technology stocks",
        "semiconductor stocks",
        "stock",
        "stocks",
        "shares",
        "stock market",
        "markets",
        "earnings",
    ),
    "开源模型": ("open source model", "open-source model", "open models"),
    "谷歌": ("google", "deepmind", "gemini"),
    "英伟达": ("nvidia", "gpu"),
    "微软": ("microsoft",),
    "苹果": ("apple",),
}


def _terms(query: str) -> list[str]:
    normalized_query = query.casefold()
    terms: list[str] = []
    for segment in re.split(r"[,，、\n]+", normalized_query):
        segment = segment.strip()
        if not segment:
            continue
        terms.append(segment)
        terms.extend(token for token in re.split(r"\s+", segment) if token)

    for source_term, aliases in _QUERY_ALIASES.items():
        if source_term.casefold() in normalized_query:
            terms.extend(alias.casefold() for alias in aliases)

    return list(dict.fromkeys(terms))


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

    # Keep a single high-volume feed from crowding out every other source.
    # If only one source matches, deferred items are still used to fill the limit.
    source_cap = max(2, (safe_limit + 2) // 3)
    selected: list[tuple[int, int, NewsItem]] = []
    deferred: list[tuple[int, int, NewsItem]] = []
    source_counts: dict[str, int] = {}
    for row in scored:
        source = row[2].source or row[2].url
        if source_counts.get(source, 0) < source_cap:
            selected.append(row)
            source_counts[source] = source_counts.get(source, 0) + 1
        else:
            deferred.append(row)
        if len(selected) >= safe_limit:
            break

    if len(selected) < safe_limit:
        selected.extend(deferred[: safe_limit - len(selected)])
    return [row[2] for row in selected[:safe_limit]]


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
                items = self.rss_source.fetch(self.feeds, limit=limit * 3)
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

