from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class WorkspaceContext:
    root: Path
    has_roles: bool
    has_molecule: bool
    has_playbooks: bool
    has_inventory: bool

    def has_path(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()


def _has_yaml_files(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    return any(path.glob("*.yml")) or any(path.glob("*.yaml"))


def detect_workspace(root: Path | None = None) -> WorkspaceContext:
    resolved_root = (root or Path.cwd()).expanduser().resolve()

    has_roles = (resolved_root / "roles").is_dir()
    has_molecule = (resolved_root / "molecule").is_dir()
    has_playbooks = _has_yaml_files(resolved_root) or _has_yaml_files(resolved_root / "playbooks")

    inventory_candidates = [
        resolved_root / "inventory",
        resolved_root / "inventories",
        resolved_root / "hosts.ini",
        resolved_root / "inventory.ini",
    ]
    has_inventory = any(candidate.exists() for candidate in inventory_candidates)

    return WorkspaceContext(
        root=resolved_root,
        has_roles=has_roles,
        has_molecule=has_molecule,
        has_playbooks=has_playbooks,
        has_inventory=has_inventory,
    )
