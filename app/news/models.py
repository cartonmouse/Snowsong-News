from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    summary: str
    source: str
    published_at: str | None = None

    @property
    def searchable_text(self) -> str:
        return f"{self.title} {self.summary} {self.source}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

