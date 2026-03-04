from __future__ import annotations

from typing import Any

from ansible_mcp.plugins import (
    AnsibleMCPPlugin,
    ToolResult,
    ToolSpec,
    build_workspace_exec_env,
    exec_command,
    require_non_empty,
    resolve_workspace_path,
)


class InventoryPlugin(AnsibleMCPPlugin):
    @classmethod
    def tool_specs(cls) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="inventory_parse",
                description="Parse inventory and return ansible-inventory --list output.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "inventory_path": {
                            "type": "string",
                            "description": "Inventory file/directory path",
                        }
                    },
                    "required": ["inventory_path"],
                },
                docs_uri="ansible://docs/inventory",
            ),
            ToolSpec(
                name="inventory_graph",
                description="Render inventory graph using ansible-inventory --graph.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "inventory_path": {
                            "type": "string",
                            "description": "Inventory file/directory path",
                        }
                    },
                    "required": ["inventory_path"],
                },
                docs_uri="ansible://docs/inventory",
            ),
        ]

    async def handle_tool_call(self, name: str, args: dict[str, Any]) -> ToolResult:
        run_env = build_workspace_exec_env(self.workspace.root)

        try:
            inventory_path = require_non_empty(args.get("inventory_path"), "inventory_path")
            resolved_inventory_path = resolve_workspace_path(self.workspace.root, inventory_path)
        except ValueError as exc:
            return ToolResult(status="failed", payload={"error": str(exc)})

        inventory_path_str = str(resolved_inventory_path)

        if name == "inventory_parse":
            command = ["ansible-inventory", "-i", inventory_path_str, "--list"]
            result = await exec_command(command, cwd=self.workspace.root, env=run_env)
            return ToolResult(status=result["status"], payload=result)

        if name == "inventory_graph":
            command = ["ansible-inventory", "-i", inventory_path_str, "--graph"]
            result = await exec_command(command, cwd=self.workspace.root, env=run_env)
            return ToolResult(status=result["status"], payload=result)

        return ToolResult(status="failed", payload={"error": f"Unsupported tool: {name}"})
