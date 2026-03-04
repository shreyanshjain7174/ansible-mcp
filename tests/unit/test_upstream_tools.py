from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from ansible_mcp.upstream_tools import (
    check_and_install_adt,
    create_ansible_project,
    define_and_build_execution_env,
    format_environment_info,
    get_ade_environment_info,
    run_ansible_navigator,
    setup_development_environment,
)


def _exec_result(
    *,
    status: str = "success",
    stdout: str = "",
    stderr: str = "",
    command: list[str] | None = None,
    resolved_command: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "command": command or [],
        "resolved_command": resolved_command or command or [],
    }


async def test_get_ade_environment_info_collects_expected_fields(tmp_path: Path) -> None:
    (tmp_path / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".venv" / "bin" / "activate").touch()

    async def fake_exec(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: int = 120,
    ) -> dict[str, Any]:
        del cwd, env, timeout_seconds
        if argv[:2] == ["python3", "--version"]:
            return _exec_result(stdout="Python 3.12.2")
        if argv[:2] == ["ansible", "--version"]:
            return _exec_result(stdout="ansible [core 2.18.0]\nextra")
        if argv[:2] == ["ansible-lint", "--version"]:
            return _exec_result(stdout="ansible-lint 26.3.0")
        if argv[:2] == ["ade", "--version"]:
            return _exec_result(stdout="ade 0.0.1")
        if argv == ["pip", "list", "--format=json"]:
            package_list = [{"name": "ansible-dev-tools", "version": "1.0.0"}]
            return _exec_result(stdout=json.dumps(package_list))
        if argv[:3] == ["ansible-galaxy", "collection", "list"]:
            return _exec_result(
                stdout=(
                    "Collection Version\n"
                    "ansible.posix 2.0.0\n"
                    "community.general 9.0.0\n"
                )
            )
        return _exec_result(status="failed", stderr="unexpected command")

    with patch("ansible_mcp.upstream_tools.exec_command", new=AsyncMock(side_effect=fake_exec)):
        result = await get_ade_environment_info(tmp_path)

    assert result["success"] is True
    environment = result["environment"]
    assert environment["pythonVersion"] == "Python 3.12.2"
    assert environment["ansibleVersion"] == "ansible [core 2.18.0]"
    assert environment["ansibleLintVersion"] == "ansible-lint 26.3.0"
    assert environment["adeInstalled"] is True
    assert environment["adtInstalled"] is True
    assert environment["installedCollections"] == ["ansible.posix", "community.general"]
    assert "Environment Information" in result["output"]


def test_format_environment_info_handles_missing_values() -> None:
    info = {
        "workspacePath": "/tmp/workspace",
        "pythonVersion": "Unknown",
        "virtualEnv": None,
        "ansibleVersion": None,
        "ansibleLintVersion": None,
        "adeInstalled": False,
        "adtInstalled": False,
        "installedCollections": [],
    }
    formatted = format_environment_info(info)

    assert "Virtual Environment: Not set" in formatted
    assert "- Ansible: Not installed" in formatted
    assert "- Ansible Lint: Not installed" in formatted
    assert "- ADE: Not installed" in formatted
    assert "- ADT: Not installed" in formatted
    assert "- None" in formatted


async def test_check_and_install_adt_uses_pipx_fallback(tmp_path: Path) -> None:
    with (
        patch("ansible_mcp.upstream_tools._check_adt_installed", new=AsyncMock(return_value=False)),
        patch(
            "ansible_mcp.upstream_tools.exec_command",
            new=AsyncMock(
                side_effect=[
                    _exec_result(status="failed", stderr="pip failed"),
                    _exec_result(status="success", stdout="installed"),
                ]
            ),
        ),
    ):
        result = await check_and_install_adt(tmp_path)

    assert result["success"] is True
    assert "pipx" in result["output"]


async def test_setup_development_environment_auto_detects_os(tmp_path: Path) -> None:
    mock_exec = AsyncMock(
        side_effect=[
            _exec_result(status="success", stdout="ansible-lint 26.3.0"),
            _exec_result(status="success", stdout="venv created"),
            _exec_result(status="success", stdout="adt installed"),
            _exec_result(status="success", stdout="ansible-lint 26.3.0"),
        ]
    )

    with (
        patch(
            "ansible_mcp.upstream_tools.check_and_install_adt",
            new=AsyncMock(return_value={"success": True, "output": "ADT installed"}),
        ),
        patch("ansible_mcp.upstream_tools.exec_command", new=mock_exec),
    ):
        result = await setup_development_environment(tmp_path)

    assert result["success"] is True
    assert "Starting Ansible development environment setup" in result["output"]


async def test_create_ansible_project_runs_ansible_creator(tmp_path: Path) -> None:
    mock_exec = AsyncMock(return_value=_exec_result(status="success", stdout="ok"))
    with patch("ansible_mcp.upstream_tools.exec_command", new=mock_exec):
        result = await create_ansible_project(
            tmp_path,
            project_type="playbook",
            name="acme.site",
            path=None,
        )

    assert result["success"] is True
    assert mock_exec.call_args is not None
    command = mock_exec.call_args[0][0]
    assert command == [
        "ansible-creator",
        "init",
        "playbook",
        "--no-overwrite",
        "acme.site",
    ]


def test_define_and_build_execution_env_writes_file(tmp_path: Path) -> None:
    result = define_and_build_execution_env(
        tmp_path,
        base_image="quay.io/fedora/fedora-minimal:41",
        tag="my-ee:latest",
        destination_path=".",
        collections=["ansible.posix"],
        system_packages=["git"],
        python_packages=["boto3"],
        generated_yaml=(
            "version: 3\n"
            "images:\n"
            "  base_image:\n"
            "    name: quay.io/fedora/fedora-minimal:41\n"
        ),
    )

    assert result["success"] is True
    assert result["mode"] == "generated"
    written_file = tmp_path / "execution-environment.yml"
    assert written_file.exists()
    assert "ansible-builder build" in result["buildCommand"]


def test_define_and_build_execution_env_requires_base_image_and_tag(tmp_path: Path) -> None:
    result = define_and_build_execution_env(
        tmp_path,
        base_image=None,
        tag="",
        destination_path=None,
        collections=None,
        system_packages=None,
        python_packages=None,
        generated_yaml=None,
    )

    assert result["success"] is False
    assert "required fields" in result["output"]


async def test_run_ansible_navigator_information_mode(tmp_path: Path) -> None:
    result = await run_ansible_navigator(
        tmp_path,
        user_message=None,
        file_path=None,
        mode=None,
        disable_execution_environment=False,
        environment=None,
    )

    assert result["success"] is True
    assert result["mode"] == "information"
    assert "Features & Usage Guide" in result["output"]


async def test_run_ansible_navigator_execution_mode(tmp_path: Path) -> None:
    playbook_path = tmp_path / "playbooks" / "site.yml"
    playbook_path.parent.mkdir(parents=True, exist_ok=True)
    playbook_path.write_text("- hosts: localhost\n", encoding="utf-8")

    mock_exec = AsyncMock(return_value=_exec_result(status="success", stdout="navigator ok"))
    with (
        patch(
            "ansible_mcp.upstream_tools._resolve_navigator_path",
            return_value=("/usr/bin/ansible-navigator", None),
        ),
        patch("ansible_mcp.upstream_tools.exec_command", new=mock_exec),
    ):
        result = await run_ansible_navigator(
            tmp_path,
            user_message="run site",
            file_path=None,
            mode=None,
            disable_execution_environment=False,
            environment="auto",
        )

    assert result["success"] is True
    assert "navigator ok" in result["output"]
    assert mock_exec.call_args is not None
    command = mock_exec.call_args[0][0]
    assert command[0] == "/usr/bin/ansible-navigator"
    assert command[1] == "run"
    assert command[2].endswith("playbooks/site.yml")
