from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from app.tools.base import ToolError


class BashTool:
    allowed_executables = {
        "python",
        "python3",
        "pytest",
        "uvicorn",
        "git",
        "echo",
        "dir",
        "type",
        "where",
    }
    blocked_patterns = (
        r"\brm\b",
        r"\bdel\b",
        r"\brmdir\b",
        r"\bremove-item\b",
        r"\bformat\b",
        r"\bshutdown\b",
        r"\bgit\s+(reset|checkout|clean)\b",
        r"\bpip\s+(install|uninstall)\b",
        r"\b(curl|wget|invoke-webrequest)\b",
    )

    def __init__(
        self,
        working_directory: str | Path,
        *,
        timeout_seconds: int = 10,
        max_output_chars: int = 4_000,
    ) -> None:
        self.working_directory = Path(working_directory).resolve()
        self.working_directory.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

    def _validate(self, command: str) -> None:
        if not command or not command.strip():
            raise ToolError("command must not be empty")
        if "\x00" in command or any(char in command for char in "\r\n;&|<>"):
            raise ToolError("shell operators and multiline commands are not allowed")

        lowered = command.casefold()
        if any(re.search(pattern, lowered) for pattern in self.blocked_patterns):
            raise ToolError("command is blocked by the safety policy")

        try:
            executable = Path(shlex.split(command, posix=False)[0]).name.casefold()
        except (IndexError, ValueError) as exc:
            raise ToolError("could not parse command") from exc
        if executable not in self.allowed_executables:
            raise ToolError(f"executable is not allowed: {executable}")

    def run(self, command: str) -> dict[str, Any]:
        self._validate(command)
        try:
            completed = subprocess.run(
                command,
                cwd=self.working_directory,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolError(
                f"command timed out after {self.timeout_seconds} seconds"
            ) from exc
        except OSError as exc:
            raise ToolError(f"could not execute command: {exc}") from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        combined_length = len(stdout) + len(stderr)
        if len(stdout) > self.max_output_chars:
            stdout = stdout[: self.max_output_chars]
        if len(stderr) > self.max_output_chars:
            stderr = stderr[: self.max_output_chars]
        return {
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "truncated": combined_length > self.max_output_chars * 2,
        }

