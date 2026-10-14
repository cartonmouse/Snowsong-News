from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.tools.base import ToolDefinition, ToolRegistry
from app.tools.business import NewsBusinessTools
from app.tools.filesystem import FileTools, WorkspaceGuard
from app.tools.shell import BashTool


REQUIRED_TOOL_NAMES = (
    "list_dir",
    "read_file",
    "search_content",
    "write_file",
    "bash",
)

BUSINESS_TOOL_NAMES = (
    "get_user_preferences",
    "fetch_news",
    "save_brief",
    "deliver_brief",
)


def build_default_registry(
    workspace_root: str | Path | None = None,
    *,
    business_tools: NewsBusinessTools | None = None,
) -> ToolRegistry:
    settings = get_settings()
    root = Path(workspace_root or settings.tool_workspace_root)
    if not root.is_absolute():
        root = Path.cwd() / root

    guard = WorkspaceGuard.from_root(root)
    file_tools = FileTools(guard)
    bash_tool = BashTool(
        guard.root,
        timeout_seconds=settings.bash_timeout_seconds,
        max_output_chars=settings.tool_output_max_chars,
    )

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="list_dir",
            description="List files and directories inside the tool workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path."}
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            handler=file_tools.list_dir,
        )
    )
    registry.register(
        ToolDefinition(
            name="read_file",
            description="Read a UTF-8 text file inside the tool workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path."}
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            handler=file_tools.read_file,
        )
    )
    registry.register(
        ToolDefinition(
            name="search_content",
            description="Search a keyword in UTF-8 text files inside a directory.",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "dir": {"type": "string", "default": "."},
                },
                "required": ["keyword"],
                "additionalProperties": False,
            },
            handler=file_tools.search_content,
        )
    )
    registry.register(
        ToolDefinition(
            name="write_file",
            description="Write UTF-8 text to a file inside the tool workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            handler=file_tools.write_file,
        )
    )
    registry.register(
        ToolDefinition(
            name="bash",
            description="Run a command allowed by the shell safety policy.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            handler=bash_tool.run,
        )
    )
    if business_tools is not None:
        registry.register(
            ToolDefinition(
                name="get_user_preferences",
                description="Read a user's saved news subscription preferences.",
                parameters={
                    "type": "object",
                    "properties": {"user_id": {"type": "integer"}},
                    "required": ["user_id"],
                    "additionalProperties": False,
                },
                handler=business_tools.get_user_preferences,
            )
        )
        registry.register(
            ToolDefinition(
                name="fetch_news",
                description="Fetch current news and filter it by a query.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "default": ""},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "additionalProperties": False,
                },
                handler=business_tools.fetch_news,
            )
        )
        registry.register(
            ToolDefinition(
                name="save_brief",
                description="Save a completed news brief for a user.",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"},
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "source_count": {"type": "integer", "default": 0},
                    },
                    "required": ["user_id", "title", "content"],
                    "additionalProperties": False,
                },
                handler=business_tools.save_brief,
            )
        )
        registry.register(
            ToolDefinition(
                name="deliver_brief",
                description="Deliver a completed brief through a configured channel.",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"},
                        "content": {"type": "string"},
                        "channel": {
                            "type": "string",
                            "default": "history",
                        },
                    },
                    "required": ["user_id", "content"],
                    "additionalProperties": False,
                },
                handler=business_tools.deliver_brief,
            )
        )
    return registry

