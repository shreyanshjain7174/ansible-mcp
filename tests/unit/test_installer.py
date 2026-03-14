from __future__ import annotations

import json
from pathlib import Path

import pytest

from ansible_mcp.installer import install_client_config


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_install_copilot_user_scope_on_macos_path(tmp_path: Path) -> None:
    result = install_client_config(
        client="copilot",
        scope="user",
        home_dir=tmp_path,
        platform="darwin",
    )

    expected = tmp_path / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
    assert result.config_path == expected
    payload = _read_json(expected)
    server = payload["servers"]["ansible-mcp"]
    assert server["type"] == "stdio"
    assert server["command"] == "ansible-mcp"


def test_install_claude_user_scope(tmp_path: Path) -> None:
    result = install_client_config(
        client="claude",
        scope="user",
        home_dir=tmp_path,
    )

    expected = tmp_path / ".claude" / "mcp_servers.json"
    assert result.config_path == expected
    payload = _read_json(expected)
    assert "mcpServers" in payload
    server = payload["mcpServers"]["ansible-mcp"]
    assert server["command"] == "ansible-mcp"
    assert server["args"] == ["serve", "--stdio"]


def test_install_cursor_project_scope(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = install_client_config(
        client="cursor",
        scope="project",
        workspace_root=workspace,
    )

    expected = workspace / ".cursor" / "mcp.json"
    assert result.config_path == expected
    payload = _read_json(expected)
    assert "mcpServers" in payload
    server = payload["mcpServers"]["ansible-mcp"]
    assert server["command"] == "ansible-mcp"


def test_install_project_scope_requires_workspace_root() -> None:
    with pytest.raises(ValueError, match="workspace_root is required"):
        install_client_config(client="copilot", scope="project")


def test_install_claude_project_scope_not_supported(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not supported"):
        install_client_config(
            client="claude",
            scope="project",
            workspace_root=tmp_path,
        )
