from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]

    def as_message_item(self) -> dict[str, Any]:
        import json

        return {
            "id": self.call_id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(
                    self.arguments,
                    ensure_ascii=False,
                ),
            },
        }


@dataclass(frozen=True)
class LLMResponse:
    content: str | None
    tool_calls: tuple[ToolCall, ...] = ()
    finish_reason: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class ToolCallRecord:
    step: int
    call_id: str
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    duration_ms: int


@dataclass
class AgentResult:
    status: Literal["completed", "failed", "max_steps"]
    content: str
    trace: list[ToolCallRecord] = field(default_factory=list)
    steps: int = 0
    error: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

