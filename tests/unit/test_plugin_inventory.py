from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from ansible_mcp.context import WorkspaceContext
from ansible_mcp.plugins.inventory import InventoryPlugin
from ansible_mcp.token_budget import TokenBudget


def _workspace(root: Path) -> WorkspaceContext:
    return WorkspaceContext(
        root=root,
        has_roles=False,
        has_molecule=False,
        has_playbooks=False,
        has_inventory=True,
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


class TestInventoryPluginSpecs:
    def test_returns_two_specs(self) -> None:
        assert len(InventoryPlugin.tool_specs()) == 2

    def test_spec_names(self) -> None:
        names = {s.name for s in InventoryPlugin.tool_specs()}
        assert names == {"inventory_parse", "inventory_graph"}

    def test_specs_have_docs_uri(self) -> None:
        for spec in InventoryPlugin.tool_specs():
            assert spec.docs_uri == "ansible://docs/inventory"


# ---------------------------------------------------------------------------
# handle_tool_call
# ---------------------------------------------------------------------------


class TestInventoryPluginExecute:
    async def test_inventory_parse(self, tmp_path: Path) -> None:
        (tmp_path / "hosts.ini").touch()
        plugin = InventoryPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok(stdout='{"all": {}}'))
        with patch(
            "ansible_mcp.plugins.inventory.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "inventory_parse", {"inventory_path": "hosts.ini"}
            )
        assert result.status == "success"
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert cmd[0] == "ansible-inventory"
        assert "--list" in cmd

    async def test_inventory_graph(self, tmp_path: Path) -> None:
        (tmp_path / "hosts.ini").touch()
        plugin = InventoryPlugin(_workspace(tmp_path), _budget())
        mock = AsyncMock(return_value=_exec_ok(stdout="@all:"))
        with patch(
            "ansible_mcp.plugins.inventory.exec_command", new=mock
        ):
            result = await plugin.handle_tool_call(
                "inventory_graph", {"inventory_path": "hosts.ini"}
            )
        assert result.status == "success"
        assert mock.call_args is not None
        cmd: list[str] = mock.call_args[0][0]
        assert "--graph" in cmd

    async def test_unsupported_tool(self, tmp_path: Path) -> None:
        plugin = InventoryPlugin(_workspace(tmp_path), _budget())
        result = await plugin.handle_tool_call(
            "unknown", {"inventory_path": "hosts"}
        )
        assert result.status == "failed"
        assert "Unsupported tool" in result.payload["error"]

    async def test_empty_inventory_path(self, tmp_path: Path) -> None:
        plugin = InventoryPlugin(_workspace(tmp_path), _budget())
        result = await plugin.handle_tool_call(
            "inventory_parse", {"inventory_path": ""}
        )
        assert result.status == "failed"
        assert "required" in result.payload["error"]

    async def test_missing_inventory_path_key(
        self, tmp_path: Path
    ) -> None:
        plugin = InventoryPlugin(_workspace(tmp_path), _budget())
        result = await plugin.handle_tool_call("inventory_parse", {})
        assert result.status == "failed"
