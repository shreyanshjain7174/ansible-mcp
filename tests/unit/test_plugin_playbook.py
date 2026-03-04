from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from ansible_mcp.context import WorkspaceContext
from ansible_mcp.plugins.playbook import PlaybookPlugin
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


class TestPlaybookPluginSpecs:
    def test_returns_two_specs(self) -> None:
        assert len(PlaybookPlugin.tool_specs()) == 2

    def test_spec_names(self) -> None:
        names = {s.name for s in PlaybookPlugin.tool_specs()}
        assert names == {"playbook_syntax_check", "playbook_run"}

    def test_specs_have_docs_uri(self) -> None:
        for spec in PlaybookPlugin.tool_specs():
            assert spec.docs_uri == "ansible://docs/playbook"


# ---------------------------------------------------------------------------
# handle_tool_call
# ---------------------------------------------------------------------------


class TestPlaybookPluginExecute:
    async def test_syntax_check(self, tmp_path: Path) -> None:
        (tmp_path / "site.yml").touch()
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok())
        with patch(
            "ansible_mcp.plugins.playbook.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "playbook_syntax_check",
                {"playbook_path": "site.yml"},
            )
        assert result.status == "success"
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert cmd[0] == "ansible-playbook"
        assert "--syntax-check" in cmd

    async def test_playbook_run_basic(self, tmp_path: Path) -> None:
        (tmp_path / "site.yml").touch()
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok())
        with patch(
            "ansible_mcp.plugins.playbook.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "playbook_run", {"playbook_path": "site.yml"}
            )
        assert result.status == "success"
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert cmd[0] == "ansible-playbook"

    async def test_playbook_run_check_mode(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "site.yml").touch()
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok())
        with patch(
            "ansible_mcp.plugins.playbook.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "playbook_run",
                {"playbook_path": "site.yml", "check": True},
            )
        assert result.status == "success"
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert "--check" in cmd

    async def test_playbook_run_with_limit(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "site.yml").touch()
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok())
        with patch(
            "ansible_mcp.plugins.playbook.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "playbook_run",
                {
                    "playbook_path": "site.yml",
                    "limit": "webservers",
                },
            )
        assert result.status == "success"
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert "--limit" in cmd
        assert "webservers" in cmd

    async def test_playbook_run_with_inventory(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "site.yml").touch()
        (tmp_path / "hosts.ini").touch()
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok())
        with patch(
            "ansible_mcp.plugins.playbook.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "playbook_run",
                {
                    "playbook_path": "site.yml",
                    "inventory_path": "hosts.ini",
                },
            )
        assert result.status == "success"
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert "-i" in cmd

    async def test_unsupported_tool(self, tmp_path: Path) -> None:
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        result = await plugin.handle_tool_call(
            "unknown", {"playbook_path": "site.yml"}
        )
        assert result.status == "failed"
        assert "Unsupported tool" in result.payload["error"]

    async def test_empty_playbook_path(self, tmp_path: Path) -> None:
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        result = await plugin.handle_tool_call(
            "playbook_syntax_check", {"playbook_path": ""}
        )
        assert result.status == "failed"
        assert "required" in result.payload["error"]

    async def test_syntax_check_failure(self, tmp_path: Path) -> None:
        (tmp_path / "bad.yml").touch()
        plugin = PlaybookPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(
            return_value=_exec_ok(exit_code=4, stderr="syntax error")
        )
        with patch(
            "ansible_mcp.plugins.playbook.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "playbook_syntax_check",
                {"playbook_path": "bad.yml"},
            )
        assert result.status == "failed"
