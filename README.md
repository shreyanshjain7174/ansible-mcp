# ansible-mcp

Standalone MCP server for Ansible workflows with first-class support for modern
MCP clients (GitHub Copilot, Claude Code, Cursor).

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
