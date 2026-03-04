#!/usr/bin/env python3
"""Backwards-compatible entrypoint for real-tool integration tests.

Run with:
  uv run python tests/e2e_test.py

This delegates to pytest so setup/teardown and cleanup are managed by fixtures.
"""

import pytest

if __name__ == "__main__":
  raise SystemExit(pytest.main(["-q", "tests/integration/test_real_tools.py"]))
