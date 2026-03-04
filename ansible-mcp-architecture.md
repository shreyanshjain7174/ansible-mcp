# ansible-mcp: Standalone MCP Server Architecture

## Executive Summary

A ground-up rewrite of the Ansible MCP server as a **standalone Python package** (`uv add ansible-mcp` / `uv tool install ansible-mcp`), decoupled from the VS Code extension monorepo, vendor-agnostic across all MCP clients, with plugin-based tool architecture and aggressive token optimization. Uses **uv** as the package manager for 10-100x faster installs, lockfile reproducibility, and inline script support.

---

## Problem Analysis: Current Upstream

| Issue | Impact |
|-------|--------|
| **Nested in vscode-ansible monorepo** | Can't install standalone; tied to VS Code extension build pipeline |
| **TypeScript/Node.js** | Language mismatch — Ansible ecosystem is Python; tool calls shell out to Python anyway |
| **Copilot-only design** | `@ansible` chat participant pattern locks out Claude, Cursor, Windsurf, CLI agents |
| **STDIO only** | No remote hosting, no containerized deployment |
| **Monolithic tool loading** | All 11 tools loaded at init; ~2400 tokens burned on `tools/list` alone |
| **Broken CI, low coverage** | ~15% test coverage estimated; packaging bugs (see #2457, #2464) |
| **No token awareness** | Tool responses return unbounded output; no pagination, truncation, or streaming |
| **Resource coupling** | Static markdown files bundled in extension package, not dynamically served |

---

## Architecture: Five-Layer Design

### Layer 1: AI Clients (Vendor-Agnostic)

No client-specific code. Any MCP-compliant client works out of the box:

- **Claude Desktop / claude.ai** — STDIO or remote HTTP
- **GitHub Copilot** — STDIO via `mcp.json`
- **Cursor / Windsurf / Zed** — STDIO or SSE
- **CLI agents** (mcp-cli, custom) — any transport
- **VS Code extension** — thin wrapper that spawns `ansible-mcp serve --stdio`

### Layer 2: Transport Layer (Multi-Protocol)

```
┌──────────────┬───────────────────┬─────────────┬──────────────┐
│    STDIO     │ Streamable HTTP   │   SSE       │  WebSocket   │
│ (local dev)  │ (remote/scale)    │ (legacy)    │ (future)     │
└──────────────┴───────────────────┴─────────────┴──────────────┘
                         │
                   JSON-RPC 2.0
```

- **STDIO**: Default for local. `ansible-mcp serve --stdio`
- **Streamable HTTP**: For remote/team deployments. `ansible-mcp serve --http --port 8080`
- **SSE**: Backward compat for older MCP clients
- **Auto-negotiation**: Server detects transport from client capabilities

### Layer 3: Core Server

The stateless core with three critical subsystems:

#### 3a. Tool Router + Registry

```python
# Entry point pattern — plugins register via Python entry_points
[project.entry-points."ansible_mcp.plugins"]
lint = "ansible_mcp.plugins.lint:LintPlugin"
playbook = "ansible_mcp.plugins.playbook:PlaybookPlugin"
inventory = "ansible_mcp.plugins.inventory:InventoryPlugin"
galaxy = "ansible_mcp.plugins.galaxy:GalaxyPlugin"
aap = "ansible_mcp.plugins.aap:AAPPlugin"
```

- Discovers plugins at startup via `importlib.metadata.entry_points()`
- **Lazy loading**: Plugin class instantiated only on first tool call
- **`listChanged` notification**: Dynamically advertise/hide tools based on workspace context
- Workspace detection: if project has `roles/` → load galaxy plugin; has `molecule/` → load molecule plugin

#### 3b. Token Budget Manager

Every tool call tracked:

```python
@dataclass
class TokenBudget:
    max_description_tokens: int = 60    # per tool in tools/list
    max_response_tokens: int = 500      # per tool call result
    max_total_list_tokens: int = 800    # entire tools/list response
```

- Tool descriptions compressed to <60 tokens each (vs ~220 upstream)
- Verbose docs moved to MCP **resources** (`ansible://docs/lint-rules`)
- Response truncation with continuation: `"... [truncated, 847 more lines — use ansible://results/abc123 to read full output]"`

#### 3c. Context Compressor

- Deduplicates repeated context (e.g., inventory already sent in previous call)
- Strips ANSI codes, redundant whitespace from subprocess output
- Structured results: JSON over free-text where possible (easier for LLMs to parse)

### Layer 4: Plugin Modules

Each plugin is a self-contained Python module:

```
ansible_mcp/plugins/
├── __init__.py          # Plugin base class
├── lint.py              # ansible-lint, yamllint, syntax-check
├── playbook.py          # create, run, validate, explain
├── inventory.py         # parse, query, graph, diff
├── galaxy.py            # search, install, scaffold, info
├── aap.py               # AAP/Tower: jobs, templates, inventories
├── molecule.py          # init, test, converge, destroy
├── vault.py             # encrypt, decrypt, rekey, view
├── navigator.py         # ansible-navigator integration
└── ee.py                # execution environment build/inspect
```

**Plugin interface:**

```python
class AnsibleMCPPlugin(ABC):
    """Base class for all plugins."""

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """Return tool definitions for this plugin."""

    @abstractmethod
    async def handle_tool_call(self, name: str, args: dict) -> ToolResult:
        """Execute a tool call."""

    def get_resources(self) -> list[Resource]:
        """Optional: expose MCP resources."""
        return []

    def should_load(self, workspace: WorkspaceContext) -> bool:
        """Optional: conditional loading based on workspace."""
        return True
```

### Layer 5: Backend / System Layer

Plugins delegate to actual Ansible tooling:

| Plugin | Backend | Method |
|--------|---------|--------|
| Lint | `ansible-lint`, `yamllint` | subprocess |
| Playbook | `ansible-playbook` | subprocess |
| Inventory | `ansible-inventory` | subprocess + parsing |
| Galaxy | `ansible-galaxy`, Galaxy API | subprocess + HTTP |
| AAP | AAP Controller REST API | HTTP (httpx) |
| Molecule | `molecule` CLI | subprocess |
| Vault | `ansible-vault` | subprocess |
| Navigator | `ansible-navigator` | subprocess |

---

## Token Optimization Strategy

### Before (Upstream): ~2400 tokens for tools/list

```
Tool: ansible_lint
Description: "Runs ansible-lint against the specified playbook or role
directory to identify issues, best practice violations, and potential
bugs in your Ansible content. The tool supports passing custom
configuration paths, rule selections, and various output formats..."
(~220 tokens per tool × 11 tools)
```

### After (Rewrite): ~600 tokens for tools/list

```
Tool: lint
Description: "Lint Ansible files. Returns issues with severity/line/rule."
InputSchema: { path: string, config?: string, tags?: string[] }
(~55 tokens per tool × 8 core tools + lazy plugins)
```

### Where the verbosity goes:

Into **MCP Resources** that the LLM can request on-demand:

```
ansible://docs/lint          → full lint tool documentation
ansible://docs/lint-rules    → all ansible-lint rules with examples
ansible://schemas/playbook   → playbook YAML schema reference
ansible://examples/lint      → example lint invocations and outputs
```

This way, the LLM gets a compact tool listing, and can pull docs only when it needs context for a specific tool.

### Response Optimization

| Strategy | Tokens Saved |
|----------|-------------|
| Structured JSON over free-text | ~40% reduction |
| Strip ANSI/whitespace from CLI output | ~15% reduction |
| Truncation with resource-based pagination | Unbounded → capped at 500 |
| Dedup context across multi-turn | ~20-30% on subsequent calls |

---

## Test Architecture

### Test Pyramid

```
            ╱ Protocol Conformance (mcp-inspector) ╲
           ╱   Transport Tests (STDIO, HTTP, SSE)    ╲
          ╱     Integration (tool → ansible-core)      ╲
         ╱       Contract (JSON-RPC schema validity)     ╲
        ╱          Unit (every function, every edge case)  ╲
       ╱─────────────────────────────────────────────────────╲
```

### Specific Test Types

**Unit Tests** (~120): Each tool function tested in isolation with mocked subprocess calls.

**Contract Tests** (~40): Every tool's input schema and output format validated against MCP JSON-RPC spec. Assert response structure: `{ content: [{ type: "text", text: string }] }`.

**Integration Tests** (~30): Real `ansible-lint`, `ansible-playbook --syntax-check` calls against fixture playbooks in `tests/fixtures/`.

**Protocol Conformance**: Run `mcp-inspector` against the server for full MCP spec compliance.

**Token Budget Tests**: Assert that no tool description exceeds 60 tokens, no tool response exceeds 500 tokens for standard inputs.

**Transport Matrix**: Each transport (STDIO, HTTP, SSE) tested with the same tool calls to ensure parity.

### CI Pipeline

```yaml
# .github/workflows/ci.yml
jobs:
  lint:        ruff check + mypy --strict
  unit:        pytest tests/unit/ --cov --cov-fail-under=90
  contract:    pytest tests/contract/
  integration: pytest tests/integration/ (needs ansible-core)
  conformance: npx @anthropic/mcp-inspector@latest ansible-mcp serve --stdio
  tokens:      pytest tests/token_budget/
  transport:   pytest tests/transport/ -k "stdio or http or sse"
```

---

## Metrics Dashboard

| Metric | Target | How Measured |
|--------|--------|-------------|
| Token cost per `tools/list` | < 800 tokens | tiktoken count in CI |
| Token cost per tool response (avg) | < 500 tokens | fixture-based measurement |
| Latency p50 (tool call) | < 200ms | pytest-benchmark |
| Latency p99 (tool call) | < 2s | pytest-benchmark |
| Test coverage (unit) | > 90% | coverage.py |
| Test coverage (contract) | 100% of tools | schema validation |
| Protocol conformance | Pass | mcp-inspector |
| Client compatibility | 5+ clients | manual matrix |
| Plugin load time | < 50ms | benchmark on cold start |

---

## Project Structure

```
ansible-mcp/
├── pyproject.toml                 # Package config, entry_points, uv workspace
├── uv.lock                        # Reproducible lockfile
├── src/
│   └── ansible_mcp/
│       ├── __init__.py
│       ├── __main__.py            # CLI: ansible-mcp serve
│       ├── server.py              # Core MCP server setup
│       ├── router.py              # Tool router + registry
│       ├── token_budget.py        # Token tracking + compression
│       ├── context.py             # Workspace detection
│       ├── transports/
│       │   ├── stdio.py
│       │   ├── http.py
│       │   └── sse.py
│       ├── plugins/
│       │   ├── __init__.py        # Plugin ABC
│       │   ├── lint.py
│       │   ├── playbook.py
│       │   ├── inventory.py
│       │   ├── galaxy.py
│       │   ├── aap.py
│       │   ├── molecule.py
│       │   ├── vault.py
│       │   └── ee.py
│       └── resources/
│           ├── __init__.py
│           └── docs/              # Markdown docs served as MCP resources
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── transport/
│   ├── token_budget/
│   └── fixtures/                  # Sample playbooks, inventories
├── Dockerfile                     # For remote deployment
├── .github/workflows/ci.yml
└── docs/
    ├── clients/                   # Setup guides per client
    │   ├── claude.md
    │   ├── copilot.md
    │   ├── cursor.md
    │   └── cli.md
    └── plugins.md                 # Plugin development guide
```

---

## Distribution Strategy

| Channel | Command | Use Case |
|---------|---------|----------|
| **PyPI (via uv)** | `uv add ansible-mcp` | Project dependency |
| **uv tool** | `uv tool install ansible-mcp` | Global CLI tool |
| **uvx** | `uvx ansible-mcp serve --stdio` | Zero-install ephemeral run |
| **Docker** | `docker run ansible/mcp-server` | Remote/team hosting |
| **VS Code** | Extension spawns installed package | IDE integration |
| **MCP Registry** | Listed for discovery | Copilot/Cursor auto-config |

### VS Code Extension (Thin Wrapper)

The VS Code extension becomes a thin wrapper:

```typescript
// extension.ts — the ENTIRE MCP integration
const server = new McpServerDescriptor(
  "Ansible Development Tools",
  "ansible-mcp",   // pip package
  ["serve", "--stdio"],
  { WORKSPACE_ROOT: workspaceFolder }
);
```

No TypeScript MCP server code. Just spawn the Python package.

---

## Migration Path from Upstream

1. **Fork nothing** — clean-room rewrite in Python using the MCP Python SDK
2. **Port tool semantics** — same tool names and behaviors, better schemas
3. **Backward-compatible config** — respect existing `WORKSPACE_ROOT` env var
4. **Coexistence period** — both servers can run; new one registered under different name initially
5. **Upstream PR** — propose replacing the TypeScript MCP package with a Python dependency

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **uv over pip/pipx** | 10-100x faster installs; lockfile reproducibility; `uvx` for zero-install MCP client configs |
| **Python over TypeScript** | Ansible is Python; eliminates Node.js dependency; direct access to ansible-core APIs |
| **Standalone package** | Independent release cycle; pip installable; no monorepo coupling |
| **Plugin entry_points** | Standard Python mechanism; third parties can add plugins |
| **Lazy loading** | Only instantiate plugins on first use; faster startup, lower memory |
| **Resources for docs** | Keeps tool descriptions tiny; LLM pulls docs on-demand |
| **Multi-transport** | STDIO for local, HTTP for remote — same code, different transport |
| **FastMCP SDK** | Official Python MCP SDK; handles protocol, we focus on tools |
| **Token budgets in CI** | Regression-test output size; prevent token bloat creep |
