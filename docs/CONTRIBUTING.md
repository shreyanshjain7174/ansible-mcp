# Contributing

This document is for maintainers and contributors of `ansible-mcp`.

## Development setup

```bash
cd /Users/sunny/Ansible/ansible-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Local run

```bash
ansible-mcp serve --stdio
```

## Test commands

Unit tests:

```bash
pytest tests/unit -v --tb=short
```

Integration tests:

```bash
pytest tests/integration -v --tb=short -m integration
```

Integration tests require these executables in `PATH`:

- `ansible-lint`
- `ansible-playbook`
- `ansible-inventory`

## Pre-commit hooks

Install once:

```bash
uv run --extra dev pre-commit install --hook-type pre-commit --hook-type pre-push
```

Run manually:

```bash
uv run --extra dev pre-commit run --all-files
uv run --extra dev pre-commit run --all-files --hook-stage pre-push
```

## Contributor guidelines

- Keep tool descriptions compact and schema-first.
- Keep subprocess execution safe (`create_subprocess_exec`, no `shell=True`).
- Add tests for every new tool path (unit and integration).
- Preserve client-agnostic behavior in core runtime.
