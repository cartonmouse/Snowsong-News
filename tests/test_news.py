import pytest

from app.news.models import NewsItem
from app.news.service import NewsService, filter_news
from app.news.source import MockNewsSource, NewsSourceError, RssNewsSource, parse_feed


def test_filter_news_ranks_matching_items() -> None:
    items = [
        NewsItem("Other story", "https://example.com/1", "general", "test"),
        NewsItem(
            "Function calling update",
            "https://example.com/2",
            "agent tools",
            "test",
        ),
    ]

    result = filter_news(items, query="function calling", limit=5)

    assert [item.title for item in result] == ["Function calling update"]


def test_filter_news_supports_chinese_enumeration_separator() -> None:
    items = [
        NewsItem(
            "Open models improve function calling",
            "https://example.com/1",
            "A practical update for AI agents.",
            "test",
        ),
    ]

    result = filter_news(items, query="RAG、Function Calling、OpenAI", limit=5)

    assert result == items


def test_filter_news_expands_chinese_topics_to_english_terms() -> None:
    item = NewsItem(
        "A new large language model improves tool use",
        "https://example.com/llm",
        "The foundation model supports reliable function calling.",
        "test",
    )

    result = filter_news([item], query="大语言模型", limit=5)

    assert result == [item]


def test_mock_news_service_returns_query_matches() -> None:
    service = NewsService(mode="mock")

    result = service.fetch(query="agents", limit=10)

    assert result
    assert all("agents" in item.searchable_text.casefold() for item in result)


def test_parse_rss_feed() -> None:
    payload = b"""
    <rss version="2.0"><channel>
      <item>
        <title>RSS title</title>
        <link>https://example.com/rss</link>
        <description>A summary.</description>
        <pubDate>Tue, 14 Oct 2026 08:00:00 GMT</pubDate>
      </item>
    </channel></rss>
    """

    result = parse_feed(payload, source="test-feed")

    assert result[0].title == "RSS title"
    assert result[0].url == "https://example.com/rss"
    assert result[0].source == "test-feed"


def test_mock_source_is_deterministic() -> None:
    source = MockNewsSource()

    first = source.fetch()
    second = source.fetch()

    assert first == second


def test_rss_failure_can_be_returned_without_mock_fallback() -> None:
    class FailingSource:
        def fetch(self, feeds: list[str], limit: int = 20) -> list[NewsItem]:
            raise NewsSourceError("feed unavailable")

    service = NewsService(
        mode="rss",
        feeds=["https://example.com/feed.xml"],
        rss_source=FailingSource(),
        fallback_to_mock=False,
    )

    with pytest.raises(NewsSourceError, match="feed unavailable"):
        service.fetch()


def test_rss_source_keeps_successful_feeds_when_one_feed_fails(monkeypatch) -> None:
    payload = b"""
    <rss version="2.0"><channel>
      <item>
        <title>Working feed item</title>
        <link>https://example.com/working</link>
        <description>AI update.</description>
      </item>
    </channel></rss>
    """

    def fake_get(url: str, **kwargs):
        if url.endswith("bad.xml"):
            import httpx

            raise httpx.ConnectError("offline", request=httpx.Request("GET", url))
        import httpx

        return httpx.Response(
            200,
            content=payload,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr("app.news.source.httpx.get", fake_get)
    source = RssNewsSource()

    result = source.fetch(
        ["https://example.com/bad.xml", "https://example.com/working.xml"],
        limit=10,
    )

    assert [item.title for item in result] == ["Working feed item"]
    assert "https://example.com/bad.xml" in source.last_errors
    assert source.last_successful_feeds == ("https://example.com/working.xml",)

