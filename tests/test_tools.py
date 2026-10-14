from pathlib import Path

from app.tools.registry import REQUIRED_TOOL_NAMES, build_default_registry


def test_registry_contains_required_tools(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path)

    assert registry.names == REQUIRED_TOOL_NAMES
    assert len(registry.schemas()) == 5


def test_file_tools_write_read_list_and_search(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path)

    written = registry.invoke(
        "write_file",
        {"path": "notes/news.txt", "content": "AI agents are useful.\n"},
    )
    assert written["ok"] is True

    read = registry.invoke("read_file", {"path": "notes/news.txt"})
    assert read["ok"] is True
    assert "AI agents" in read["content"]

    listing = registry.invoke("list_dir", {"path": "notes"})
    assert listing["ok"] is True
    assert listing["entries"][0]["name"] == "news.txt"

    matches = registry.invoke(
        "search_content",
        {"keyword": "agents", "dir": "notes"},
    )
    assert matches["ok"] is True
    assert matches["matches"][0]["path"] == "notes/news.txt"


def test_file_tools_reject_workspace_escape(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path)

    result = registry.invoke("read_file", {"path": "../outside.txt"})

    assert result["ok"] is False
    assert "outside" in result["error"]


def test_bash_tool_blocks_destructive_commands(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path)

    result = registry.invoke("bash", {"command": "git reset --hard"})

    assert result["ok"] is False
    assert "blocked" in result["error"]


def test_bash_tool_runs_allowed_command(tmp_path: Path) -> None:
    registry = build_default_registry(tmp_path)

    result = registry.invoke("bash", {"command": "python --version"})

    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert "Python" in result["stdout"]

