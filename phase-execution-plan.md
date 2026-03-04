# Phase Execution Plan

Date: 2026-03-04
Status: Published

## Scope
This plan starts from the current stable baseline:
- CI green after lint environment hardening
- Unit + integration tests passing
- MCP stdio handshake and tool discovery verified

## Phase 1 — Baseline Lock
**Objective**
Lock current tool contracts and CI behavior to prevent accidental drift.

**Tasks**
- Freeze and validate current tool names/schemas/docs URIs.
- Keep pre-commit checks aligned with CI jobs.
- Add a lint regression check for hostile/unwritable environment settings.

**Acceptance Criteria**
- No contract drift in existing tools.
- CI remains green on quality + unit + integration.
- New lint regression check reproduces prior failure class and passes with current fix.

**Verification**
```bash
uv run ruff check src tests
uv run mypy --strict src
uv run pytest tests/unit -v --tb=short
uv run pytest tests/integration -v --tb=short -m integration
```

**Safety / Rollback**
- Revert to last green commit if contract or CI instability appears.
- Keep scope limited to reliability guardrails only.

---

## Phase 2 — Galaxy Plugin MVP
**Objective**
Deliver first roadmap expansion plugin with the same quality bar as existing plugins.

**Tasks**
- Implement `galaxy` plugin module.
- Register tools in plugin entry points and server wrappers.
- Add docs resource page for galaxy tools.
- Add unit + integration tests for success/failure paths.

**Acceptance Criteria**
- Galaxy tools appear in `list_ansible_tools`.
- Tool calls return structured payloads with stable status behavior.
- Unit and integration coverage added and passing.

**Verification**
```bash
uv run pytest tests/unit -k galaxy -v --tb=short
uv run pytest tests/integration -k galaxy -v --tb=short -m integration
uv run pytest tests/unit tests/integration -v --tb=short
```

**Safety / Rollback**
- Disable galaxy registration first to feature-off quickly.
- Revert plugin entry-point and wrapper wiring if needed.

---

## Phase 3 — Molecule Plugin MVP
**Objective**
Ship molecule lifecycle tooling with workspace-aware loading.

**Tasks**
- Implement molecule plugin and command wrappers.
- Add `should_load` logic based on workspace context.
- Add docs + tests mirroring existing plugin patterns.

**Acceptance Criteria**
- Molecule tools appear only when workspace supports them.
- Tool execution is safe and deterministic under CI.
- Full suite remains green.

**Verification**
```bash
uv run pytest tests/unit -k molecule -v --tb=short
uv run pytest tests/integration -k molecule -v --tb=short -m integration
uv run ruff check src tests && uv run mypy --strict src
```

**Safety / Rollback**
- Keep molecule registration isolated for one-step disable.
- Roll back only molecule surface if regressions are detected.

---

## Phase 4 — Vault Plugin MVP + Release Gate
**Objective**
Add vault tooling with strict output safety and release readiness.

**Tasks**
- Implement vault plugin + wrappers + docs.
- Validate no sensitive leakage in rendered payload paths.
- Update roadmap/status docs.
- Run full release gate (quality + tests + MCP smoke).

**Acceptance Criteria**
- Vault tools discoverable and functionally validated.
- No sensitive-path leakage in outputs.
- CI fully green and release gate passed.

**Verification**
```bash
uv run ruff check src tests
uv run mypy --strict src
uv run pytest tests/unit tests/integration -v --tb=short
# MCP smoke sequence
(printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"manual-check","version":"1.0"}}}\n'; \
 printf '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}\n'; \
 printf '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n') | uv run ansible-mcp serve --stdio
```

**Safety / Rollback**
- Remove vault registration immediately on any safety concern.
- Release only from a known green commit/tag.

---

## Priority Hardening Backlog
### P0 (Mandatory)
- Add hostile-environment lint regression check in integration lane.
- Bound `ansible-lint` dependency drift to tested range.

### P1 (Recommended)
- Add post-failure CI diagnostics (`ansible-lint --version`, env snapshot).
- Enable stricter pytest config (`--strict-config --strict-markers`).

### P2 (Optional)
- Extend environment hardening parity to playbook and inventory plugin execution paths.

## Exit Definition
This plan is complete when:
1. Phases 1–4 acceptance criteria are met.
2. CI remains green throughout expansions.
3. Tool contracts remain stable and documented.
