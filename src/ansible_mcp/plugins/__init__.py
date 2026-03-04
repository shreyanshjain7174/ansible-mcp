from __future__ import annotations

import asyncio
import os
import shutil
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
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


@dataclass(slots=True)
class ExecutableResolution:
    requested: str
    resolved: str | None
    source: str
    env_var: str
    checked: list[str]
    warning: str | None = None


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


_COMMON_VENV_NAMES = (
    "ansible-dev",
    ".venv",
    "venv",
    "virtualenv",
    ".virtualenv",
    "env",
    ".env",
)


def executable_env_var_name(executable: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in executable.upper())
    return f"ANSIBLE_MCP_{normalized}_EXECUTABLE"


def _is_executable_file(candidate: Path) -> bool:
    return candidate.is_file() and os.access(candidate, os.X_OK)


def _workspace_search_roots(workspace_root: Path) -> list[Path]:
    resolved_root = workspace_root.resolve()
    roots = [resolved_root]
    roots.extend(resolved_root.parents)
    return roots


def resolve_executable(
    executable: str,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> ExecutableResolution:
    checked: list[str] = []
    env_var = executable_env_var_name(executable)
    warning: str | None = None

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    def _append_checked(path: Path) -> None:
        path_str = str(path)
        if path_str not in checked:
            checked.append(path_str)

    requested_path = Path(executable)
    has_path_hint = requested_path.is_absolute() or requested_path.parent != Path(".")
    if has_path_hint:
        candidate = requested_path.expanduser()
        if not candidate.is_absolute():
            candidate = (cwd / candidate).resolve()
        _append_checked(candidate)
        if _is_executable_file(candidate):
            return ExecutableResolution(
                requested=executable,
                resolved=str(candidate),
                source="explicit-path",
                env_var=env_var,
                checked=checked,
            )
        warning = f"Explicit executable path is not executable: {candidate}"
        return ExecutableResolution(
            requested=executable,
            resolved=None,
            source="explicit-path",
            env_var=env_var,
            checked=checked,
            warning=warning,
        )

    override = merged_env.get(env_var)
    if override:
        override_path = Path(override).expanduser()
        if not override_path.is_absolute():
            override_path = (cwd / override_path).resolve()
        _append_checked(override_path)
        if _is_executable_file(override_path):
            return ExecutableResolution(
                requested=executable,
                resolved=str(override_path),
                source="env-override",
                env_var=env_var,
                checked=checked,
            )
        warning = f"{env_var} points to a non-executable path: {override_path}"

    python_bin_candidate = Path(sys.executable).resolve().parent / executable
    _append_checked(python_bin_candidate)
    if _is_executable_file(python_bin_candidate):
        return ExecutableResolution(
            requested=executable,
            resolved=str(python_bin_candidate),
            source="python-bin",
            env_var=env_var,
            checked=checked,
            warning=warning,
        )

    virtual_env = merged_env.get("VIRTUAL_ENV")
    if virtual_env:
        virtual_env_candidate = Path(virtual_env).expanduser() / "bin" / executable
        _append_checked(virtual_env_candidate)
        if _is_executable_file(virtual_env_candidate):
            return ExecutableResolution(
                requested=executable,
                resolved=str(virtual_env_candidate),
                source="virtual-env",
                env_var=env_var,
                checked=checked,
                warning=warning,
            )

    for search_root in _workspace_search_roots(cwd):
        for venv_name in _COMMON_VENV_NAMES:
            candidate = search_root / venv_name / "bin" / executable
            _append_checked(candidate)
            if _is_executable_file(candidate):
                return ExecutableResolution(
                    requested=executable,
                    resolved=str(candidate),
                    source="workspace-venv",
                    env_var=env_var,
                    checked=checked,
                    warning=warning,
                )

    path_lookup = shutil.which(executable, path=merged_env.get("PATH"))
    if path_lookup:
        path_candidate = Path(path_lookup).expanduser().resolve()
        _append_checked(path_candidate)
        if _is_executable_file(path_candidate):
            return ExecutableResolution(
                requested=executable,
                resolved=str(path_candidate),
                source="path",
                env_var=env_var,
                checked=checked,
                warning=warning,
            )

    return ExecutableResolution(
        requested=executable,
        resolved=None,
        source="not-found",
        env_var=env_var,
        checked=checked,
        warning=warning,
    )


async def exec_command(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    if not argv:
        return {
            "status": "failed",
            "command": [],
            "resolved_command": [],
            "exit_code": None,
            "stdout": "",
            "stderr": "No command provided",
            "executable_resolution": None,
        }

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    resolution = resolve_executable(argv[0], cwd=cwd, env=merged_env)
    resolution_dict = asdict(resolution)

    if resolution.resolved is None:
        details = f"Checked: {', '.join(resolution.checked)}"
        if resolution.warning:
            details = f"{resolution.warning}. {details}"
        return {
            "status": "failed",
            "command": argv,
            "resolved_command": None,
            "exit_code": None,
            "stdout": "",
            "stderr": f"Command not found: {argv[0]}. {details}",
            "executable_resolution": resolution_dict,
        }

    resolved_argv = [resolution.resolved, *argv[1:]]

    try:
        process = await asyncio.create_subprocess_exec(
            *resolved_argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
            env=merged_env,
        )
    except FileNotFoundError:
        return {
            "status": "failed",
            "command": argv,
            "resolved_command": resolved_argv,
            "exit_code": None,
            "stdout": "",
            "stderr": f"Command not found: {argv[0]}",
            "executable_resolution": resolution_dict,
        }

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
    except TimeoutError:
        process.kill()
        await process.wait()
        return {
            "status": "failed",
            "command": argv,
            "resolved_command": resolved_argv,
            "exit_code": None,
            "stdout": "",
            "stderr": f"Timed out after {timeout_seconds} seconds",
            "executable_resolution": resolution_dict,
        }

    exit_code = process.returncode
    return {
        "status": "success" if exit_code == 0 else "failed",
        "command": argv,
        "resolved_command": resolved_argv,
        "exit_code": exit_code,
        "stdout": stdout.decode("utf-8", errors="replace").strip(),
        "stderr": stderr.decode("utf-8", errors="replace").strip(),
        "executable_resolution": resolution_dict,
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
