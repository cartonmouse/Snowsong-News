from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class Database:
    def __init__(
        self,
        database_url: str,
        *,
        migration_path: str | Path | None = None,
    ) -> None:
        if database_url.startswith("sqlite:///") and ":memory:" not in database_url:
            database_path = Path(database_url.removeprefix("sqlite:///"))
            if not database_path.is_absolute():
                database_path = Path.cwd() / database_path
            database_path.parent.mkdir(parents=True, exist_ok=True)

        connect_args = (
            {"check_same_thread": False}
            if database_url.startswith("sqlite")
            else {}
        )
        self.engine: Engine = create_engine(
            database_url,
            connect_args=connect_args,
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        self.migration_path = Path(migration_path) if migration_path else (
            Path(__file__).resolve().parents[2]
            / "migrations"
            / "001_initial.sql"
        )

    def migrate(self) -> None:
        sql = self.migration_path.read_text(encoding="utf-8")
        with self.engine.begin() as connection:
            if self.engine.dialect.name == "sqlite":
                connection.exec_driver_sql("PRAGMA foreign_keys = ON")
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    connection.exec_driver_sql(statement)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        self.engine.dispose()

