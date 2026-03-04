from __future__ import annotations

from pathlib import Path

import pytest

from ansible_mcp.context import detect_workspace
from ansible_mcp.plugins import AnsibleMCPPlugin, ToolResult, ToolSpec
from ansible_mcp.router import PluginRouter
from ansible_mcp.token_budget import TokenBudget


class DemoPlugin(AnsibleMCPPlugin):
    @classmethod
    def tool_specs(cls) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="demo_tool",
                description="A demo tool that returns a payload.",
                input_schema={"type": "object", "properties": {}},
            )
        ]

    async def handle_tool_call(self, name: str, args: dict) -> ToolResult:
        return ToolResult(status="success", payload={"name": name, "args": args})


@pytest.mark.asyncio
async def test_router_register_and_execute(tmp_path: Path) -> None:
    workspace = detect_workspace(tmp_path)
    router = PluginRouter(workspace=workspace, token_budget=TokenBudget())
    router.register_plugin(DemoPlugin)

    tools = router.list_tool_specs()
    assert len(tools) == 1
    assert tools[0].name == "demo_tool"

    result = await router.execute("demo_tool", {"k": "v"})
    assert result["status"] == "success"
    assert result["raw"]["args"]["k"] == "v"


@pytest.mark.asyncio
async def test_router_unknown_tool_raises(tmp_path: Path) -> None:
    workspace = detect_workspace(tmp_path)
    router = PluginRouter(workspace=workspace, token_budget=TokenBudget())

    with pytest.raises(ValueError):
        await router.execute("missing", {})
