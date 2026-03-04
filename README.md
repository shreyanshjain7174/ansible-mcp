# ansible-mcp

Standalone MCP server for Ansible tooling (lint, playbook operations, inventory parsing) with plugin-based routing and token-aware responses.

## Install from package index (standalone)

After first release to PyPI, install directly with:

```bash
uv tool install ansible-mcp
# or
pip install ansible-mcp
```

Run:

```bash
ansible-mcp serve --stdio
```

## Install from source (development)

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

## Requirements files

This project uses `pyproject.toml` as the dependency source of truth.

For teams/tools that expect pip-style requirement files, optional exports are included:

- `requirements.txt` (runtime)
- `requirements-dev.txt` (development)

Install with pip if needed:

```bash
pip install -r requirements.txt
# or
pip install -r requirements-dev.txt
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

## Upstream-compatible tools (parity track)

- `list_available_tools` — list upstream endpoints and current availability
- `zen_of_ansible` — upstream philosophy endpoint
- `ansible_content_best_practices` — upstream guidance endpoint
- `ansible_lint` — upstream-compatible wrapper (mapped to `lint`)
- `ade_environment_info` — environment diagnostics endpoint
- `ade_setup_environment` — development environment setup endpoint
- `adt_check_env` — ADT check/install endpoint
- `ansible_create_playbook` — playbook project scaffold endpoint
- `ansible_create_collection` — collection project scaffold endpoint
- `define_and_build_execution_env` — execution environment definition endpoint
- `ansible_navigator` — navigator execution/info endpoint

Detailed parity status is available at `ansible://docs/upstream-parity`.

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

## Roadmap: upstream parity first

Before adding non-upstream capabilities, this project will complete parity with
the current upstream endpoint surface.

### Phase 1 — upstream endpoint parity (completed)

- `zen_of_ansible` ✅
- `ansible_content_best_practices` ✅
- `list_available_tools` ✅
- `ansible_lint` ✅ (mapped to local `lint`)
- `ade_environment_info` ✅
- `ade_setup_environment` ✅
- `adt_check_env` ✅
- `ansible_create_playbook` ✅
- `ansible_create_collection` ✅
- `define_and_build_execution_env` ✅
- `ansible_navigator` ✅

With parity complete, additional standalone-only tool families can be layered in without changing upstream-compatible contracts.

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

## Publish to PyPI

This repo includes `.github/workflows/publish.yml` for package publishing.

### One-time setup

1. In PyPI and TestPyPI, create the `ansible-mcp` project (or reserve the name).
2. Configure Trusted Publishing for this GitHub repository and workflow.

### Publish flow

- Manual test publish: run **Publish Package** workflow with `repository=testpypi`.
- Production publish: push a version tag (for example `v0.1.1`) to trigger PyPI publish.

```bash
git tag v0.1.1
git push origin v0.1.1
```

## Notes

- Tool descriptions are intentionally compact for token efficiency.
- Detailed docs are available as MCP resources:
  - `ansible://docs/lint`
  - `ansible://docs/playbook`
  - `ansible://docs/inventory`
  - `ansible://docs/environment`
  - `ansible://docs/project-generators`
  - `ansible://docs/execution-environment`
  - `ansible://docs/navigator`
  - `schema://execution-environment`
  - `sample://execution-environment`
  - `rules://execution-environment`
  - `guidelines://ansible-content-best-practices`

## Developer guidelines

- Use Python 3.12+ and `uv` for dependency and environment management.
- Keep tool descriptions compact and schema-first.
- Return structured outputs; avoid unbounded free-text payloads.
- Keep subprocess execution safe (`create_subprocess_exec`, no `shell=True`).
- Add tests for every new tool path (unit + integration).
- Keep client-agnostic behavior: no VS Code-only assumptions in core runtime.

## License

MIT (declared in `pyproject.toml`).
