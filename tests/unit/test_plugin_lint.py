from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from ansible_mcp.context import WorkspaceContext
from ansible_mcp.plugins.lint import LintPlugin
from ansible_mcp.token_budget import TokenBudget


def _workspace(root: Path) -> WorkspaceContext:
    return WorkspaceContext(
        root=root,
        has_roles=False,
        has_molecule=False,
        has_playbooks=True,
        has_inventory=False,
    )


def _budget() -> TokenBudget:
    return TokenBudget()


def _exec_ok(
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> dict[str, Any]:
    return {
        "status": "success" if exit_code == 0 else "failed",
        "command": [],
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }


# ---------------------------------------------------------------------------
# tool_specs
# ---------------------------------------------------------------------------


class TestLintPluginSpecs:
    def test_returns_one_spec(self) -> None:
        specs = LintPlugin.tool_specs()
        assert len(specs) == 1

    def test_spec_name_is_lint(self) -> None:
        assert LintPlugin.tool_specs()[0].name == "lint"

    def test_spec_has_docs_uri(self) -> None:
        assert LintPlugin.tool_specs()[0].docs_uri == "ansible://docs/lint"


# ---------------------------------------------------------------------------
# handle_tool_call
# ---------------------------------------------------------------------------


class TestLintPluginExecute:
    async def test_lint_success(self, tmp_path: Path) -> None:
        (tmp_path / "site.yml").touch()
        plugin = LintPlugin(_workspace(tmp_path), _budget())
        with patch(
            "ansible_mcp.plugins.lint.exec_command",
            new=AsyncMock(return_value=_exec_ok()),
        ):
            result = await plugin.handle_tool_call(
                "lint", {"path": "site.yml"}
            )
        assert result.status == "success"

    async def test_lint_failure(self, tmp_path: Path) -> None:
        (tmp_path / "bad.yml").touch()
        plugin = LintPlugin(_workspace(tmp_path), _budget())
        with patch(
            "ansible_mcp.plugins.lint.exec_command",
            new=AsyncMock(
                return_value=_exec_ok(exit_code=2, stderr="lint err")
            ),
        ):
            result = await plugin.handle_tool_call(
                "lint", {"path": "bad.yml"}
            )
        assert result.status == "failed"

    async def test_lint_with_config_and_tags(self, tmp_path: Path) -> None:
        (tmp_path / "site.yml").touch()
        (tmp_path / ".ansible-lint").touch()
        plugin = LintPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok())
        with patch("ansible_mcp.plugins.lint.exec_command", new=mock):
            await plugin.handle_tool_call(
                "lint",
                {
                    "path": "site.yml",
                    "config": ".ansible-lint",
                    "tags": ["yaml"],
                },
            )
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        kwargs = mock.call_args.kwargs
        assert cmd[0] == "ansible-lint"
        assert cmd[1] == "--project-dir"
        assert cmd[2] == str(tmp_path)
        assert "-c" in cmd
        assert "--tags" in cmd
        assert "yaml" in cmd
        assert kwargs["cwd"] == tmp_path
        assert kwargs["env"]["HOME"] == str(tmp_path)
        assert kwargs["env"]["XDG_CACHE_HOME"] == str(tmp_path / ".cache")
        assert kwargs["env"]["ANSIBLE_HOME"] == str(tmp_path / ".ansible")

    async def test_unsupported_tool_name(self, tmp_path: Path) -> None:
        plugin = LintPlugin(_workspace(tmp_path), _budget())
        result = await plugin.handle_tool_call("unknown", {})
        assert result.status == "failed"
        assert "Unsupported tool" in result.payload["error"]

    async def test_empty_path_returns_error(self, tmp_path: Path) -> None:
        plugin = LintPlugin(_workspace(tmp_path), _budget())
        result = await plugin.handle_tool_call("lint", {"path": ""})
        assert result.status == "failed"
        assert "required" in result.payload["error"]

    async def test_default_path_is_dot(self, tmp_path: Path) -> None:
        plugin = LintPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok())
        with patch("ansible_mcp.plugins.lint.exec_command", new=mock):
            await plugin.handle_tool_call("lint", {})
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert cmd[0] == "ansible-lint"
        assert cmd[1] == "--project-dir"
        assert cmd[2] == str(tmp_path)
        assert cmd[3] == str(tmp_path.resolve())
