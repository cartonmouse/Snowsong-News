from pathlib import Path

from app.storage.database import Database
from app.storage.repository import NewsRepository


def test_database_migration_and_repository(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'news.db'}")
    database.migrate()
    repository = NewsRepository(database.session_factory)

    user = repository.create_or_update_user("Alice", "AI engineer")
    repository.save_subscription(
        user.id,
        topics=["agents"],
        keywords=["function calling"],
        sources=["mock"],
        push_channel="history",
    )

    preferences = repository.get_preferences(user.id)
    brief = repository.save_brief(
        user.id,
        title="Daily AI Brief",
        content="One useful item.",
        source_count=1,
    )
    briefs = repository.list_briefs(user.id)

    assert preferences["keywords"] == ["function calling"]
    assert preferences["push_channel"] == "history"
    assert brief.id is not None
    assert briefs[0].title == "Daily AI Brief"
    database.close()

