from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from app.agent.models import LLMResponse, ToolCall
from app.agent.runner import AgentRunner
from app.tools.registry import build_default_registry


class FakeProvider:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[list[dict[str, Any]], Sequence[dict[str, Any]]]] = []

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
    ) -> LLMResponse:
        self.calls.append((list(messages), tools))
        return self.responses.pop(0)


def test_runner_follows_provider_selected_tool_order(tmp_path: Path) -> None:
    provider = FakeProvider(
        [
            LLMResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        "call-write",
                        "write_file",
                        {"path": "brief.txt", "content": "first draft"},
                    ),
                ),
            ),
            LLMResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        "call-read",
                        "read_file",
                        {"path": "brief.txt"},
                    ),
                ),
            ),
            LLMResponse(content="The brief is ready."),
        ]
    )
    runner = AgentRunner(
        provider,
        build_default_registry(tmp_path),
        max_steps=4,
    )

    result = runner.run("Prepare the brief.")

    assert result.status == "completed"
    assert result.content == "The brief is ready."
    assert [item.name for item in result.trace] == [
        "write_file",
        "read_file",
    ]
    assert (tmp_path / "brief.txt").read_text(encoding="utf-8") == "first draft"
    assert len(provider.calls) == 3


def test_runner_returns_tool_errors_to_the_provider(tmp_path: Path) -> None:
    provider = FakeProvider(
        [
            LLMResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        "call-missing",
                        "read_file",
                        {"path": "missing.txt"},
                    ),
                ),
            ),
            LLMResponse(content="I could not find that file."),
        ]
    )
    runner = AgentRunner(provider, build_default_registry(tmp_path))

    result = runner.run("Read the file.")

    assert result.status == "completed"
    assert result.trace[0].result["ok"] is False
    assert "does not exist" in result.trace[0].result["error"]
    tool_message = provider.calls[1][0][-1]
    assert tool_message["role"] == "tool"
    assert "does not exist" in tool_message["content"]


def test_runner_stops_at_max_steps(tmp_path: Path) -> None:
    provider = FakeProvider(
        [
            LLMResponse(
                content="still working",
                tool_calls=(
                    ToolCall(
                        f"call-{index}",
                        "list_dir",
                        {"path": "."},
                    ),
                ),
            )
            for index in range(3)
        ]
    )
    runner = AgentRunner(
        provider,
        build_default_registry(tmp_path),
        max_steps=2,
    )

    result = runner.run("Keep working.")

    assert result.status == "max_steps"
    assert result.steps == 2
    assert len(result.trace) == 2

