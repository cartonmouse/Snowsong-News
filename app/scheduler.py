from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import Settings
from app.services.generation import run_news_agent
from app.storage.database import Database
from app.storage.repository import NewsRepository


class DailyScheduler:
    job_id = "daily-news-agent"

    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings = settings
        self.database = database
        self.scheduler = BackgroundScheduler(
            timezone=ZoneInfo(settings.schedule_timezone),
        )
        self._started = False

    def _trigger(self) -> CronTrigger:
        return CronTrigger(
            hour=self.settings.schedule_hour,
            minute=self.settings.schedule_minute,
            timezone=ZoneInfo(self.settings.schedule_timezone),
        )

    def start(self) -> bool:
        if not self.settings.scheduler_enabled:
            return False
        self.scheduler.add_job(
            self.run_all_users,
            trigger=self._trigger(),
            id=self.job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
        )
        self.scheduler.start()
        self._started = True
        return True

    def run_all_users(self) -> list[dict[str, Any]]:
        repository = NewsRepository(self.database.session_factory)
        results = []
        for user in repository.list_users():
            try:
                result = run_news_agent(
                    self.settings,
                    self.database,
                    user.id,
                )
            except Exception as exc:
                result = {
                    "status": "failed",
                    "error": str(exc),
                    "user_id": user.id,
                }
            results.append({"user_id": user.id, **result})
        return results

    def stop(self) -> None:
        if self._started and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self._started = False

