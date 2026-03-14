# Release Guide

This file documents release operations for maintainers.

## Versioning

Update version in `pyproject.toml` before creating a release tag.

## Publish to PyPI

This repo includes `.github/workflows/publish.yml`.

### One-time setup

1. Create `ansible-mcp` project on TestPyPI/PyPI (or reserve name).
2. Configure Trusted Publishing for this repository/workflow.
3. Create GitHub environments used by the workflow:
   - `testpypi`
   - `pypi`

### Publish flow

Manual test publish:

- Run workflow **Publish Package** with `repository=testpypi`.

Production publish:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The tag triggers PyPI publish workflow.

## Release checklist

- Run `pytest tests/unit -v --tb=short`
- Run `pytest tests/integration -v --tb=short -m integration`
- Validate install flow:
  - `uv tool install ansible-mcp`
  - `ansible-mcp install --client copilot`
  - `ansible-mcp install --client claude`
  - `ansible-mcp install --client cursor`
- Smoke check server startup:
  - `ansible-mcp serve --stdio`
