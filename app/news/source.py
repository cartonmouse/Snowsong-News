from __future__ import annotations

import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        self.last_errors: dict[str, str] = {}
        self.last_successful_feeds: tuple[str, ...] = ()

    def _fetch_one(
        self,
        index: int,
        feed: str,
    ) -> tuple[int, str, list[NewsItem], str | None]:
        try:
            response = httpx.get(
                feed,
                timeout=self.timeout_seconds,
                follow_redirects=True,
                headers={"User-Agent": "news-agent/1.0 RSS reader"},
            )
            response.raise_for_status()
            return index, feed, parse_feed(response.content, source=feed), None
        except (httpx.HTTPError, NewsSourceError) as exc:
            return index, feed, [], str(exc)

    def fetch(
        self,
        feeds: Sequence[str],
        limit: int = 20,
    ) -> list[NewsItem]:
        unique_feeds = tuple(dict.fromkeys(feed.strip() for feed in feeds if feed.strip()))
        if not unique_feeds:
            raise NewsSourceError("no RSS feeds configured")
        safe_limit = max(0, limit)
        self.last_errors = {}
        self.last_successful_feeds = ()
        if safe_limit == 0:
            return []

        results: list[tuple[int, str, list[NewsItem], str | None]] = []
        with ThreadPoolExecutor(max_workers=min(8, len(unique_feeds))) as executor:
            futures = [
                executor.submit(self._fetch_one, index, feed)
                for index, feed in enumerate(unique_feeds)
            ]
            for future in as_completed(futures):
                results.append(future.result())

        results.sort(key=lambda result: result[0])
        feed_items: list[list[NewsItem]] = []
        successful_feeds: list[str] = []
        for _, feed, items, error in results:
            if error:
                self.last_errors[feed] = error
            else:
                successful_feeds.append(feed)
                feed_items.append(items)
        self.last_successful_feeds = tuple(successful_feeds)

        if not successful_feeds:
            details = "; ".join(
                f"{feed}: {error}" for feed, error in self.last_errors.items()
            )
            raise NewsSourceError(f"all RSS feeds failed: {details}")

        # Round-robin the feeds so the next filtering step sees more than one source.
        items: list[NewsItem] = []
        while len(items) < safe_limit:
            added = False
            for current_feed_items in feed_items:
                if current_feed_items:
                    items.append(current_feed_items.pop(0))
                    added = True
                    if len(items) >= safe_limit:
                        break
            if not added:
                break
        return items

