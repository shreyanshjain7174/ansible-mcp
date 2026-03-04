from __future__ import annotations

from ansible_mcp.upstream import upstream_tool_catalog, upstream_tool_names


def test_upstream_tool_names_count_and_order() -> None:
    names = upstream_tool_names()
    assert len(names) == 11
    assert names[:4] == [
        "zen_of_ansible",
        "ansible_content_best_practices",
        "list_available_tools",
        "ansible_lint",
    ]


def test_upstream_catalog_marks_wrapped_lint_available() -> None:
    catalog = upstream_tool_catalog(
        {"lint", "playbook_run"},
        {
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
        },
    )
    as_map = {row["name"]: row for row in catalog}

    assert as_map["ansible_lint"]["available"] is True
    assert as_map["ansible_lint"]["mapped_to"] == "lint"
    assert as_map["ansible_lint"]["status"] == "implemented"


def test_upstream_catalog_marks_lint_planned_when_router_tool_missing() -> None:
    catalog = upstream_tool_catalog(
        set(),
        {
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
        },
    )
    as_map = {row["name"]: row for row in catalog}

    assert as_map["ansible_lint"]["available"] is False
    assert as_map["ansible_lint"]["status"] == "planned"
    assert as_map["ade_environment_info"]["available"] is True
    assert as_map["ade_environment_info"]["status"] == "implemented"
