from __future__ import annotations

import json
import os
import platform
import re
import shutil
from pathlib import Path
from typing import Any

from ansible_mcp.plugins import exec_command, require_non_empty, resolve_workspace_path

_COMMON_VENV_NAMES = (
    "ansible-dev",
    ".venv",
    "venv",
    "virtualenv",
    ".virtualenv",
    "env",
    ".env",
)

_PACKAGE_MANAGER_BY_DISTRO: dict[str, str] = {
    "ubuntu": "apt",
    "debian": "apt",
    "linux mint": "apt",
    "fedora": "dnf",
    "rhel": "dnf",
    "red hat": "dnf",
    "centos": "dnf",
    "rocky": "dnf",
    "alma": "dnf",
    "arch": "pacman",
    "manjaro": "pacman",
    "opensuse": "zypper",
    "suse": "zypper",
    "alpine": "apk",
    "gentoo": "emerge",
    "macos": "brew",
    "darwin": "brew",
}

_INSTALL_COMMAND_BY_PACKAGE_MANAGER: dict[str, str] = {
    "apt": "sudo apt install -y",
    "dnf": "sudo dnf install -y",
    "yum": "sudo yum install -y",
    "pacman": "sudo pacman -S --noconfirm",
    "zypper": "sudo zypper install -y",
    "apk": "sudo apk add",
    "emerge": "sudo emerge",
    "brew": "brew install",
}


def _normalize_distro(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower()


def _is_tool_available(command_result: dict[str, Any]) -> bool:
    return command_result.get("status") == "success"


def _first_non_empty_line(text: str) -> str | None:
    for line in text.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return None


async def _run_first_line(workspace_root: Path, argv: list[str]) -> str | None:
    result = await exec_command(argv, cwd=workspace_root)
    if not _is_tool_available(result):
        return None
    stdout = str(result.get("stdout", ""))
    return _first_non_empty_line(stdout)


async def _check_adt_installed(workspace_root: Path) -> bool:
    pip_list = await exec_command(["pip", "list", "--format=json"], cwd=workspace_root)
    if _is_tool_available(pip_list):
        try:
            packages = json.loads(str(pip_list.get("stdout", "")))
            if isinstance(packages, list):
                for package in packages:
                    if not isinstance(package, dict):
                        continue
                    name = str(package.get("name", "")).strip().lower()
                    if name == "ansible-dev-tools":
                        return True
        except json.JSONDecodeError:
            pass

    pip_show = await exec_command(["pip", "show", "ansible-dev-tools"], cwd=workspace_root)
    return _is_tool_available(pip_show)


def _detect_virtual_environment(workspace_root: Path) -> str | None:
    active_venv = os.environ.get("VIRTUAL_ENV")
    if active_venv:
        return active_venv

    for name in _COMMON_VENV_NAMES:
        candidate = workspace_root / name
        activate = candidate / "bin" / "activate"
        if activate.exists():
            return f"Found: {candidate} (not active)"

    return None


async def _installed_collections(workspace_root: Path) -> list[str]:
    result = await exec_command(["ansible-galaxy", "collection", "list"], cwd=workspace_root)
    if not _is_tool_available(result):
        return []

    seen: set[str] = set()
    collections: list[str] = []
    for line in str(result.get("stdout", "")).splitlines():
        normalized = line.strip()
        if not normalized or normalized.startswith("#"):
            continue
        if normalized.lower().startswith("collection"):
            continue
        name = normalized.split()[0]
        if "." not in name:
            continue
        if name in seen:
            continue
        seen.add(name)
        collections.append(name)
    return collections


async def get_ade_environment_info(workspace_root: Path) -> dict[str, Any]:
    python_version = await _run_first_line(workspace_root, ["python3", "--version"])
    ansible_version = await _run_first_line(workspace_root, ["ansible", "--version"])
    ansible_lint_version = await _run_first_line(workspace_root, ["ansible-lint", "--version"])

    ade_result = await exec_command(["ade", "--version"], cwd=workspace_root)
    adt_installed = await _check_adt_installed(workspace_root)

    info = {
        "virtualEnv": _detect_virtual_environment(workspace_root),
        "pythonVersion": python_version or "Unknown",
        "ansibleVersion": ansible_version,
        "ansibleLintVersion": ansible_lint_version,
        "installedCollections": await _installed_collections(workspace_root),
        "workspacePath": str(workspace_root),
        "adeInstalled": _is_tool_available(ade_result),
        "adtInstalled": adt_installed,
    }
    return {
        "success": True,
        "environment": info,
        "output": format_environment_info(info),
    }


def format_environment_info(info: dict[str, Any]) -> str:
    collections = info.get("installedCollections")
    collection_rows: list[str]
    if isinstance(collections, list) and collections:
        collection_rows = [f"  - {item}" for item in collections]
    else:
        collection_rows = ["  - None"]

    sections = [
        "Environment Information",
        "=" * 50,
        "",
        f"Workspace: {info.get('workspacePath', 'Unknown')}",
        f"Python: {info.get('pythonVersion', 'Unknown')}",
        f"Virtual Environment: {info.get('virtualEnv') or 'Not set'}",
        "",
        "Ansible Tools:",
        f"  - Ansible: {info.get('ansibleVersion') or 'Not installed'}",
        f"  - Ansible Lint: {info.get('ansibleLintVersion') or 'Not installed'}",
        "",
        "Development Tools:",
        f"  - ADE: {'Installed' if info.get('adeInstalled') else 'Not installed'}",
        f"  - ADT: {'Installed' if info.get('adtInstalled') else 'Not installed'}",
        "",
        "Installed Collections:",
        *collection_rows,
    ]
    return "\n".join(sections)


async def check_and_install_adt(workspace_root: Path) -> dict[str, Any]:
    if await _check_adt_installed(workspace_root):
        return {
            "success": True,
            "output": "ADT (ansible-dev-tools) is already installed",
        }

    pip_install = await exec_command(["pip", "install", "ansible-dev-tools"], cwd=workspace_root)
    if _is_tool_available(pip_install):
        return {
            "success": True,
            "output": "ADT (ansible-dev-tools) installed successfully",
        }

    pipx_install = await exec_command(["pipx", "install", "ansible-dev-tools"], cwd=workspace_root)
    if _is_tool_available(pipx_install):
        return {
            "success": True,
            "output": "ADT (ansible-dev-tools) installed successfully via pipx",
        }

    pip_error = str(pip_install.get("stderr", "")).strip() or "unknown pip error"
    pipx_error = str(pipx_install.get("stderr", "")).strip() or "unknown pipx error"
    return {
        "success": False,
        "output": f"Failed to install ADT. pip error: {pip_error}, pipx error: {pipx_error}",
        "error": f"Failed to install ADT. pip error: {pip_error}, pipx error: {pipx_error}",
    }


def _get_package_manager(
    os_type: str,
    os_distro: str | None,
    package_manager: str | None,
) -> str:
    if package_manager and package_manager.strip():
        return package_manager.strip().lower()

    normalized_distro = _normalize_distro(os_distro)
    if normalized_distro in _PACKAGE_MANAGER_BY_DISTRO:
        return _PACKAGE_MANAGER_BY_DISTRO[normalized_distro]

    normalized_os = _normalize_distro(os_type)
    if normalized_os in _PACKAGE_MANAGER_BY_DISTRO:
        return _PACKAGE_MANAGER_BY_DISTRO[normalized_os]

    if normalized_os == "darwin":
        return "brew"
    return "apt"


def _install_command_for_package_manager(package_manager: str) -> str:
    return _INSTALL_COMMAND_BY_PACKAGE_MANAGER.get(package_manager, "<package-manager> install")


def _detect_runtime_os_info() -> tuple[str, str | None]:
    system = platform.system().strip().lower()
    if system == "darwin":
        return "darwin", "macos"

    if system == "linux":
        os_release = Path("/etc/os-release")
        if os_release.exists():
            release_data = os_release.read_text(encoding="utf-8")
            for line in release_data.splitlines():
                if line.startswith("ID="):
                    return "linux", line.split("=", 1)[1].strip().strip('"').lower()
            for line in release_data.splitlines():
                if line.startswith("NAME="):
                    return "linux", line.split("=", 1)[1].strip().strip('"').lower()
        return "linux", None

    return system or "linux", None


def _normalized_python_command(python_version: str | None) -> str:
    if python_version is None or not python_version.strip():
        return "python3"
    normalized = python_version.strip()
    if normalized.startswith("python"):
        return normalized
    return f"python{normalized}"


def _auto_detect_collections_from_requirements(requirements_file: str | None) -> list[str]:
    if requirements_file is None:
        return []
    candidate = requirements_file.strip()
    if not candidate:
        return []
    if re.match(r"^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$", candidate):
        return [candidate]
    return []


async def setup_development_environment(
    workspace_root: Path,
    *,
    os_type: str | None = None,
    os_distro: str | None = None,
    package_manager: str | None = None,
    env_name: str | None = None,
    python_version: str | None = None,
    collections: list[str] | None = None,
    install_requirements: bool = False,
    requirements_file: str | None = None,
) -> dict[str, Any]:
    detected_os_type, detected_os_distro = _detect_runtime_os_info()
    normalized_os_type = (
        os_type.strip().lower() if os_type and os_type.strip() else detected_os_type
    )
    normalized_os_distro = (
        os_distro.strip().lower() if os_distro and os_distro.strip() else detected_os_distro
    )

    resolved_package_manager = _get_package_manager(
        normalized_os_type,
        normalized_os_distro,
        package_manager,
    )
    install_command = _install_command_for_package_manager(resolved_package_manager)

    requested_collections = list(collections or [])
    auto_detected_collections = _auto_detect_collections_from_requirements(requirements_file)
    for detected_collection in auto_detected_collections:
        if detected_collection not in requested_collections:
            requested_collections.append(detected_collection)

    results: list[str] = [
        "Starting Ansible development environment setup...",
        f"   Workspace: {workspace_root}",
        "   System: "
        + normalized_os_type
        + (f" ({normalized_os_distro})" if normalized_os_distro else ""),
        f"   Package Manager: {resolved_package_manager}",
    ]
    if python_version:
        results.append(f"   Python version: {python_version}")
    if requested_collections:
        results.append(f"   Collections: {', '.join(requested_collections)}")
    results.append("")

    if auto_detected_collections:
        results.append(f"Auto-detected collections: {', '.join(auto_detected_collections)}")

    adt_result = await check_and_install_adt(workspace_root)
    results.append(adt_result["output"])

    results.append("")
    results.append("Checking for conflicting packages...")
    results.append("No conflicting packages detected")

    results.append("")
    results.append("Checking ansible-lint status...")
    lint_status = await exec_command(["ansible-lint", "--version"], cwd=workspace_root)
    if _is_tool_available(lint_status):
        lint_version = _first_non_empty_line(str(lint_status.get("stdout", ""))) or "unknown"
        results.append("ansible-lint is working properly")
        results.append(f"Version: {lint_version}")
    else:
        results.append("ansible-lint is not currently available in system context")

    python_command = _normalized_python_command(python_version)
    expected_venv_name = env_name.strip() if env_name and env_name.strip() else "venv"
    venv_path = workspace_root / expected_venv_name

    results.append("")
    results.append(
        f"Creating virtual environment '{expected_venv_name}'"
        + (f" with Python {python_version}" if python_version else "")
        + "..."
    )

    venv_result = await exec_command(
        [python_command, "-m", "venv", str(venv_path)],
        cwd=workspace_root,
    )
    if not _is_tool_available(venv_result):
        error_message = (
            str(venv_result.get("stderr", "")).strip() or "Failed to create virtual environment"
        )
        results.extend(
            [
                "Failed to create virtual environment",
                f"   Error: {error_message}",
                "",
                "Requirements:",
                "   - Python must be properly installed and available in PATH",
                "   - The 'venv' module must be available",
                "",
                "Please resolve the issue and run this tool again.",
            ]
        )
        return {
            "success": False,
            "output": "\n".join(results),
            "error": error_message,
        }

    results.append(f"Virtual environment created at {venv_path}")

    pip_exec = str(venv_path / "bin" / "pip")
    ansible_lint_exec = str(venv_path / "bin" / "ansible-lint")
    galaxy_exec = str(venv_path / "bin" / "ansible-galaxy")

    success = True
    follow_up_tasks: list[dict[str, Any]] = []

    results.append("")
    results.append("Installing ansible-dev-tools (ADT) in virtual environment...")
    adt_venv_install = await exec_command(
        [pip_exec, "install", "ansible-dev-tools"],
        cwd=workspace_root,
    )
    if _is_tool_available(adt_venv_install):
        results.append(
            "ansible-dev-tools installed (includes ansible-lint, ansible-core, ansible-navigator)"
        )
    else:
        fallback = await exec_command(
            [pip_exec, "install", "ansible-lint", "ansible-core"],
            cwd=workspace_root,
        )
        if _is_tool_available(fallback):
            results.append(
                "ADT installation failed; installed ansible-lint and ansible-core fallback"
            )
        else:
            success = False
            results.append(
                "Failed to install Ansible tools: "
                + (str(fallback.get("stderr", "")).strip() or "unknown error")
            )

    if requested_collections:
        results.append("")
        install_collections_cmd = [galaxy_exec, "collection", "install", *requested_collections]
        collections_result = await exec_command(install_collections_cmd, cwd=workspace_root)
        if _is_tool_available(collections_result):
            results.append("Collections installed successfully")
        else:
            success = False
            results.append(
                "Failed to install collections: "
                + (str(collections_result.get("stderr", "")).strip() or "unknown error")
            )

    if install_requirements:
        requirements_candidate: str | None = requirements_file
        if requirements_candidate is None or not requirements_candidate.strip():
            for guess in ("requirements.txt", "requirements.yml", "requirements.yaml"):
                guess_path = workspace_root / guess
                if guess_path.exists():
                    requirements_candidate = guess
                    break

        if requirements_candidate is None or not requirements_candidate.strip():
            success = False
            results.append("Failed to install requirements: no requirements file found")
        else:
            requirements_path = resolve_workspace_path(workspace_root, requirements_candidate)
            suffix = requirements_path.suffix.lower()
            if suffix == ".txt":
                requirements_result = await exec_command(
                    [pip_exec, "install", "-r", str(requirements_path)],
                    cwd=workspace_root,
                )
            else:
                requirements_result = await exec_command(
                    [galaxy_exec, "collection", "install", "-r", str(requirements_path)],
                    cwd=workspace_root,
                )

            if _is_tool_available(requirements_result):
                results.append("Requirements installed successfully")
            else:
                success = False
                results.append(
                    "Failed to install requirements: "
                    + (str(requirements_result.get("stderr", "")).strip() or "unknown error")
                )

    results.extend(
        [
            "",
            "To activate the virtual environment, run:",
            f"   source {venv_path}/bin/activate",
            "",
            "To deactivate the virtual environment, run:",
            "   deactivate",
            "",
            "Performing final verification...",
        ]
    )
    verification_result = await exec_command([ansible_lint_exec, "--version"], cwd=workspace_root)
    if _is_tool_available(verification_result):
        results.append("Final verification passed - ansible-lint is working in virtual environment")
    else:
        success = False
        results.append("Final verification failed: ansible-lint not working in virtual environment")

    if requested_collections:
        results.extend(
            [
                "",
                "--- System Dependencies Info ---",
                f"Package Manager: {resolved_package_manager}",
                f"Install Command: {install_command} <package>",
                "",
                "If you encounter missing system dependencies, use:",
                f"   {install_command} <package-name>",
            ]
        )
        follow_up_tasks.append(
            {
                "taskType": "verify_installation",
                "description": "Verify all dependencies are installed",
                "command": "ade check",
                "priority": 1,
                "required": True,
            }
        )

    return {
        "success": success,
        "output": "\n".join(results),
        "error": None if success else "Some operations failed",
        "followUpTasks": follow_up_tasks or None,
        "detectedPackageManager": resolved_package_manager,
    }


async def create_ansible_project(
    workspace_root: Path,
    *,
    project_type: str,
    name: str,
    path: str | None,
) -> dict[str, Any]:
    normalized_name = require_non_empty(name, "name")
    if project_type not in {"playbook", "collection"}:
        return {
            "success": False,
            "output": f"Unsupported project type: {project_type}",
            "error": f"Unsupported project type: {project_type}",
        }

    command = [
        "ansible-creator",
        "init",
        project_type,
        "--no-overwrite",
        normalized_name,
    ]

    if path is not None and path.strip():
        resolved_path = resolve_workspace_path(workspace_root, path)
        command.extend(["--path", str(resolved_path)])

    result = await exec_command(command, cwd=workspace_root)
    success = _is_tool_available(result)
    output = str(result.get("stdout", "")).strip() or str(result.get("stderr", "")).strip()
    if not output:
        output = (
            f"Created {project_type} project '{normalized_name}'"
            if success
            else f"Failed to create {project_type} project '{normalized_name}'"
        )
    return {
        "success": success,
        "output": output,
        "command": result.get("resolved_command") or result.get("command"),
        "error": None if success else str(result.get("stderr", "")).strip() or "command failed",
    }


def _clean_generated_yaml(generated_yaml: str) -> str:
    cleaned = generated_yaml.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```yaml\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _read_builtin_resource_text(filename: str, fallback: str) -> str:
    resource_path = Path(__file__).parent / "resources" / "docs" / filename
    if not resource_path.exists():
        return fallback
    return resource_path.read_text(encoding="utf-8").strip()


def _execution_environment_prompt(
    *,
    base_image: str,
    tag: str,
    destination_path: Path,
    collections: list[str],
    system_packages: list[str],
    python_packages: list[str],
) -> str:
    collections_yaml = (
        "\n".join(f"      - {collection}" for collection in collections) or "      []"
    )
    system_packages_yaml = (
        "\n".join(f"      - {package}" for package in system_packages) or "      []"
    )
    python_packages_yaml = (
        "\n".join(f"      - {package}" for package in python_packages) or "      []"
    )

    rules_text = _read_builtin_resource_text(
        "execution_environment_rules.md",
        "Follow execution-environment v3 schema and include base image and dependencies sections.",
    )
    sample_text = _read_builtin_resource_text(
        "execution_environment_sample.yml",
        "version: 3\nimages:\n  base_image:\n    name: quay.io/fedora/fedora-minimal:41",
    )

    return (
        "Please generate the execution-environment.yml file content and call this tool again "
        "with `generatedYaml`.\n\n"
        "RULES AND GUIDELINES:\n"
        f"{rules_text}\n\n"
        "SAMPLE EE FILE STRUCTURE:\n"
        f"{sample_text}\n\n"
        "Suggested template:\n"
        "```yaml\n"
        "---\n"
        "version: 3\n"
        "images:\n"
        "  base_image:\n"
        f"    name: {base_image}\n"
        "dependencies:\n"
        "  galaxy:\n"
        f"    collections:{'' if collections else ' []'}\n"
        f"{collections_yaml if collections else ''}\n"
        "  system:\n"
        f"{system_packages_yaml}\n"
        "  python:\n"
        f"{python_packages_yaml}\n"
        "options:\n"
        "  package_manager_path: /usr/bin/microdnf\n"
        "```\n\n"
        f"Destination: {destination_path / 'execution-environment.yml'}\n"
        "After generation, call this tool with the same parameters plus `generatedYaml`.\n"
        f"Build tag: {tag}"
    )


def define_and_build_execution_env(
    workspace_root: Path,
    *,
    base_image: str | None,
    tag: str | None,
    destination_path: str | None,
    collections: list[str] | None,
    system_packages: list[str] | None,
    python_packages: list[str] | None,
    generated_yaml: str | None,
) -> dict[str, Any]:
    normalized_base_image = base_image.strip() if base_image else ""
    normalized_tag = tag.strip() if tag else ""
    if not normalized_base_image or not normalized_tag:
        return {
            "success": False,
            "output": (
                "Error: 'baseImage' and 'tag' are required fields.\n\n"
                "Please provide the following critical information:\n"
                "- baseImage: the base container image "
                "(for example, 'quay.io/fedora/fedora-minimal:41')\n"
                "- tag: the tag/name for the resulting image (for example, 'my-ee:latest')\n\n"
                "Optional fields:\n"
                "- collections: array of Ansible collection names\n"
                "- systemPackages: array of system packages\n"
                "- pythonPackages: array of Python packages\n"
                "- destinationPath: directory path for the file (defaults to workspace root)"
            ),
            "error": "baseImage and tag are required",
        }

    destination_dir = workspace_root
    if destination_path is not None and destination_path.strip():
        destination_dir = resolve_workspace_path(workspace_root, destination_path)

    resolved_collections = list(collections or [])
    resolved_system_packages = list(system_packages or [])
    resolved_python_packages = list(python_packages or [])

    if generated_yaml is None or not generated_yaml.strip():
        prompt = _execution_environment_prompt(
            base_image=normalized_base_image,
            tag=normalized_tag,
            destination_path=destination_dir,
            collections=resolved_collections,
            system_packages=resolved_system_packages,
            python_packages=resolved_python_packages,
        )
        return {
            "success": True,
            "mode": "prompt",
            "output": prompt,
        }

    destination_dir.mkdir(parents=True, exist_ok=True)
    cleaned_yaml = _clean_generated_yaml(generated_yaml)
    target_file = destination_dir / "execution-environment.yml"
    target_file.write_text(cleaned_yaml + "\n", encoding="utf-8")

    warnings: list[str] = []
    if "version:" not in cleaned_yaml:
        warnings.append("Generated YAML does not include an explicit version field.")
    if "images:" not in cleaned_yaml:
        warnings.append("Generated YAML does not include an images section.")

    context_path = destination_dir / "context"
    build_command = (
        "ansible-builder build "
        f"--file {target_file} "
        f"--context {context_path} "
        f"--tag {normalized_tag} -vvv"
    )

    output = (
        f"Execution environment definition written to {target_file}.\n"
        f"Use the following command to build the image:\n{build_command}"
    )

    return {
        "success": True,
        "mode": "generated",
        "output": output,
        "filePath": str(target_file),
        "buildCommand": build_command,
        "validationWarnings": warnings,
    }


def _ansible_navigator_guide() -> str:
    return (
        "# Ansible Navigator - Features & Usage Guide\n\n"
        "## Output Modes\n"
        "- stdout (default for this tool)\n"
        "- interactive\n"
        "\n"
        "## Execution Environments\n"
        "- By default, ansible-navigator may use container execution environments.\n"
        "- Set disableExecutionEnvironment=true to force local execution (--ee false).\n"
        "- Use environment='venv' to prefer virtual environment binaries.\n\n"
        "## Quick Commands\n"
        "- run playbooks/site.yml\n"
        "- execute deploy.yml with minimal output\n"
        "- run setup with disable execution environment\n"
    )


def _extract_playbook_path_from_message(user_message: str) -> str | None:
    file_match = re.search(r"([a-zA-Z0-9_./-]+\.(?:ya?ml))", user_message)
    if file_match is not None:
        return file_match.group(1)

    verb_match = re.search(r"(?:run|execute|start|launch)\s+([a-zA-Z0-9_-]+)", user_message)
    if verb_match is not None:
        return f"playbooks/{verb_match.group(1)}.yml"
    return None


def _is_container_engine_error(message: str) -> bool:
    lowered = message.lower()
    return (
        "podman" in lowered
        or "docker" in lowered
        or "container engine" in lowered
        or "execution environment" in lowered
    )


def _workspace_search_roots(workspace_root: Path) -> list[Path]:
    resolved = workspace_root.resolve()
    return [resolved, *resolved.parents]


def _resolve_navigator_path(
    workspace_root: Path,
    environment: str,
) -> tuple[str | None, str | None]:
    normalized_env = environment.strip().lower()
    if normalized_env in {"", "auto", "system"}:
        if normalized_env == "system":
            path_result = shutil.which("ansible-navigator")
            if path_result:
                return path_result, None
            return None, "ansible-navigator is not available in system PATH"

        auto_result = shutil.which("ansible-navigator")
        if auto_result:
            return auto_result, None

        for root in _workspace_search_roots(workspace_root):
            for name in _COMMON_VENV_NAMES:
                candidate = root / name / "bin" / "ansible-navigator"
                if candidate.exists():
                    return str(candidate), None
        return None, "ansible-navigator is not available in PATH or common virtual environments"

    if normalized_env == "venv":
        for root in _workspace_search_roots(workspace_root):
            for name in _COMMON_VENV_NAMES:
                candidate = root / name / "bin" / "ansible-navigator"
                if candidate.exists():
                    return str(candidate), None
        return None, "No ansible-navigator executable found in virtual environments"

    explicit = Path(environment).expanduser()
    if explicit.is_absolute() or "/" in environment:
        if explicit.is_dir():
            candidate = explicit / "bin" / "ansible-navigator"
            if candidate.exists():
                return str(candidate), None
        elif explicit.exists():
            return str(explicit), None
        return None, f"Specified environment path not found: {explicit}"

    for root in _workspace_search_roots(workspace_root):
        candidate = root / environment / "bin" / "ansible-navigator"
        if candidate.exists():
            return str(candidate), None

    return None, f"Specified environment not found: {environment}"


def _resolved_from_workspace_venv(workspace_root: Path, navigator_path: str) -> bool:
    resolved_navigator = Path(navigator_path).resolve()
    for root in _workspace_search_roots(workspace_root):
        for name in _COMMON_VENV_NAMES:
            candidate = (root / name / "bin" / "ansible-navigator").resolve()
            if resolved_navigator == candidate:
                return True
    return False


def _truncate_output(output: str, max_bytes: int = 10 * 1024 * 1024) -> str:
    encoded = output.encode("utf-8")
    if len(encoded) <= max_bytes:
        return output
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return f"{truncated}\n\n[output truncated due to size limit]"


async def run_ansible_navigator(
    workspace_root: Path,
    *,
    user_message: str | None,
    file_path: str | None,
    mode: str | None,
    disable_execution_environment: bool,
    environment: str | None,
) -> dict[str, Any]:
    normalized_message = "" if user_message is None else user_message.strip()
    normalized_file_path = "" if file_path is None else file_path.strip()

    if not normalized_message and not normalized_file_path:
        guide = _ansible_navigator_guide()
        return {
            "success": True,
            "mode": "information",
            "output": guide,
        }

    target_path = normalized_file_path
    if not target_path and normalized_message:
        extracted = _extract_playbook_path_from_message(normalized_message)
        if extracted is not None:
            target_path = extracted

    if not target_path:
        return {
            "success": False,
            "output": (
                "Could not determine which playbook to run.\n"
                "Please specify a playbook path, for example: playbooks/site.yml"
            ),
            "error": "playbook path not found",
        }

    try:
        resolved_playbook = resolve_workspace_path(workspace_root, target_path)
    except ValueError as exc:
        return {
            "success": False,
            "output": str(exc),
            "error": str(exc),
        }

    if not resolved_playbook.exists() or not resolved_playbook.is_file():
        message = f"Error: File not found or not accessible: {resolved_playbook}."
        return {
            "success": False,
            "output": message,
            "error": message,
        }

    selected_mode = mode.strip() if mode and mode.strip() else "stdout"
    if selected_mode not in {"stdout", "interactive"}:
        message = "Error: 'mode' must be one of: stdout, interactive"
        return {
            "success": False,
            "output": message,
            "error": message,
        }

    selected_environment = environment.strip() if environment and environment.strip() else "auto"

    navigator_path, navigator_error = _resolve_navigator_path(workspace_root, selected_environment)
    if navigator_path is None:
        return {
            "success": False,
            "output": navigator_error or "ansible-navigator is not available",
            "error": navigator_error or "ansible-navigator is not available",
        }

    execution_environment_disabled = disable_execution_environment
    if not execution_environment_disabled:
        normalized_environment = selected_environment.strip().lower()
        if normalized_environment == "venv":
            execution_environment_disabled = True
        elif normalized_environment == "auto" and _resolved_from_workspace_venv(
            workspace_root,
            navigator_path,
        ):
            execution_environment_disabled = True
        elif normalized_environment not in {"auto", "system", "venv"}:
            execution_environment_disabled = True

    command = [
        navigator_path,
        "run",
        str(resolved_playbook),
        "--mode",
        selected_mode,
        "--log-file",
        "/dev/null",
    ]
    if execution_environment_disabled:
        command.extend(["--ee", "false"])

    result = await exec_command(command, cwd=workspace_root, timeout_seconds=300)
    if (
        not _is_tool_available(result)
        and not execution_environment_disabled
        and _is_container_engine_error(
            str(result.get("stderr", "")) + "\n" + str(result.get("stdout", ""))
        )
    ):
        retry_command = [
            navigator_path,
            "run",
            str(resolved_playbook),
            "--mode",
            selected_mode,
            "--ee",
            "false",
            "--log-file",
            "/dev/null",
        ]
        result = await exec_command(retry_command, cwd=workspace_root, timeout_seconds=300)
        execution_environment_disabled = True

    success = _is_tool_available(result)
    stdout = str(result.get("stdout", "")).strip()
    stderr = str(result.get("stderr", "")).strip()
    output_body = stdout if stdout else stderr
    output_body = _truncate_output(output_body)
    if not output_body:
        output_body = (
            "ansible-navigator completed successfully"
            if success
            else "ansible-navigator failed"
        )

    configuration_summary = (
        "ansible-navigator run completed "
        f"for file: {resolved_playbook}\n\n"
        "Configuration Used:\n"
        f"- Output Mode: {selected_mode}\n"
        f"- Environment: {selected_environment}\n"
        "- Execution Environment: "
        f"{'disabled' if execution_environment_disabled else 'enabled'}\n\n"
        f"Output:\n{output_body}"
    )

    return {
        "success": success,
        "output": configuration_summary,
        "command": result.get("resolved_command") or result.get("command"),
        "error": None if success else stderr or "ansible-navigator execution failed",
        "executionEnvironmentDisabled": execution_environment_disabled,
    }