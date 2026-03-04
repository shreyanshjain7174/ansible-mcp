# ansible-mcp

Standalone MCP server for Ansible tooling (lint, playbook operations, inventory parsing) with plugin-based routing and token-aware responses.

## Install

```bash
cd /Users/sunny/Ansible/ansible-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run (stdio)

```bash
ansible-mcp serve --stdio
```

## VS Code MCP config (project)

Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "ansible-mcp": {
      "command": "ansible-mcp",
      "args": ["serve", "--stdio"],
      "type": "stdio",
      "env": {
        "WORKSPACE_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

## Current tools (MVP)

- `lint` — run `ansible-lint` on a file/directory
- `playbook_syntax_check` — run `ansible-playbook --syntax-check`
- `playbook_run` — run `ansible-playbook`
- `inventory_parse` — run `ansible-inventory --list`
- `inventory_graph` — run `ansible-inventory --graph`

## Tests

- Fast unit lane:

  ```bash
  pytest tests/unit -v --tb=short
  ```

- Integration lane (real Ansible executables):

  ```bash
  pytest tests/integration -v --tb=short -m integration
  ```

Integration tests require `ansible-lint`, `ansible-playbook`, and
`ansible-inventory`. Tests are skipped automatically when required executables
are missing.

## Notes

- Tool descriptions are intentionally compact for token efficiency.
- Detailed docs are available as MCP resources:
  - `ansible://docs/lint`
  - `ansible://docs/playbook`
  - `ansible://docs/inventory`
