from app.news.models import NewsItem
from app.news.service import NewsService, filter_news
from app.news.source import MockNewsSource, parse_feed


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

