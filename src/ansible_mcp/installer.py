from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

ClientName = Literal["copilot", "claude", "cursor"]
InstallScope = Literal["user", "project"]


@dataclass(frozen=True)
class InstallResult:
    client: ClientName
    scope: InstallScope
    config_path: Path
    server_name: str


def _vscode_user_mcp_path(
    *,
    home_dir: Path,
    platform: str,
    appdata: str | None,
) -> Path:
    if platform == "darwin":
        return home_dir / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
    if platform.startswith("win"):
        if appdata:
            return Path(appdata) / "Code" / "User" / "mcp.json"
        return home_dir / "AppData" / "Roaming" / "Code" / "User" / "mcp.json"
    return home_dir / ".config" / "Code" / "User" / "mcp.json"


def _target_for_client(
    *,
    client: ClientName,
    scope: InstallScope,
    workspace_root: Path | None,
    home_dir: Path,
    platform: str,
    appdata: str | None,
) -> tuple[Path, str]:
    if scope == "project":
        if workspace_root is None:
            raise ValueError("workspace_root is required for project scope")
        if client == "copilot":
            return workspace_root / ".vscode" / "mcp.json", "servers"
        if client == "cursor":
            return workspace_root / ".cursor" / "mcp.json", "mcpServers"
        raise ValueError("Project scope is not supported for client 'claude'")

    if client == "copilot":
        return (
            _vscode_user_mcp_path(
                home_dir=home_dir,
                platform=platform,
                appdata=appdata,
            ),
            "servers",
        )
    if client == "claude":
        return home_dir / ".claude" / "mcp_servers.json", "mcpServers"
    if client == "cursor":
        return home_dir / ".cursor" / "mcp.json", "mcpServers"

    raise ValueError(f"Unsupported client: {client}")


def _build_server_definition(client: ClientName) -> dict[str, Any]:
    definition: dict[str, Any] = {
        "command": "ansible-mcp",
        "args": ["serve", "--stdio"],
    }
    if client == "copilot":
        definition["type"] = "stdio"
        definition["env"] = {"WORKSPACE_ROOT": "${workspaceFolder}"}
    elif client == "cursor":
        definition["env"] = {"WORKSPACE_ROOT": "${workspaceFolder}"}
    return definition


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def install_client_config(
    *,
    client: ClientName,
    scope: InstallScope,
    server_name: str = "ansible-mcp",
    workspace_root: Path | None = None,
    home_dir: Path | None = None,
    platform: str | None = None,
    appdata: str | None = None,
) -> InstallResult:
    resolved_home = home_dir or Path.home()
    resolved_platform = platform or sys.platform
    resolved_appdata = appdata if appdata is not None else os.getenv("APPDATA")

    config_path, server_key = _target_for_client(
        client=client,
        scope=scope,
        workspace_root=workspace_root,
        home_dir=resolved_home,
        platform=resolved_platform,
        appdata=resolved_appdata,
    )

    config = _load_json(config_path)
    existing_servers = config.get(server_key)
    if existing_servers is None:
        servers: dict[str, Any] = {}
    elif isinstance(existing_servers, dict):
        servers = dict(existing_servers)
    else:
        raise ValueError(f"Expected '{server_key}' to be an object in {config_path}")

    servers[server_name] = _build_server_definition(client)
    config[server_key] = servers

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    return InstallResult(
        client=client,
        scope=scope,
        config_path=config_path,
        server_name=server_name,
    )
