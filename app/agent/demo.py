from __future__ import annotations

import json
from typing import Any, Sequence

from app.agent.models import LLMResponse, ToolCall


class DemoNewsProvider:
    """A deterministic local provider for demos without an API key."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.brief_content = ""

    @staticmethod
    def _last_tool_message(
        messages: Sequence[dict[str, Any]],
    ) -> tuple[str | None, dict[str, Any]]:
        for message in reversed(messages):
            if message.get("role") != "tool":
                continue
            try:
                payload = json.loads(message.get("content", "{}"))
            except json.JSONDecodeError:
                payload = {}
            return message.get("name"), payload
        return None, {}

    @staticmethod
    def _build_brief(
        items: list[dict[str, Any]],
        *,
        source_mode: str = "mock",
        error: str | None = None,
    ) -> str:
        source_label = "RSS" if source_mode.casefold() == "rss" else "Mock"
        lines = [
            "# 今日 AI 新闻简报",
            "",
            f"当前使用 {source_label} 新闻源生成内容。",
            "",
        ]
        if error:
            lines.append(f"新闻源获取失败：{error}")
        elif not items:
            lines.append("今天没有匹配到新闻。")
        else:
            for index, item in enumerate(items, start=1):
                lines.extend(
                    [
                        f"## {index}. {item.get('title', '未命名新闻')}",
                        f"- 来源：{item.get('source', 'unknown')}",
                        f"- 摘要：{item.get('summary', '')}",
                        f"- 链接：{item.get('url', '')}",
                        "",
                    ]
                )
        return "\n".join(lines).strip()

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
    ) -> LLMResponse:
        last_name, payload = self._last_tool_message(messages)

        if last_name is None:
            return LLMResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        "demo-preferences",
                        "get_user_preferences",
                        {"user_id": self.user_id},
                    ),
                ),
            )

        if last_name == "get_user_preferences":
            preferences = payload.get("preferences", {})
            query = ", ".join(
                preferences.get("keywords", [])
                + preferences.get("topics", [])
            )
            return LLMResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        "demo-news",
                        "fetch_news",
                        {"query": query, "limit": 10},
                    ),
                ),
            )

        if last_name == "fetch_news":
            items = payload.get("items", [])
            self.brief_content = self._build_brief(
                items,
                source_mode=payload.get("source_mode", "mock"),
                error=(
                    payload.get("error")
                    if not payload.get("ok", True)
                    else None
                ),
            )
            if not payload.get("ok", True):
                return LLMResponse(content=self.brief_content)
            return LLMResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        "demo-save",
                        "save_brief",
                        {
                            "user_id": self.user_id,
                            "title": "今日 AI 新闻简报",
                            "content": self.brief_content,
                            "source_count": len(items),
                        },
                    ),
                ),
            )

        if last_name == "save_brief":
            return LLMResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        "demo-deliver",
                        "deliver_brief",
                        {
                            "user_id": self.user_id,
                            "content": self.brief_content,
                            "channel": "history",
                        },
                    ),
                ),
            )

        if last_name == "deliver_brief":
            return LLMResponse(
                content=(
                    f"{self.brief_content}\n\n"
                    "本次简报已保存到历史记录。"
                ),
            )

        return LLMResponse(content="Agent 已完成本次任务。")

