---
name: ansible-mcp
description: Use this skill when working on the ansible-mcp standalone MCP server project.
---

# ansible-mcp Development Skill

## Project Context

**ansible-mcp** is a standalone, vendor-agnostic MCP server for Ansible development tooling.
- Language: Python 3.11+
- SDK: FastMCP (official Python MCP SDK)
- Package manager: uv (NOT pip)
- Package: `uv add ansible-mcp` / `uvx ansible-mcp serve`
- Repo: `github.com/ansible/ansible-mcp` (proposed)

## Architecture Quick Reference

```
Clients (Claude/Copilot/Cursor/CLI) → Transport (STDIO|HTTP|SSE)
  → Core Server (router + token_budget + context)
    → Plugin Modules (lazy-loaded via entry_points)
      → Backend (ansible-core CLI, AAP API, Galaxy API)
```

## Key Files

```
src/ansible_mcp/
├── server.py          # MCP server init, transport selection
├── router.py          # Tool registry, plugin dispatch, lazy loading
├── token_budget.py    # Token tracking, response truncation
├── context.py         # Workspace detection (roles/playbooks/molecule)
├── plugins/           # Each plugin: get_tools(), handle_tool_call()
│   ├── lint.py        # ansible-lint, yamllint, syntax-check
│   ├── playbook.py    # create, run, validate, explain
│   ├── inventory.py   # parse, query, graph
│   ├── galaxy.py      # search, install, scaffold
│   ├── aap.py         # AAP/Tower jobs, templates
│   ├── molecule.py    # test lifecycle
│   ├── vault.py       # encrypt/decrypt/rekey
│   └── ee.py          # execution environments
└── resources/docs/    # MCP resources (verbose docs served on-demand)
```

## Plugin Pattern

```python
from ansible_mcp.plugins import AnsibleMCPPlugin, Tool, ToolResult

class MyPlugin(AnsibleMCPPlugin):
    def get_tools(self) -> list[Tool]:
        return [Tool(
            name="my_tool",
            description="Short desc (<60 tokens)",  # CRITICAL: keep short
            inputSchema={...}
        )]

    async def handle_tool_call(self, name: str, args: dict) -> ToolResult:
        # Execute and return structured result
        ...

    def should_load(self, workspace) -> bool:
        # Only load if workspace has relevant files
        return workspace.has_path("molecule/")
```

Register in pyproject.toml:
```toml
[project.entry-points."ansible_mcp.plugins"]
my_plugin = "ansible_mcp.plugins.my_plugin:MyPlugin"
```

## Token Budget Rules (ENFORCED IN CI)

| Metric | Max |
|--------|-----|
| Tool description | 60 tokens |
| tools/list total | 800 tokens |
| Tool response (avg) | 500 tokens |
| Tool response (max) | 2000 tokens (with truncation notice) |

Verbose docs go into MCP resources: `ansible://docs/{topic}`

## Test Conventions

```
tests/
├── unit/           # Mock subprocess, test each tool function
├── contract/       # Validate MCP JSON-RPC schema per tool
├── integration/    # Real ansible-core calls against fixtures/
├── transport/      # STDIO + HTTP + SSE parity
├── token_budget/   # Assert output sizes don't exceed limits
└── fixtures/       # Sample playbooks, inventories, roles
```

Run: `pytest tests/unit/ --cov --cov-fail-under=90`

## Common Tasks

### Add a new tool to existing plugin
1. Add method to plugin class
2. Register in `get_tools()` with short description
3. Add unit test in `tests/unit/test_{plugin}.py`
4. Add contract test in `tests/contract/`
5. Add token budget assertion
6. If docs needed: add `resources/docs/{tool}.md`

### Add a new plugin
1. Create `src/ansible_mcp/plugins/{name}.py`
2. Implement `AnsibleMCPPlugin` interface
3. Register entry_point in `pyproject.toml`
4. Add `should_load()` for workspace-aware activation
5. Full test suite: unit + contract + token budget

### Transport testing
```bash
# STDIO
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uvx ansible-mcp serve --stdio

# HTTP
uvx ansible-mcp serve --http --port 8080
curl -X POST http://localhost:8080/mcp -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Inspect
npx @anthropic/mcp-inspector uvx ansible-mcp serve --stdio

# Dev (from repo)
uv run ansible-mcp serve --stdio
```

## Design Principles

1. **No VS Code dependency** — the server is a pure Python package
2. **No client-specific code** — works with any MCP client
3. **Lazy everything** — plugins load on demand, resources fetched on request
4. **Token-first** — every output measured, budgeted, truncated
5. **Structured over text** — JSON responses, not free-text dumps
6. **Subprocess safety** — all CLI calls use `asyncio.create_subprocess_exec`, never `shell=True`
7. **Test coverage gate** — CI fails below 90% unit coverage
