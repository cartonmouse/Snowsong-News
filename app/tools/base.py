from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


ToolHandler = Callable[..., dict[str, Any]]


class ToolError(RuntimeError):
    """An expected, user-visible tool failure."""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def invoke(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        try:
            result = self.handler(**dict(arguments))
        except ToolError as exc:
            return {"ok": False, "error": str(exc)}
        except TypeError as exc:
            return {"ok": False, "error": f"invalid arguments: {exc}"}
        except Exception as exc:
            return {"ok": False, "error": f"tool execution failed: {exc}"}

        if isinstance(result, dict):
            return result
        return {"ok": True, "result": result}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolError(f"unknown tool: {name}") from exc

    def invoke(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        return self.get(name).invoke(arguments)

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

