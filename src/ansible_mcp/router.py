from __future__ import annotations

import json
from dataclasses import asdict, replace
from typing import Any

from ansible_mcp.context import WorkspaceContext
from ansible_mcp.plugins import AnsibleMCPPlugin, ToolSpec
from ansible_mcp.token_budget import TokenBudget, compress_description, format_tool_output


class PluginRouter:
    def __init__(
        self,
        workspace: WorkspaceContext,
        token_budget: TokenBudget | None = None,
    ) -> None:
        self.workspace = workspace
        self.token_budget = token_budget or TokenBudget()
        self._tool_specs: dict[str, ToolSpec] = {}
        self._tool_to_plugin: dict[str, type[AnsibleMCPPlugin]] = {}
        self._plugin_instances: dict[str, AnsibleMCPPlugin] = {}

    def register_plugin(self, plugin_cls: type[AnsibleMCPPlugin]) -> None:
        if not plugin_cls.should_load(self.workspace):
            return

        for spec in plugin_cls.tool_specs():
            compact_spec = replace(
                spec,
                description=compress_description(
                    spec.description,
                    self.token_budget.max_description_tokens,
                ),
            )
            self._tool_specs[compact_spec.name] = compact_spec
            self._tool_to_plugin[compact_spec.name] = plugin_cls

    def _estimate_list_tokens(self, specs: list[ToolSpec]) -> int:
        payload = [asdict(spec) for spec in specs]
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
        chars_per_token = max(1, self.token_budget.approx_chars_per_token)
        return (len(serialized) + chars_per_token - 1) // chars_per_token

    def _compress_specs(self, specs: list[ToolSpec], max_description_tokens: int) -> list[ToolSpec]:
        return [
            replace(
                spec,
                description=compress_description(spec.description, max_description_tokens),
            )
            for spec in specs
        ]

    def list_tool_specs(self) -> list[ToolSpec]:
        specs = [self._tool_specs[name] for name in sorted(self._tool_specs.keys())]
        if not specs:
            return specs

        max_total_tokens = self.token_budget.max_total_list_tokens
        if self._estimate_list_tokens(specs) <= max_total_tokens:
            return specs

        min_description_tokens = 12
        starting_limit = max(self.token_budget.max_description_tokens, min_description_tokens)
        compact_specs = self._compress_specs(specs, starting_limit)
        if self._estimate_list_tokens(compact_specs) <= max_total_tokens:
            return compact_specs

        for description_limit in range(starting_limit - 1, min_description_tokens - 1, -1):
            compact_specs = self._compress_specs(specs, description_limit)
            if self._estimate_list_tokens(compact_specs) <= max_total_tokens:
                return compact_specs

        return compact_specs

    def list_tool_dicts(self) -> list[dict[str, Any]]:
        return [asdict(spec) for spec in self.list_tool_specs()]

    def get_tool_spec(self, name: str) -> ToolSpec | None:
        return self._tool_specs.get(name)

    async def execute(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        plugin_cls = self._tool_to_plugin.get(tool_name)
        if plugin_cls is None:
            available = ", ".join(sorted(self._tool_specs.keys()))
            raise ValueError(f"Unknown tool '{tool_name}'. Available tools: {available}")

        plugin_key = plugin_cls.__name__
        plugin = self._plugin_instances.get(plugin_key)
        if plugin is None:
            plugin = plugin_cls(self.workspace, self.token_budget)
            self._plugin_instances[plugin_key] = plugin

        result = await plugin.handle_tool_call(tool_name, args)
        return {
            "status": result.status,
            "raw": result.payload,
            "text": format_tool_output(result.payload, self.token_budget),
        }
