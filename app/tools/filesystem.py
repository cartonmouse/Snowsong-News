from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.tools.base import ToolError


@dataclass(frozen=True)
class WorkspaceGuard:
    root: Path

    @classmethod
    def from_root(cls, root: str | Path) -> WorkspaceGuard:
        resolved = Path(root).expanduser().resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return cls(resolved)

    def resolve(self, path: str) -> Path:
        if not path:
            raise ToolError("path must not be empty")

        candidate = Path(path)
        resolved = (
            candidate if candidate.is_absolute() else self.root / candidate
        ).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ToolError("path is outside the tool workspace") from exc
        return resolved

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()


class FileTools:
    def __init__(
        self,
        guard: WorkspaceGuard,
        *,
        max_read_chars: int = 20_000,
        max_search_results: int = 50,
    ) -> None:
        self.guard = guard
        self.max_read_chars = max_read_chars
        self.max_search_results = max_search_results

    def list_dir(self, path: str = ".") -> dict[str, Any]:
        target = self.guard.resolve(path)
        if not target.exists():
            raise ToolError(f"directory does not exist: {path}")
        if not target.is_dir():
            raise ToolError(f"path is not a directory: {path}")

        entries = []
        for entry in sorted(target.iterdir(), key=lambda item: item.name.lower()):
            item_type = "directory" if entry.is_dir() else "file"
            size = entry.stat().st_size if entry.is_file() else None
            entries.append(
                {
                    "name": entry.name,
                    "type": item_type,
                    "size": size,
                }
            )
        return {
            "ok": True,
            "path": self.guard.relative(target) or ".",
            "entries": entries,
        }

    def read_file(self, path: str) -> dict[str, Any]:
        target = self.guard.resolve(path)
        if not target.exists():
            raise ToolError(f"file does not exist: {path}")
        if not target.is_file():
            raise ToolError(f"path is not a file: {path}")

        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ToolError("file is not valid UTF-8 text") from exc

        truncated = len(content) > self.max_read_chars
        if truncated:
            content = content[: self.max_read_chars]
        return {
            "ok": True,
            "path": self.guard.relative(target),
            "content": content,
            "truncated": truncated,
        }

    def search_content(
        self,
        keyword: str,
        dir: str = ".",
    ) -> dict[str, Any]:
        if not keyword:
            raise ToolError("keyword must not be empty")

        target = self.guard.resolve(dir)
        if not target.exists():
            raise ToolError(f"directory does not exist: {dir}")
        if not target.is_dir():
            raise ToolError(f"path is not a directory: {dir}")

        matches: list[dict[str, Any]] = []
        for candidate in sorted(target.rglob("*")):
            if not candidate.is_file():
                continue
            try:
                text = candidate.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if keyword.casefold() in line.casefold():
                    matches.append(
                        {
                            "path": self.guard.relative(candidate),
                            "line": line_number,
                            "text": line[:500],
                        }
                    )
                    if len(matches) >= self.max_search_results:
                        return {
                            "ok": True,
                            "keyword": keyword,
                            "matches": matches,
                            "truncated": True,
                        }
        return {
            "ok": True,
            "keyword": keyword,
            "matches": matches,
            "truncated": False,
        }

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        target = self.guard.resolve(path)
        if target.exists() and target.is_dir():
            raise ToolError(f"path is a directory: {path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise ToolError(f"could not write file: {path}") from exc
        return {
            "ok": True,
            "path": self.guard.relative(target),
            "characters": len(content),
        }

