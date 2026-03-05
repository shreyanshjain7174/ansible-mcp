# PyPI Trusted Publisher Setup Guide

This document walks you through configuring PyPI Trusted Publisher (OIDC) to enable automated releases from the GitHub workflow.

## Current Status

- ✅ Package `ansible-mcp` created on PyPI
- ✅ GitHub workflow `.github/workflows/publish.yml` configured and tested
- ✅ TestPyPI trusted publisher working (v0.1.0 successfully published)
- ❌ **PyPI production trusted publisher: BLOCKED** (configuration pending)

## The Issue

The GitHub workflow attempts to publish to production PyPI using OIDC (OpenID Connect) trusted publishing. The publish job fails with:

```
Trusted publishing exchange failure: 
Token request failed: the server refused the request for the following reasons:
* `invalid-publisher`: valid token, but no corresponding publisher 
  (Publisher with matching claims was not found)
```

This means: **PyPI is rejecting the OIDC token because no trusted publisher is configured to accept it**.

## Solution: Configure Trusted Publisher on PyPI

### Step 1: Log into PyPI

1. Go to https://pypi.org/account/login/
2. Sign in with your account credentials

### Step 2: Navigate to Project Settings

1. Go to https://pypi.org/project/ansible-mcp/
2. Click **"Manage"** in the top navigation
3. Look for **"Publishers"** or **"Publishing"** section in the left sidebar
4. Click **"Add a new pending publisher"** or similar option

### Step 3: Configure GitHub OIDC Publisher

Fill in the following fields:

| Field | Value |
|-------|-------|
| **Provider** | GitHub |
| **Owner** | `shreyanshjain7174` |
| **Repository** | `ansible-mcp` |
| **Workflow name** | `publish.yml` |
| **Workflow ref** | `refs/heads/main` (for manual dispatches and tag-based publishes on main) |
| **Environment name** | `pypi` |

**Note:** If your workflow can be triggered from multiple branches or tags, you may need to add multiple publisher entries:

- One for `refs/heads/main` (manual dispatch + tag-based on main)
- One for `refs/tags/v*` if you tag from other branches (adjust as needed)

### Step 4: Verify the Configuration

After adding the publisher:

1. You should see it listed under "Publishers" with status **"Pending"** (may take 1-2 minutes to activate)
2. Once active, the status will show **"Active"**

### Step 5: Test the Configuration

Trigger a test publish to PyPI:

```bash
# Using the GitHub CLI:
gh workflow run publish.yml --ref main -f repository=pypi

# This will dispatch the publish workflow with repository=pypi parameter
```

Monitor the workflow:

```bash
gh run list --workflow=publish.yml --limit=1
# Get the run ID from output, then:
gh run view <RUN_ID> --log
```

Expected output: `publish-pypi` job should succeed with status `success` and conclusion `completed`.

### Step 6: Verify Package on PyPI

Once publish succeeds, verify the package is live:

```bash
# Check via PyPI API
curl -s https://pypi.org/pypi/ansible-mcp/json | python -m json.tool | head -50

# Should return v0.1.0, v1, and any newer versions you publish
```

Or visit: https://pypi.org/project/ansible-mcp/

### Step 7: Validate Fresh Install (Optional but Recommended)

Test a fresh installation from production PyPI:

```bash
# Fresh install from production PyPI
uv tool install ansible-mcp

# Test the binary
ansible-mcp serve --help
```

Should resolve all 43 dependencies and create the executable without errors.

---

## Alternative: TestPyPI as Fallback

While waiting for PyPI configuration to be completed, users can install from TestPyPI:

```bash
uv tool install \
  --index-url https://test.pypi.org/simple \
  --extra-index-url https://pypi.org/simple \
  ansible-mcp==0.1.0
```

#### To update documentation for TestPyPI fallback:

Add to README Installation section:

```markdown
### Install from TestPyPI (while production configuration is pending)

```bash
uv tool install \
  --index-url https://test.pypi.org/simple \
  --extra-index-url https://pypi.org/simple \
  ansible-mcp==0.1.0
```
```

---

## Troubleshooting

### Error: "Publisher not found"

This indicates the OIDC token claims don't match your configured publisher. Verify:

1. **Owner** matches exactly: `shreyanshjain7174`
2. **Repository** matches exactly: `ansible-mcp`
3. **Workflow name** matches: `publish.yml`
4. **Environment name** matches: `pypi`
5. **Workflow ref** is correct for how you're triggering publishes

### Error: "Invalid environment"

Ensure GitHub environment `pypi` exists in your repository:

1. Go to https://github.com/shreyanshjain7174/ansible-mcp/settings/environments
2. Create environment `pypi` if it doesn't exist
3. No special configuration needed (you can leave it empty)

### Publish still fails after configuration

Wait 2-5 minutes for PyPI to fully activate the publisher, then retry.

If still failing, try triggering from a new tag:

```bash
git tag v0.1.1
git push origin v0.1.1
```

---

## Reference: Current Workflow Configuration

For reference, here's what the workflow expects (from `.github/workflows/publish.yml`):

```yaml
permissions:
  id-token: write  # Required for OIDC token exchange

jobs:
  publish-pypi:
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    environment: pypi  # Must match your PyPI published environment name
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/
      
      - name: Publish distribution to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist/
```

The workflow uses `pypa/gh-action-pypi-publish@release/v1`, which automatically handles OIDC token exchange with PyPI.

---

## Next Steps After Setup

Once PyPI trusted publisher is configured and the first publish succeeds:

1. Future releases can be published by simply tagging: `git tag vX.Y.Z && git push origin vX.Y.Z`
2. You can also use manual dispatch: `gh workflow run publish.yml -f repository=pypi`
3. Remove TestPyPI workaround from documentation

---

## Questions?

Refer to:
- PyPI Trusted Publishing docs: https://docs.pypi.org/trusted-publishers/
- GitHub OIDC docs: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
