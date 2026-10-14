from pathlib import Path

from app.news.service import NewsService
from app.storage.database import Database
from app.storage.repository import NewsRepository
from app.tools.business import NewsBusinessTools
from app.tools.registry import BUSINESS_TOOL_NAMES, REQUIRED_TOOL_NAMES, build_default_registry


def test_business_tools_complete_local_news_flow(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'news.db'}")
    database.migrate()
    repository = NewsRepository(database.session_factory)
    user = repository.create_or_update_user("Alice", "AI engineer")
    repository.save_subscription(
        user.id,
        topics=["agents"],
        keywords=["tool"],
        sources=["mock"],
    )
    business_tools = NewsBusinessTools(
        repository,
        NewsService(mode="mock"),
    )
    registry = build_default_registry(
        tmp_path / "workspace",
        business_tools=business_tools,
    )

    preferences = registry.invoke(
        "get_user_preferences",
        {"user_id": user.id},
    )
    news = registry.invoke(
        "fetch_news",
        {"query": "agents", "limit": 5},
    )
    saved = registry.invoke(
        "save_brief",
        {
            "user_id": user.id,
            "title": "Daily AI Brief",
            "content": "A short brief.",
            "source_count": news["count"],
        },
    )
    delivered = registry.invoke(
        "deliver_brief",
        {
            "user_id": user.id,
            "content": "A short brief.",
            "channel": "history",
        },
    )

    assert registry.names == REQUIRED_TOOL_NAMES + BUSINESS_TOOL_NAMES
    assert preferences["ok"] is True
    assert preferences["preferences"]["topics"] == ["agents"]
    assert news["ok"] is True
    assert news["count"] > 0
    assert saved["ok"] is True
    assert delivered["delivered"] is True
    database.close()

