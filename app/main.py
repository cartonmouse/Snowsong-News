from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.routes import create_router
from app.core.config import get_settings
from app.storage.database import Database


def create_app(
    settings=None,
    database: Database | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    database = database or Database(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database.migrate()
        yield
        database.close()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Daily AI news assistant Agent.",
        lifespan=lifespan,
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
        }

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(
            Path(__file__).resolve().parent / "web" / "index.html"
        )

    application.include_router(create_router(settings, database))
    return application


app = create_app()

