from __future__ import annotations

import json
from typing import Any, Protocol, Sequence

import httpx

from app.agent.models import LLMResponse, ToolCall


class ProviderError(RuntimeError):
    """Raised when an LLM provider response cannot be used."""


class LLMProvider(Protocol):
    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
    ) -> LLMResponse:
        ...


def _parse_arguments(raw_arguments: Any) -> dict[str, Any]:
    if raw_arguments is None or raw_arguments == "":
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not isinstance(raw_arguments, str):
        raise ProviderError("tool arguments must be an object or JSON string")
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ProviderError("tool arguments are not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ProviderError("tool arguments JSON must decode to an object")
    return parsed


def parse_openai_response(payload: dict[str, Any]) -> LLMResponse:
    try:
        choice = payload["choices"][0]
        message = choice["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("provider response has no usable choice") from exc

    parsed_tool_calls: list[ToolCall] = []
    for index, raw_call in enumerate(message.get("tool_calls") or []):
        function = raw_call.get("function") or {}
        name = function.get("name")
        if not name:
            raise ProviderError("tool call has no function name")
        parsed_tool_calls.append(
            ToolCall(
                call_id=raw_call.get("id") or f"call-{index + 1}",
                name=name,
                arguments=_parse_arguments(function.get("arguments")),
            )
        )

    return LLMResponse(
        content=message.get("content"),
        tool_calls=tuple(parsed_tool_calls),
        finish_reason=choice.get("finish_reason"),
        raw=payload,
    )


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30,
        client: httpx.Client | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url must not be empty")
        if not api_key:
            raise ValueError("api_key must not be empty")
        if not model:
            raise ValueError("model must not be empty")

        self.model = model
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout_seconds,
        )

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
    ) -> LLMResponse:
        try:
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": list(messages),
                    "tools": list(tools),
                    "tool_choice": "auto",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"LLM request failed: {exc}") from exc
        return parse_openai_response(payload)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

