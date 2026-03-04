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


class PlaybookPlugin(AnsibleMCPPlugin):
    @classmethod
    def tool_specs(cls) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="playbook_syntax_check",
                description="Run ansible-playbook syntax check for a playbook.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "playbook_path": {
                            "type": "string",
                            "description": "Path to playbook YAML",
                        },
                        "inventory_path": {
                            "type": "string",
                            "description": "Optional inventory path",
                        },
                    },
                    "required": ["playbook_path"],
                },
                docs_uri="ansible://docs/playbook",
            ),
            ToolSpec(
                name="playbook_run",
                description="Execute ansible-playbook with optional inventory and check mode.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "playbook_path": {
                            "type": "string",
                            "description": "Path to playbook YAML",
                        },
                        "inventory_path": {
                            "type": "string",
                            "description": "Optional inventory path",
                        },
                        "check": {
                            "type": "boolean",
                            "description": "Enable check mode",
                            "default": False,
                        },
                        "limit": {
                            "type": "string",
                            "description": "Optional host limit expression",
                        },
                    },
                    "required": ["playbook_path"],
                },
                docs_uri="ansible://docs/playbook",
            ),
        ]

    async def handle_tool_call(self, name: str, args: dict[str, Any]) -> ToolResult:
        run_env = build_workspace_exec_env(self.workspace.root)

        if name == "playbook_syntax_check":
            try:
                command = self._build_base_command(args)
            except ValueError as exc:
                return ToolResult(status="failed", payload={"error": str(exc)})
            command.append("--syntax-check")
            result = await exec_command(command, cwd=self.workspace.root, env=run_env)
            return ToolResult(status=result["status"], payload=result)

        if name == "playbook_run":
            try:
                command = self._build_base_command(args)
            except ValueError as exc:
                return ToolResult(status="failed", payload={"error": str(exc)})
            if bool(args.get("check", False)):
                command.append("--check")
            limit = args.get("limit")
            if isinstance(limit, str) and limit.strip():
                command.extend(["--limit", limit])
            result = await exec_command(command, cwd=self.workspace.root, env=run_env)
            return ToolResult(status=result["status"], payload=result)

        return ToolResult(status="failed", payload={"error": f"Unsupported tool: {name}"})

    def _build_base_command(self, args: dict[str, Any]) -> list[str]:
        playbook_path = require_non_empty(args.get("playbook_path"), "playbook_path")
        resolved_playbook_path = resolve_workspace_path(self.workspace.root, playbook_path)

        command = ["ansible-playbook", str(resolved_playbook_path)]
        inventory_path = args.get("inventory_path")
        if inventory_path is not None:
            inventory_value = require_non_empty(inventory_path, "inventory_path")
            resolved_inventory_path = resolve_workspace_path(self.workspace.root, inventory_value)
            command.extend(["-i", str(resolved_inventory_path)])
        return command
