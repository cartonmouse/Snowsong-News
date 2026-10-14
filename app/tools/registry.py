from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.tools.base import ToolDefinition, ToolRegistry
from app.tools.filesystem import FileTools, WorkspaceGuard
from app.tools.shell import BashTool


REQUIRED_TOOL_NAMES = (
    "list_dir",
    "read_file",
    "search_content",
    "write_file",
    "bash",
)


def build_default_registry(
    workspace_root: str | Path | None = None,
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
    return registry

