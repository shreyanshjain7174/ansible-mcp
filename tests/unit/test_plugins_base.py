from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ansible_mcp.plugins import (
    ExecutableResolution,
    ToolResult,
    ToolSpec,
    exec_command,
    executable_env_var_name,
    require_non_empty,
    resolve_executable,
    resolve_workspace_path,
)

# ---------------------------------------------------------------------------
# ToolSpec
# ---------------------------------------------------------------------------


class TestToolSpec:
    def test_all_fields(self) -> None:
        spec = ToolSpec(
            name="my_tool",
            description="A tool",
            input_schema={"type": "object"},
            docs_uri="ansible://docs/my_tool",
        )
        assert spec.name == "my_tool"
        assert spec.description == "A tool"
        assert spec.input_schema == {"type": "object"}
        assert spec.docs_uri == "ansible://docs/my_tool"

    def test_default_docs_uri_is_none(self) -> None:
        spec = ToolSpec(name="t", description="d", input_schema={})
        assert spec.docs_uri is None


# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------


class TestToolResult:
    def test_success_result(self) -> None:
        result = ToolResult(status="success", payload={"data": 1})
        assert result.status == "success"
        assert result.payload == {"data": 1}

    def test_failed_result(self) -> None:
        result = ToolResult(status="failed", payload={"error": "bad"})
        assert result.status == "failed"
        assert result.payload["error"] == "bad"


# ---------------------------------------------------------------------------
# require_non_empty
# ---------------------------------------------------------------------------


class TestRequireNonEmpty:
    def test_valid_string(self) -> None:
        assert require_non_empty("hello", "field") == "hello"

    def test_strips_whitespace(self) -> None:
        assert require_non_empty("  hello  ", "field") == "hello"

    def test_none_raises(self) -> None:
        with pytest.raises(ValueError, match="field is required"):
            require_non_empty(None, "field")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="x is required"):
            require_non_empty("", "x")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="y is required"):
            require_non_empty("   ", "y")


# ---------------------------------------------------------------------------
# resolve_workspace_path
# ---------------------------------------------------------------------------


class TestResolveWorkspacePath:
    def test_relative_path(self, tmp_path: Path) -> None:
        (tmp_path / "sub").mkdir()
        target = tmp_path / "sub" / "file.yml"
        target.touch()
        resolved = resolve_workspace_path(tmp_path, "sub/file.yml")
        assert resolved == target.resolve()

    def test_absolute_within_workspace(self, tmp_path: Path) -> None:
        target = tmp_path / "main.yml"
        target.touch()
        resolved = resolve_workspace_path(tmp_path, str(target))
        assert resolved == target.resolve()

    def test_traversal_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="within workspace root"):
            resolve_workspace_path(tmp_path, "../../../etc/passwd")

    def test_nonexistent_path_still_resolves(self, tmp_path: Path) -> None:
        resolved = resolve_workspace_path(tmp_path, "nonexistent.yml")
        assert resolved == (tmp_path / "nonexistent.yml").resolve()


# ---------------------------------------------------------------------------
# exec_command helpers
# ---------------------------------------------------------------------------


def _mock_process(
    stdout: bytes = b"",
    stderr: bytes = b"",
    returncode: int = 0,
) -> MagicMock:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    proc.returncode = returncode
    proc.kill = MagicMock()
    proc.wait = AsyncMock()
    return proc  # type: ignore[return-value]


def _make_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)


# ---------------------------------------------------------------------------
# exec_command
# ---------------------------------------------------------------------------


class TestExecCommand:
    async def test_success(self, tmp_path: Path) -> None:
        proc = _mock_process(stdout=b"hello", returncode=0)
        resolution = ExecutableResolution(
            requested="echo",
            resolved="/bin/echo",
            source="path",
            env_var="ANSIBLE_MCP_ECHO_EXECUTABLE",
            checked=["/bin/echo"],
        )
        with patch(
            "asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ), patch("ansible_mcp.plugins.resolve_executable", return_value=resolution):
            result = await exec_command(["echo", "hello"], cwd=tmp_path)
        assert result["status"] == "success"
        assert result["stdout"] == "hello"
        assert result["exit_code"] == 0
        assert result["resolved_command"] is not None
        assert result["executable_resolution"]["resolved"] is not None

    async def test_nonzero_exit(self, tmp_path: Path) -> None:
        proc = _mock_process(stderr=b"error occurred", returncode=2)
        resolution = ExecutableResolution(
            requested="fail",
            resolved="/bin/fail",
            source="path",
            env_var="ANSIBLE_MCP_FAIL_EXECUTABLE",
            checked=["/bin/fail"],
        )
        with patch(
            "asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ), patch("ansible_mcp.plugins.resolve_executable", return_value=resolution):
            result = await exec_command(["fail"], cwd=tmp_path)
        assert result["status"] == "failed"
        assert result["exit_code"] == 2
        assert result["stderr"] == "error occurred"

    async def test_command_not_found(self, tmp_path: Path) -> None:
        with patch(
            "asyncio.create_subprocess_exec",
            new=AsyncMock(side_effect=FileNotFoundError),
        ):
            result = await exec_command(["nonexistent"], cwd=tmp_path)
        assert result["status"] == "failed"
        assert result["exit_code"] is None
        assert "Command not found" in result["stderr"]

    async def test_timeout(self, tmp_path: Path) -> None:
        # Use plain MagicMock for communicate so that calling it does
        # NOT produce a coroutine — asyncio.wait_for is mocked to raise
        # before the return value is ever awaited.
        proc = MagicMock()
        proc.kill = MagicMock()
        proc.wait = AsyncMock()
        resolution = ExecutableResolution(
            requested="slow",
            resolved="/bin/slow",
            source="path",
            env_var="ANSIBLE_MCP_SLOW_EXECUTABLE",
            checked=["/bin/slow"],
        )
        with (
            patch(
                "asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=proc),
            ),
            patch(
                "asyncio.wait_for",
                new=AsyncMock(side_effect=TimeoutError),
            ),
            patch("ansible_mcp.plugins.resolve_executable", return_value=resolution),
        ):
            result = await exec_command(
                ["slow"], cwd=tmp_path, timeout_seconds=1
            )
        assert result["status"] == "failed"
        assert result["exit_code"] is None
        assert "Timed out" in result["stderr"]


# ---------------------------------------------------------------------------
# exec_command – env merging
# ---------------------------------------------------------------------------


class TestExecCommandEnv:
    async def test_passes_custom_env(self, tmp_path: Path) -> None:
        proc = _mock_process(stdout=b"ok")
        create_mock = AsyncMock(return_value=proc)
        resolution = ExecutableResolution(
            requested="cmd",
            resolved="/bin/cmd",
            source="path",
            env_var="ANSIBLE_MCP_CMD_EXECUTABLE",
            checked=["/bin/cmd"],
        )
        with patch("asyncio.create_subprocess_exec", new=create_mock), patch(
            "ansible_mcp.plugins.resolve_executable", return_value=resolution
        ):
            await exec_command(
                ["cmd"],
                cwd=tmp_path,
                env={"MY_VAR": "1"},
            )
        assert create_mock.call_args is not None
        passed_env: dict[str, str] = create_mock.call_args[1]["env"]
        assert passed_env["MY_VAR"] == "1"


# ---------------------------------------------------------------------------
# executable_env_var_name
# ---------------------------------------------------------------------------


class TestExecutableEnvVarName:
    def test_generates_expected_name(self) -> None:
        assert (
            executable_env_var_name("ansible-lint")
            == "ANSIBLE_MCP_ANSIBLE_LINT_EXECUTABLE"
        )


# ---------------------------------------------------------------------------
# resolve_executable
# ---------------------------------------------------------------------------


class TestResolveExecutable:
    def test_prefers_env_override(self, tmp_path: Path) -> None:
        override = tmp_path / "custom" / "ansible-lint"
        _make_executable(override)

        resolution = resolve_executable(
            "ansible-lint",
            cwd=tmp_path,
            env={"ANSIBLE_MCP_ANSIBLE_LINT_EXECUTABLE": str(override)},
        )

        assert resolution.resolved == str(override)
        assert resolution.source == "env-override"

    def test_prefers_workspace_venv_before_path(self, tmp_path: Path) -> None:
        workspace_exec = tmp_path / ".venv" / "bin" / "ansible-lint"
        path_dir = tmp_path / "pathbin"
        path_exec = path_dir / "ansible-lint"
        _make_executable(workspace_exec)
        _make_executable(path_exec)

        with patch("ansible_mcp.plugins.sys.executable", str(tmp_path / "python" / "python3")):
            resolution = resolve_executable(
                "ansible-lint",
                cwd=tmp_path,
                env={"PATH": str(path_dir), "VIRTUAL_ENV": ""},
            )

        assert resolution.resolved == str(workspace_exec)
        assert resolution.source == "workspace-venv"

    def test_falls_back_to_path(self, tmp_path: Path) -> None:
        path_dir = tmp_path / "pathbin"
        path_exec = path_dir / "ansible-lint"
        _make_executable(path_exec)

        with patch("ansible_mcp.plugins.sys.executable", str(tmp_path / "python" / "python3")):
            resolution = resolve_executable(
                "ansible-lint",
                cwd=tmp_path,
                env={"PATH": str(path_dir), "VIRTUAL_ENV": ""},
            )

        assert resolution.resolved == str(path_exec)
        assert resolution.source == "path"

    def test_not_found_reports_checked_candidates(self, tmp_path: Path) -> None:
        with patch("ansible_mcp.plugins.sys.executable", str(tmp_path / "python" / "python3")):
            resolution = resolve_executable(
                "ansible-lint",
                cwd=tmp_path,
                env={"PATH": "", "VIRTUAL_ENV": ""},
            )

        assert resolution.resolved is None
        assert resolution.source == "not-found"
        assert resolution.checked


# ---------------------------------------------------------------------------
# exec_command – resolver integration
# ---------------------------------------------------------------------------


class TestExecCommandResolverIntegration:
    async def test_uses_resolved_command_for_spawn(self, tmp_path: Path) -> None:
        proc = _mock_process(stdout=b"ok", returncode=0)
        create_mock = AsyncMock(return_value=proc)

        resolution = ExecutableResolution(
            requested="ansible-lint",
            resolved="/custom/bin/ansible-lint",
            source="env-override",
            env_var="ANSIBLE_MCP_ANSIBLE_LINT_EXECUTABLE",
            checked=["/custom/bin/ansible-lint"],
        )

        with (
            patch("ansible_mcp.plugins.resolve_executable", return_value=resolution),
            patch("asyncio.create_subprocess_exec", new=create_mock),
        ):
            result = await exec_command(["ansible-lint", "playbook.yml"], cwd=tmp_path)

        assert create_mock.call_args is not None
        assert create_mock.call_args[0][0] == "/custom/bin/ansible-lint"
        assert create_mock.call_args[0][1] == "playbook.yml"
        assert result["command"] == ["ansible-lint", "playbook.yml"]
        assert result["resolved_command"] == ["/custom/bin/ansible-lint", "playbook.yml"]

    async def test_resolution_failure_does_not_spawn(self, tmp_path: Path) -> None:
        create_mock = AsyncMock()
        resolution = ExecutableResolution(
            requested="ansible-lint",
            resolved=None,
            source="not-found",
            env_var="ANSIBLE_MCP_ANSIBLE_LINT_EXECUTABLE",
            checked=["/not/found"],
            warning="override invalid",
        )

        with (
            patch("ansible_mcp.plugins.resolve_executable", return_value=resolution),
            patch("asyncio.create_subprocess_exec", new=create_mock),
        ):
            result = await exec_command(["ansible-lint", "playbook.yml"], cwd=tmp_path)

        assert create_mock.call_count == 0
        assert result["status"] == "failed"
        assert result["exit_code"] is None
        assert "Command not found" in result["stderr"]
        assert result["executable_resolution"]["source"] == "not-found"
