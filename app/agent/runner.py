from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from app.agent.models import AgentResult, LLMResponse, ToolCallRecord
from app.agent.provider import LLMProvider
from app.tools.base import ToolError, ToolRegistry


DEFAULT_SYSTEM_PROMPT = (
    "You are a news assistant Agent. Use the available tools when needed. "
    "Choose the next tool based on the current task and tool results. "
    "Do not assume a fixed tool order. Stop and provide the final answer "
    "when the task is complete."
)


class AgentRunner:
    def __init__(
        self,
        provider: LLMProvider,
        registry: ToolRegistry,
        *,
        max_steps: int = 8,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.provider = provider
        self.registry = registry
        self.max_steps = max_steps
        self.system_prompt = system_prompt

    def _assistant_message(self, response: LLMResponse) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": [
                call.as_message_item() for call in response.tool_calls
            ],
        }

    @staticmethod
    def _tool_message(
        call_id: str,
        name: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "name": name,
            "content": json.dumps(result, ensure_ascii=False, default=str),
        }

    def run(self, user_message: str) -> AgentResult:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        trace: list[ToolCallRecord] = []
        last_content = ""

        for step in range(1, self.max_steps + 1):
            try:
                response = self.provider.complete(
                    messages,
                    self.registry.schemas(),
                )
            except Exception as exc:
                return AgentResult(
                    status="failed",
                    content=last_content,
                    trace=trace,
                    steps=step - 1,
                    error=str(exc),
                    messages=messages,
                )

            last_content = response.content or last_content
            if not response.tool_calls:
                return AgentResult(
                    status="completed",
                    content=response.content or "",
                    trace=trace,
                    steps=step,
                    messages=messages,
                )

            messages.append(self._assistant_message(response))
            for call in response.tool_calls:
                started = perf_counter()
                try:
                    result = self.registry.invoke(call.name, call.arguments)
                except ToolError as exc:
                    result = {"ok": False, "error": str(exc)}
                except Exception as exc:
                    result = {"ok": False, "error": f"tool failure: {exc}"}
                duration_ms = round((perf_counter() - started) * 1000)
                trace.append(
                    ToolCallRecord(
                        step=step,
                        call_id=call.call_id,
                        name=call.name,
                        arguments=call.arguments,
                        result=result,
                        duration_ms=duration_ms,
                    )
                )
                messages.append(
                    self._tool_message(call.call_id, call.name, result)
                )

        return AgentResult(
            status="max_steps",
            content=last_content,
            trace=trace,
            steps=self.max_steps,
            error=f"agent reached max_steps={self.max_steps}",
            messages=messages,
        )

