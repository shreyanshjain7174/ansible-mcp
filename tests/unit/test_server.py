from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ansible_mcp.context import detect_workspace
from ansible_mcp.router import PluginRouter
from ansible_mcp.server import build_router, create_server
from ansible_mcp.token_budget import TokenBudget

# ---------------------------------------------------------------------------
# create_server
# ---------------------------------------------------------------------------


class TestCreateServer:
    def test_returns_fastmcp_instance(self, tmp_path: Path) -> None:
        mcp = create_server(workspace_root=tmp_path)
        assert isinstance(mcp, FastMCP)

    def test_accepts_custom_token_budget(self, tmp_path: Path) -> None:
        budget = TokenBudget(max_response_tokens=100)
        mcp = create_server(
            workspace_root=tmp_path, token_budget=budget
        )
        assert isinstance(mcp, FastMCP)


# ---------------------------------------------------------------------------
# build_router
# ---------------------------------------------------------------------------


class TestBuildRouter:
    def test_returns_plugin_router(self, tmp_path: Path) -> None:
        ws = detect_workspace(tmp_path)
        router = build_router(ws, TokenBudget())
        assert isinstance(router, PluginRouter)

    def test_registers_builtin_tools(self, tmp_path: Path) -> None:
        ws = detect_workspace(tmp_path)
        router = build_router(ws, TokenBudget())
        names = {s.name for s in router.list_tool_specs()}
        assert "lint" in names
        assert "inventory_parse" in names
        assert "inventory_graph" in names
        assert "playbook_syntax_check" in names
        assert "playbook_run" in names
