# Ansible Content Best Practices

## Naming
- Give every play and task a clear, action-oriented name.
- Keep role and variable names consistent and predictable.

## Idempotency
- Prefer idempotent modules over ad-hoc shell commands.
- Ensure repeated runs converge to the same state.
- Validate `--check` mode where possible.

## Structure
- Keep playbooks focused by responsibility.
- Reuse logic via roles and include/import mechanisms.
- Keep inventories and group variables organized and explicit.

## Safety
- Store secrets in Ansible Vault, never in plain text.
- Avoid broad privilege escalation when narrow scope is enough.
- Fail early with clear messages for missing prerequisites.

## Quality
- Run `ansible-lint` before commit/push.
- Prefer FQCNs for module references.
- Keep YAML formatting consistent and readable.

## Testing
- Add syntax checks and lint checks in CI.
- Validate roles/playbooks in representative environments.
- Use integration tests for critical automation paths.
