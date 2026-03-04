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

## Upstream vs standalone (this project)

| Area | VS Code Ansible MCP (upstream model) | `ansible-mcp` (this repo) |
|---|---|---|
| Packaging | Coupled to extension/monorepo workflows | Standalone Python package (`ansible-mcp`) |
| Client scope | Primarily VS Code/Copilot flows | Any MCP-compatible client (VS Code, Claude, Cursor, CLI, etc.) |
| Transport | Typically extension-managed STDIO | STDIO, Streamable HTTP, SSE |
| Tool architecture | Extension-shaped integration | Plugin router + entry-point based expansion |
| Token strategy | More verbose tool metadata by default | Compact tool descriptions + capped/truncated responses |
| Docs delivery | Mostly extension/context-driven docs | MCP resources (`ansible://docs/*`) on demand |

### Token efficiency targets

- Tool description budget: `< 60` tokens per tool
- `tools/list` total budget target: `< 800` tokens
- Per-tool response budget target: `< 500` tokens (before truncation markers)

These budgets are enforced through `TokenBudget` and formatting/truncation helpers in the server runtime.

## Roadmap: add remaining tool families

Current server scope is MVP. The remaining planned tool families are below.

### Phase 1 — CLI-first plugins (next)

- **Galaxy**: search/install/info/init collection or role scaffolding
- **Molecule**: init/test/converge/destroy
- **Vault**: encrypt/decrypt/view/rekey with strict path and secret handling

### Phase 2 — Controller/API plugins

- **AAP (Automation Controller)**: list templates, launch jobs, monitor job status, inventory operations

### Phase 3 — Advanced execution tooling

- **Execution Environments**: build/inspect flows (for ansible-builder based workflows)
- **Navigator**: run/inventory/artifact-oriented tool surface

### Definition of done for each new plugin/tool

1. Tool schema and compact description added to plugin metadata
2. Unit tests for argument validation and result shaping
3. Integration tests against real backend executable/API
4. MCP resource docs added under `ansible://docs/*`
5. Token budgets respected in tool listing and responses
6. Included in CI lanes (quality, unit, integration)

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

## Pre-commit hooks

Install the shared hooks once per clone:

```bash
uv run --extra dev pre-commit install --hook-type pre-commit --hook-type pre-push
```

What runs automatically:

- `pre-commit`: `ruff`, `mypy`, and `tests/unit`
- `pre-push`: `tests/integration -m integration`

Run all hooks manually:

```bash
uv run --extra dev pre-commit run --all-files
uv run --extra dev pre-commit run --all-files --hook-stage pre-push
```

## Notes

- Tool descriptions are intentionally compact for token efficiency.
- Detailed docs are available as MCP resources:
  - `ansible://docs/lint`
  - `ansible://docs/playbook`
  - `ansible://docs/inventory`

## Developer guidelines

- Use Python 3.11+ and `uv` for dependency and environment management.
- Keep tool descriptions compact and schema-first.
- Return structured outputs; avoid unbounded free-text payloads.
- Keep subprocess execution safe (`create_subprocess_exec`, no `shell=True`).
- Add tests for every new tool path (unit + integration).
- Keep client-agnostic behavior: no VS Code-only assumptions in core runtime.

## License

MIT (declared in `pyproject.toml`).
