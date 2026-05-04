# ansible-mcp

Standalone, vendor-agnostic MCP server for Ansible workflows with first-class
support for modern MCP clients (GitHub Copilot, Claude Code, Cursor).

## Requirements

- Python 3.12+
- `ansible-core` 2.20+ (installed automatically as a package dependency)
- `uv` recommended for install and execution

## One-click setup

Install once:

```bash
uv tool install ansible-mcp
```

Then configure your client in one command:

### GitHub Copilot in VS Code

```bash
ansible-mcp install --client copilot
```

### Claude Code

```bash
ansible-mcp install --client claude
```

### Cursor

```bash
ansible-mcp install --client cursor
```

For project-scoped setup (checked into your repo):

```bash
ansible-mcp install --client copilot --scope project --workspace-root .
ansible-mcp install --client cursor --scope project --workspace-root .
```

Use a custom server key in client config if needed:

```bash
ansible-mcp install --client copilot --name ansible-mcp-prod
```

## Running the server manually

Default transport (STDIO):

```bash
ansible-mcp serve --stdio
```

Streamable HTTP transport:

```bash
ansible-mcp serve --http --host 127.0.0.1 --port 8000
```

SSE transport:

```bash
ansible-mcp serve --sse --host 127.0.0.1 --port 8000
```

## Why `ansible-mcp serve --stdio` keeps the terminal open

`--stdio` runs a long-lived MCP server process. It waits for JSON-RPC messages
from your MCP client.

- This is expected.
- Press `Ctrl+C` to stop it when running manually.
- In real usage, the client launches and manages this process for you.

## Tool coverage

### Core Ansible operations

- `lint`
- `playbook_syntax_check`
- `playbook_run`
- `inventory_parse`
- `inventory_graph`

### Upstream-compatible endpoints

- `list_available_tools`
- `zen_of_ansible`
- `ansible_content_best_practices`
- `ansible_lint`
- `ade_environment_info`
- `ade_setup_environment`
- `adt_check_env`
- `ansible_create_playbook`
- `ansible_create_collection`
- `define_and_build_execution_env`
- `ansible_navigator`

Detailed parity notes: `ansible://docs/upstream-parity`

## Typical local development loop

```bash
uv run pytest tests/unit -q --tb=short
uv run pytest tests/integration -q --tb=short -m integration
```

## Upstream comparison

| Area | VS Code Ansible MCP (extension-coupled model) | ansible-mcp |
|---|---|---|
| Packaging | Coupled to extension/monorepo workflows | Standalone Python package (`ansible-mcp`) |
| Client scope | Primarily VS Code/Copilot flows | Any MCP-compatible client |
| Transport | Usually extension-managed STDIO | STDIO, Streamable HTTP, SSE |
| Tool architecture | Extension-shaped integration | Plugin router + entry-point extension model |
| Token behavior | Often more verbose metadata payloads | Compact tool descriptions and bounded responses |
| Docs access | Mostly extension context | MCP resources (`ansible://docs/*`) |

## Marketplace compatibility

For Marketplace specifics and how to ship a VS Code wrapper extension around
this server, see [docs/MARKETPLACE_COMPATIBILITY.md](docs/MARKETPLACE_COMPATIBILITY.md).

## Additional docs

- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [docs/RELEASE.md](docs/RELEASE.md)
- [PYPI_TRUSTED_PUBLISHER_SETUP.md](PYPI_TRUSTED_PUBLISHER_SETUP.md)

## License

MIT
