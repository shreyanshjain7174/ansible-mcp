from __future__ import annotations

import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ansible_mcp.context import WorkspaceContext, detect_workspace
from ansible_mcp.plugins import AnsibleMCPPlugin
from ansible_mcp.plugins.inventory import InventoryPlugin
from ansible_mcp.plugins.lint import LintPlugin
from ansible_mcp.plugins.playbook import PlaybookPlugin
from ansible_mcp.router import PluginRouter
from ansible_mcp.token_budget import TokenBudget
from ansible_mcp.upstream import (
    UPSTREAM_ZEN_OF_ANSIBLE,
    upstream_tool_catalog,
)
from ansible_mcp.upstream_tools import (
    check_and_install_adt,
    create_ansible_project,
    get_ade_environment_info,
    run_ansible_navigator,
    setup_development_environment,
)
from ansible_mcp.upstream_tools import (
    define_and_build_execution_env as define_and_build_execution_env_artifacts,
)

logger = logging.getLogger(__name__)


def _builtin_plugins() -> list[type[AnsibleMCPPlugin]]:
    return [LintPlugin, PlaybookPlugin, InventoryPlugin]


def _discover_external_plugins() -> list[type[AnsibleMCPPlugin]]:
    discovered: list[type[AnsibleMCPPlugin]] = []

    for ep in entry_points(group="ansible_mcp.plugins"):
        try:
            loaded = ep.load()
        except Exception as exc:
            logger.warning("Failed to load ansible-mcp plugin entry point '%s': %s", ep.name, exc)
            continue
        if isinstance(loaded, type) and issubclass(loaded, AnsibleMCPPlugin):
            discovered.append(loaded)
    return discovered


def build_router(workspace: WorkspaceContext, token_budget: TokenBudget) -> PluginRouter:
    router = PluginRouter(workspace=workspace, token_budget=token_budget)
    seen: set[str] = set()
    for plugin_cls in [*_builtin_plugins(), *_discover_external_plugins()]:
        key = f"{plugin_cls.__module__}.{plugin_cls.__qualname__}"
        if key in seen:
            continue
        seen.add(key)
        router.register_plugin(plugin_cls)
    return router


def _docs_path() -> Path:
    return Path(__file__).parent / "resources" / "docs"


def _read_doc(name: str) -> str:
    doc_file = _docs_path() / name
    if not doc_file.exists():
        return f"Documentation not found: {name}"
    return doc_file.read_text(encoding="utf-8")


def create_server(
    *,
    workspace_root: Path | None = None,
    token_budget: TokenBudget | None = None,
) -> FastMCP:
    workspace = detect_workspace(workspace_root)
    budget = token_budget or TokenBudget()
    router = build_router(workspace, budget)

    mcp = FastMCP(
        "ansible-mcp",
        instructions="Standalone MCP server for Ansible lint, playbook, and inventory tooling.",
        json_response=True,
    )

    @mcp.tool()
    def list_ansible_tools() -> list[dict[str, Any]]:
        """List ansible-mcp tool metadata with compact descriptions."""

        return router.list_tool_dicts()

    @mcp.tool()
    def list_available_tools() -> list[dict[str, str | bool | None]]:
        """List upstream-compatible tools and whether each is currently available."""

        available_router_tools = {spec.name for spec in router.list_tool_specs()}
        available_server_tools = {
            "zen_of_ansible",
            "ansible_content_best_practices",
            "list_available_tools",
            "ade_environment_info",
            "ade_setup_environment",
            "adt_check_env",
            "ansible_create_playbook",
            "ansible_create_collection",
            "define_and_build_execution_env",
            "ansible_navigator",
        }
        return upstream_tool_catalog(available_router_tools, available_server_tools)

    @mcp.tool()
    def zen_of_ansible() -> str:
        """Return the Zen of Ansible aphorisms."""

        return UPSTREAM_ZEN_OF_ANSIBLE

    @mcp.tool()
    def ansible_content_best_practices(topic: str | None = None) -> str:
        """Return best-practices guidance for Ansible content."""

        full_text = _read_doc("best_practices.md")
        if topic is None or not topic.strip():
            return full_text

        normalized_topic = topic.strip().lower()
        sections = [section.strip() for section in full_text.split("\n## ")]
        for section in sections:
            if section.lower().startswith(normalized_topic):
                if section.startswith("#"):
                    return section
                return f"## {section}"
        return full_text

    @mcp.tool()
    async def ansible_lint(filePath: str, fix: bool | None = None) -> dict[str, Any]:
        """Upstream-compatible wrapper around lint."""

        result = await router.execute(
            "lint",
            {
                "path": filePath,
            },
        )
        if fix is True:
            raw = result.get("raw", {})
            if isinstance(raw, dict):
                raw["notice"] = (
                    "'fix=true' requested, but standalone ansible-mcp currently runs "
                    "read-only lint mode. Auto-fix parity is planned."
                )
        return result

    @mcp.tool()
    async def ade_environment_info() -> dict[str, Any]:
        """Get comprehensive environment information for Ansible development."""

        return await get_ade_environment_info(workspace.root)

    @mcp.tool()
    async def adt_check_env() -> dict[str, Any]:
        """Check and install ADT (ansible-dev-tools) when needed."""

        return await check_and_install_adt(workspace.root)

    @mcp.tool()
    async def ade_setup_environment(
        envName: str | None = None,
        pythonVersion: str | None = None,
        collections: list[str] | None = None,
        installRequirements: bool = False,
        requirementsFile: str | None = None,
    ) -> dict[str, Any]:
        """Setup an Ansible development environment with venv and tool installation."""

        return await setup_development_environment(
            workspace.root,
            env_name=envName,
            python_version=pythonVersion,
            collections=collections,
            install_requirements=installRequirements,
            requirements_file=requirementsFile,
        )

    @mcp.tool()
    async def ansible_create_playbook(name: str, path: str | None = None) -> dict[str, Any]:
        """Create a new Ansible playbook project scaffold via ansible-creator."""

        return await create_ansible_project(
            workspace.root,
            project_type="playbook",
            name=name,
            path=path,
        )

    @mcp.tool()
    async def ansible_create_collection(name: str, path: str | None = None) -> dict[str, Any]:
        """Create a new Ansible collection scaffold via ansible-creator."""

        return await create_ansible_project(
            workspace.root,
            project_type="collection",
            name=name,
            path=path,
        )

    @mcp.tool()
    def define_and_build_execution_env(
        baseImage: str | None = None,
        tag: str | None = None,
        destinationPath: str | None = None,
        collections: list[str] | None = None,
        systemPackages: list[str] | None = None,
        pythonPackages: list[str] | None = None,
        generatedYaml: str | None = None,
    ) -> dict[str, Any]:
        """Define and build execution environment artifacts (two-step prompt + write flow)."""

        return define_and_build_execution_env_artifacts(
            workspace.root,
            base_image=baseImage,
            tag=tag,
            destination_path=destinationPath,
            collections=collections,
            system_packages=systemPackages,
            python_packages=pythonPackages,
            generated_yaml=generatedYaml,
        )

    @mcp.tool()
    async def ansible_navigator(
        userMessage: str | None = None,
        filePath: str | None = None,
        mode: str | None = None,
        environment: str | None = None,
        disableExecutionEnvironment: bool = False,
    ) -> dict[str, Any]:
        """Execute ansible-navigator in info mode or run mode."""

        return await run_ansible_navigator(
            workspace.root,
            user_message=userMessage,
            file_path=filePath,
            mode=mode,
            disable_execution_environment=disableExecutionEnvironment,
            environment=environment,
        )

    @mcp.tool()
    async def lint(
        path: str = ".",
        config: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Lint Ansible files using ansible-lint."""

        return await router.execute(
            "lint",
            {
                "path": path,
                "config": config,
                "tags": tags or [],
            },
        )

    @mcp.tool()
    async def playbook_syntax_check(
        playbook_path: str,
        inventory_path: str | None = None,
    ) -> dict[str, Any]:
        """Run ansible-playbook --syntax-check."""

        return await router.execute(
            "playbook_syntax_check",
            {
                "playbook_path": playbook_path,
                "inventory_path": inventory_path,
            },
        )

    @mcp.tool()
    async def playbook_run(
        playbook_path: str,
        inventory_path: str | None = None,
        check: bool = False,
        limit: str | None = None,
    ) -> dict[str, Any]:
        """Run ansible-playbook with optional check mode and host limit."""

        return await router.execute(
            "playbook_run",
            {
                "playbook_path": playbook_path,
                "inventory_path": inventory_path,
                "check": check,
                "limit": limit,
            },
        )

    @mcp.tool()
    async def inventory_parse(inventory_path: str) -> dict[str, Any]:
        """Parse inventory using ansible-inventory --list."""

        return await router.execute("inventory_parse", {"inventory_path": inventory_path})

    @mcp.tool()
    async def inventory_graph(inventory_path: str) -> dict[str, Any]:
        """Render inventory graph using ansible-inventory --graph."""

        return await router.execute("inventory_graph", {"inventory_path": inventory_path})

    @mcp.resource("ansible://docs/lint")
    def lint_docs() -> str:
        """Detailed docs for lint tool."""

        return _read_doc("lint.md")

    @mcp.resource("ansible://docs/playbook")
    def playbook_docs() -> str:
        """Detailed docs for playbook tools."""

        return _read_doc("playbook.md")

    @mcp.resource("ansible://docs/inventory")
    def inventory_docs() -> str:
        """Detailed docs for inventory tools."""

        return _read_doc("inventory.md")

    @mcp.resource("ansible://docs/upstream-parity")
    def upstream_parity_docs() -> str:
        """Current upstream tool parity status."""

        return _read_doc("upstream_parity.md")

    @mcp.resource("ansible://docs/environment")
    def environment_docs() -> str:
        """Detailed docs for ADE/ADT environment tools."""

        return _read_doc("environment.md")

    @mcp.resource("ansible://docs/project-generators")
    def project_generator_docs() -> str:
        """Detailed docs for project generator tools."""

        return _read_doc("project_generators.md")

    @mcp.resource("ansible://docs/execution-environment")
    def execution_environment_docs() -> str:
        """Detailed docs for execution environment helper tool."""

        return _read_doc("execution_environment.md")

    @mcp.resource("ansible://docs/navigator")
    def navigator_docs() -> str:
        """Detailed docs for ansible_navigator tool."""

        return _read_doc("navigator.md")

    @mcp.resource("schema://execution-environment")
    def execution_environment_schema() -> str:
        """JSON schema for execution-environment definition files."""

        return _read_doc("execution_environment_schema.json")

    @mcp.resource("sample://execution-environment")
    def execution_environment_sample() -> str:
        """Sample execution-environment YAML document."""

        return _read_doc("execution_environment_sample.yml")

    @mcp.resource("rules://execution-environment")
    def execution_environment_rules() -> str:
        """Rules/guidelines for generating execution-environment files."""

        return _read_doc("execution_environment_rules.md")

    @mcp.resource("guidelines://ansible-content-best-practices")
    def content_best_practices_guidelines() -> str:
        """Official-style URI alias for best-practices guidance."""

        return _read_doc("best_practices.md")

    return mcp


def run_server(
    *,
    workspace_root: Path | None = None,
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
    stateless_http: bool = False,
) -> None:
    mcp = create_server(workspace_root=workspace_root)
    mcp.settings.host = host
    mcp.settings.port = port

    if transport == "stdio":
        mcp.run()
        return
    if transport == "streamable-http":
        mcp.settings.stateless_http = stateless_http
        mcp.run(transport="streamable-http")
        return
    if transport == "sse":
        mcp.run(transport="sse")
        return
    raise ValueError(f"Unsupported transport: {transport}")
