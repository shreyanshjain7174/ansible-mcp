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


class LintPlugin(AnsibleMCPPlugin):
    @classmethod
    def tool_specs(cls) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="lint",
                description="Lint Ansible files and return issues with severity, line, and rule.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File or directory to lint",
                            "default": ".",
                        },
                        "config": {
                            "type": "string",
                            "description": "Optional ansible-lint config file",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional ansible-lint tags",
                        },
                    },
                    "required": ["path"],
                },
                docs_uri="ansible://docs/lint",
            )
        ]

    async def handle_tool_call(self, name: str, args: dict[str, Any]) -> ToolResult:
        if name != "lint":
            return ToolResult(status="failed", payload={"error": f"Unsupported tool: {name}"})

        try:
            path = require_non_empty(args.get("path", "."), "path")
            resolved_path = resolve_workspace_path(self.workspace.root, path)

            config = args.get("config")
            resolved_config: str | None = None
            if config is not None:
                config_value = require_non_empty(config, "config")
                resolved_config = str(resolve_workspace_path(self.workspace.root, config_value))

            tags = args.get("tags", [])
        except ValueError as exc:
            return ToolResult(status="failed", payload={"error": str(exc)})

        command = [
            "ansible-lint",
            "--project-dir",
            str(self.workspace.root),
            str(resolved_path),
        ]
        if resolved_config is not None:
            command.extend(["-c", resolved_config])
        if isinstance(tags, list) and tags:
            command.extend(["--tags", ",".join(str(tag) for tag in tags)])

        lint_env = build_workspace_exec_env(self.workspace.root)
        result = await exec_command(command, cwd=self.workspace.root, env=lint_env)
        status = "success" if result["exit_code"] == 0 else "failed"
        return ToolResult(status=status, payload=result)
