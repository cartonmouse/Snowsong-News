from __future__ import annotations

import html
import re
from typing import Protocol, Sequence
from xml.etree import ElementTree

import httpx

from app.news.models import NewsItem


class NewsSourceError(RuntimeError):
    pass


class NewsSource(Protocol):
    def fetch(self, limit: int = 20) -> list[NewsItem]:
        ...


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(without_tags).split())


def _find_text(element: ElementTree.Element, name: str) -> str:
    return _clean_text(element.findtext(name))


def parse_feed(payload: bytes, source: str) -> list[NewsItem]:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise NewsSourceError("RSS payload is not valid XML") from exc

    items: list[NewsItem] = []
    for item in root.findall(".//item"):
        title = _find_text(item, "title")
        url = _find_text(item, "link")
        summary = _find_text(item, "description")
        published_at = _find_text(item, "pubDate") or None
        if title:
            items.append(
                NewsItem(
                    title=title,
                    url=url,
                    summary=summary,
                    source=source,
                    published_at=published_at,
                )
            )

    atom_namespace = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f".//{atom_namespace}entry"):
        title = _find_text(entry, f"{atom_namespace}title")
        summary = _find_text(entry, f"{atom_namespace}summary")
        if not summary:
            summary = _find_text(entry, f"{atom_namespace}content")
        published_at = (
            _find_text(entry, f"{atom_namespace}published")
            or _find_text(entry, f"{atom_namespace}updated")
            or None
        )
        link = ""
        for link_element in entry.findall(f"{atom_namespace}link"):
            if link_element.attrib.get("rel", "alternate") == "alternate":
                link = link_element.attrib.get("href", "")
                break
        if title:
            items.append(
                NewsItem(
                    title=title,
                    url=link,
                    summary=summary,
                    source=source,
                    published_at=published_at,
                )
            )
    return items


class MockNewsSource:
    def __init__(self, items: Sequence[NewsItem] | None = None) -> None:
        self.items = list(items or self._default_items())

    @staticmethod
    def _default_items() -> list[NewsItem]:
        return [
            NewsItem(
                title="New tool-use benchmark compares AI coding agents",
                url="https://example.com/mock/tool-use-benchmark",
                summary="The benchmark evaluates planning, tool use, and recovery from failures.",
                source="mock",
                published_at="2026-10-14",
            ),
            NewsItem(
                title="Open models improve structured function calling",
                url="https://example.com/mock/function-calling",
                summary="A new model release focuses on reliable JSON and function calling.",
                source="mock",
                published_at="2026-10-14",
            ),
            NewsItem(
                title="Researchers publish a practical guide to AI news evaluation",
                url="https://example.com/mock/news-evaluation",
                summary="The guide discusses source quality, freshness, and duplicate detection.",
                source="mock",
                published_at="2026-10-14",
            ),
        ]

    def fetch(self, limit: int = 20) -> list[NewsItem]:
        return self.items[: max(0, limit)]


class RssNewsSource:
    def __init__(self, timeout_seconds: float = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch(
        self,
        feeds: Sequence[str],
        limit: int = 20,
    ) -> list[NewsItem]:
        if not feeds:
            raise NewsSourceError("no RSS feeds configured")

        items: list[NewsItem] = []
        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                follow_redirects=True,
            ) as client:
                for feed in feeds:
                    response = client.get(feed)
                    response.raise_for_status()
                    items.extend(parse_feed(response.content, source=feed))
        except httpx.HTTPError as exc:
            raise NewsSourceError(f"RSS request failed: {exc}") from exc
        return items[: max(0, limit)]

