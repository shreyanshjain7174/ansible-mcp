from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from ansible_mcp.context import detect_workspace
from ansible_mcp.plugins import resolve_executable
from ansible_mcp.plugins.inventory import InventoryPlugin
from ansible_mcp.plugins.lint import LintPlugin
from ansible_mcp.plugins.playbook import PlaybookPlugin
from ansible_mcp.token_budget import TokenBudget

pytestmark = pytest.mark.integration

FIXTURE_RELATIVE_PATHS = {
    "sample_playbook": Path("tests/fixtures/sample_playbook.yml"),
    "bad_playbook": Path("tests/fixtures/bad_playbook.yml"),
    "broken_syntax": Path("tests/fixtures/broken_syntax.yml"),
    "inventory": Path("tests/fixtures/inventory.ini"),
}

REQUIRED_EXECUTABLES = (
    "ansible-lint",
    "ansible-playbook",
    "ansible-inventory",
)


def _fixture_path(name: str) -> str:
    return FIXTURE_RELATIVE_PATHS[name].as_posix()


def _assert_status(result_status: str, expected: str, label: str) -> None:
    assert result_status == expected, (
        f"{label} expected {expected!r}, got {result_status!r}"
    )


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def source_fixtures(repo_root: Path) -> Path:
    return repo_root / "tests" / "fixtures"


@pytest.fixture
def fixture_workspace(tmp_path: Path, source_fixtures: Path) -> Path:
    copied_fixtures = tmp_path / "tests" / "fixtures"
    copied_fixtures.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_fixtures, copied_fixtures)
    return tmp_path


@pytest.fixture(scope="module")
def require_real_ansible_tools(repo_root: Path) -> None:
    missing: list[str] = []
    env = dict(os.environ)

    for executable in REQUIRED_EXECUTABLES:
        resolution = resolve_executable(executable, cwd=repo_root, env=env)
        if resolution.resolved is None:
            missing.append(executable)

    if missing:
        pytest.skip(
            "Missing required executables for real integration tests: "
            + ", ".join(missing)
        )


@pytest.fixture
def token_budget() -> TokenBudget:
    return TokenBudget()


async def test_lint_plugin_real_calls(
    require_real_ansible_tools: None,
    fixture_workspace: Path,
    token_budget: TokenBudget,
) -> None:
    plugin = LintPlugin(detect_workspace(fixture_workspace), token_budget)

    good = await plugin.handle_tool_call(
        "lint", {"path": _fixture_path("sample_playbook")}
    )
    _assert_status(good.status, "success", "lint good playbook")

    bad = await plugin.handle_tool_call(
        "lint", {"path": _fixture_path("bad_playbook")}
    )
    _assert_status(bad.status, "failed", "lint bad playbook")


async def test_lint_plugin_real_calls_hostile_env(
    require_real_ansible_tools: None,
    fixture_workspace: Path,
    token_budget: TokenBudget,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", "/var/empty")
    monkeypatch.setenv("XDG_CACHE_HOME", "/var/empty")
    monkeypatch.setenv("ANSIBLE_HOME", "/var/empty")

    plugin = LintPlugin(detect_workspace(fixture_workspace), token_budget)

    good = await plugin.handle_tool_call(
        "lint", {"path": _fixture_path("sample_playbook")}
    )
    _assert_status(good.status, "success", "lint good playbook hostile env")
    assert "PermissionError" not in good.payload.get("stderr", "")


async def test_playbook_plugin_real_calls(
    require_real_ansible_tools: None,
    fixture_workspace: Path,
    token_budget: TokenBudget,
) -> None:
    plugin = PlaybookPlugin(detect_workspace(fixture_workspace), token_budget)

    syntax_ok = await plugin.handle_tool_call(
        "playbook_syntax_check",
        {"playbook_path": _fixture_path("sample_playbook")},
    )
    _assert_status(syntax_ok.status, "success", "syntax-check good playbook")

    syntax_bad = await plugin.handle_tool_call(
        "playbook_syntax_check",
        {"playbook_path": _fixture_path("broken_syntax")},
    )
    _assert_status(syntax_bad.status, "failed", "syntax-check broken playbook")

    dry_run = await plugin.handle_tool_call(
        "playbook_run",
        {
            "playbook_path": _fixture_path("sample_playbook"),
            "check": True,
        },
    )
    _assert_status(dry_run.status, "success", "dry-run playbook")


async def test_inventory_plugin_real_calls(
    require_real_ansible_tools: None,
    fixture_workspace: Path,
    token_budget: TokenBudget,
) -> None:
    plugin = InventoryPlugin(detect_workspace(fixture_workspace), token_budget)

    parsed = await plugin.handle_tool_call(
        "inventory_parse",
        {"inventory_path": _fixture_path("inventory")},
    )
    _assert_status(parsed.status, "success", "inventory parse")

    graphed = await plugin.handle_tool_call(
        "inventory_graph",
        {"inventory_path": _fixture_path("inventory")},
    )
    _assert_status(graphed.status, "success", "inventory graph")
