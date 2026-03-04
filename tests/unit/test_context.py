from pathlib import Path

from ansible_mcp.context import detect_workspace


def test_detect_workspace_flags(tmp_path: Path) -> None:
    (tmp_path / "roles").mkdir()
    (tmp_path / "playbooks").mkdir()
    (tmp_path / "playbooks" / "site.yml").write_text("- hosts: all\n", encoding="utf-8")
    (tmp_path / "inventory").mkdir()

    ctx = detect_workspace(tmp_path)

    assert ctx.has_roles is True
    assert ctx.has_playbooks is True
    assert ctx.has_inventory is True
