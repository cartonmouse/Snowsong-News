from pathlib import Path

from app.core.config import Settings
from app.scheduler import DailyScheduler
from app.storage.database import Database
from app.storage.repository import NewsRepository


def test_scheduler_disabled_by_default(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'news.db'}",
        scheduler_enabled=False,
    )
    database = Database(settings.database_url)
    scheduler = DailyScheduler(settings, database)

    assert scheduler.start() is False
    assert scheduler.scheduler.running is False
    scheduler.stop()
    database.close()


def test_scheduler_registers_configured_cron_job(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'news.db'}",
        scheduler_enabled=True,
        schedule_hour=6,
        schedule_minute=30,
        schedule_timezone="Asia/Shanghai",
    )
    database = Database(settings.database_url)
    database.migrate()
    scheduler = DailyScheduler(settings, database)

    assert scheduler.start() is True
    job = scheduler.scheduler.get_job(scheduler.job_id)
    assert job is not None
    assert "hour='6'" in str(job.trigger)
    assert "minute='30'" in str(job.trigger)
    scheduler.stop()
    database.close()


def test_scheduler_runs_all_users(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'news.db'}",
        scheduler_enabled=False,
    )
    database = Database(settings.database_url)
    database.migrate()
    repository = NewsRepository(database.session_factory)
    first = repository.create_or_update_user("Alice")
    second = repository.create_or_update_user("Bob")
    calls = []

    def fake_run(settings, database, user_id):
        calls.append(user_id)
        return {"status": "completed", "trace": []}

    monkeypatch.setattr("app.scheduler.run_news_agent", fake_run)
    scheduler = DailyScheduler(settings, database)

    results = scheduler.run_all_users()

    assert calls == [first.id, second.id]
    assert [item["status"] for item in results] == [
        "completed",
        "completed",
    ]
    database.close()
