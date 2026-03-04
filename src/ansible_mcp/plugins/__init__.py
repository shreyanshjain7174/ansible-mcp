from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ansible_mcp.context import WorkspaceContext
from ansible_mcp.token_budget import TokenBudget


@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    docs_uri: str | None = None


@dataclass(slots=True)
class ToolResult:
    status: str
    payload: dict[str, Any]


def require_non_empty(value: Any, field_name: str) -> str:
    normalized = "" if value is None else str(value)
    stripped = normalized.strip()
    if not stripped:
        raise ValueError(f"{field_name} is required")
    return stripped


def resolve_workspace_path(workspace_root: Path, candidate: str) -> Path:
    root = workspace_root.resolve()
    candidate_path = Path(candidate)
    if not candidate_path.is_absolute():
        candidate_path = root / candidate_path

    resolved = candidate_path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path must be within workspace root") from exc

    return resolved


async def exec_command(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
            env=merged_env,
        )
    except FileNotFoundError:
        return {
            "status": "failed",
            "command": argv,
            "exit_code": None,
            "stdout": "",
            "stderr": f"Command not found: {argv[0]}",
        }

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
    except TimeoutError:
        process.kill()
        await process.wait()
        return {
            "status": "failed",
            "command": argv,
            "exit_code": None,
            "stdout": "",
            "stderr": f"Timed out after {timeout_seconds} seconds",
        }

    exit_code = process.returncode
    return {
        "status": "success" if exit_code == 0 else "failed",
        "command": argv,
        "exit_code": exit_code,
        "stdout": stdout.decode("utf-8", errors="replace").strip(),
        "stderr": stderr.decode("utf-8", errors="replace").strip(),
    }


class AnsibleMCPPlugin(ABC):
    def __init__(self, workspace: WorkspaceContext, token_budget: TokenBudget) -> None:
        self.workspace = workspace
        self.token_budget = token_budget

    @classmethod
    @abstractmethod
    def tool_specs(cls) -> list[ToolSpec]:
        raise NotImplementedError

    @classmethod
    def should_load(cls, workspace: WorkspaceContext) -> bool:
        return True

    @abstractmethod
    async def handle_tool_call(self, name: str, args: dict[str, Any]) -> ToolResult:
        raise NotImplementedError
