from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpstreamTool:
    name: str
    category: str
    description: str
    mapped_to: str | None = None


UPSTREAM_TOOLS: tuple[UpstreamTool, ...] = (
    UpstreamTool(
        name="zen_of_ansible",
        category="information",
        description="Ansible design philosophy and principles.",
    ),
    UpstreamTool(
        name="ansible_content_best_practices",
        category="information",
        description="Best practices and guidelines for writing Ansible content.",
    ),
    UpstreamTool(
        name="list_available_tools",
        category="information",
        description="List all upstream-compatible tools and availability.",
    ),
    UpstreamTool(
        name="ansible_lint",
        category="validation",
        description="Run ansible-lint for a playbook/file path.",
        mapped_to="lint",
    ),
    UpstreamTool(
        name="ade_environment_info",
        category="environment",
        description="Get development environment information.",
    ),
    UpstreamTool(
        name="ade_setup_environment",
        category="environment",
        description="Setup development environment.",
    ),
    UpstreamTool(
        name="adt_check_env",
        category="environment",
        description="Check and install Ansible development tools.",
    ),
    UpstreamTool(
        name="ansible_create_playbook",
        category="project-generators",
        description="Create a new Ansible playbook project scaffold.",
    ),
    UpstreamTool(
        name="ansible_create_collection",
        category="project-generators",
        description="Create a new Ansible collection project scaffold.",
    ),
    UpstreamTool(
        name="define_and_build_execution_env",
        category="validation",
        description="Define and build execution environment artifacts.",
    ),
    UpstreamTool(
        name="ansible_navigator",
        category="playbook-execution",
        description="Execute playbooks through ansible-navigator.",
    ),
)


UPSTREAM_ZEN_OF_ANSIBLE = """1. Ansible is not Python.
2. YAML is for declarations, not complex logic.
3. Idempotency is better than imperative steps.
4. Readability counts.
5. Simple tasks beat clever tasks.
6. Explicit is better than implicit.
7. Roles should be composable.
8. Variables should be predictable.
9. Inventories should reflect reality.
10. Playbooks should describe intent.
11. Modules are better than shell commands.
12. Check mode should be meaningful.
13. Lint early, lint often.
14. Prefer FQCNs for clarity.
15. Keep secrets out of plain text.
16. Minimize side effects.
17. Fail clearly and early.
18. Tests increase confidence.
19. Automation should be maintainable.
20. Consistency enables scale."""


def upstream_tool_names() -> list[str]:
    return [tool.name for tool in UPSTREAM_TOOLS]


def upstream_tool_catalog(available_router_tools: set[str]) -> list[dict[str, str | bool | None]]:
    always_available = {
        "zen_of_ansible",
        "ansible_content_best_practices",
        "list_available_tools",
    }
    catalog: list[dict[str, str | bool | None]] = []
    for tool in UPSTREAM_TOOLS:
        available = tool.name in always_available
        if tool.mapped_to is not None:
            available = tool.mapped_to in available_router_tools

        catalog.append(
            {
                "name": tool.name,
                "category": tool.category,
                "description": tool.description,
                "mapped_to": tool.mapped_to,
                "available": available,
                "status": "implemented" if available else "planned",
            }
        )
    return catalog
