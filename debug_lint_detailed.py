#!/usr/bin/env python3
"""Debug script to trace ansible-lint behavior in detail."""

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from ansible_mcp.context import detect_workspace
from ansible_mcp.plugins.lint import LintPlugin
from ansible_mcp.token_budget import TokenBudget


async def main():
    """Run detailed debugging of ansible-lint."""
    import tempfile
    
    # Create fixture workspace like the test does
    repo_root = Path(__file__).resolve().parent
    source_fixtures = repo_root / "tests" / "fixtures"
    
    # Create temp directory for fixtures
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Copy fixtures
        copied_fixtures = tmp_path / "tests" / "fixtures"
        copied_fixtures.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_fixtures, copied_fixtures)
        
        print(f"Workspace root: {tmp_path}")
        print(f"Fixtures dir: {copied_fixtures}")
        
        # Check fixture files
        sample_playbook = copied_fixtures / "sample_playbook.yml"
        print(f"Sample playbook path: {sample_playbook}")
        print(f"Sample playbook exists: {sample_playbook.exists()}")
        print(f"Sample playbook is absolute: {sample_playbook.is_absolute()}")
        print()
        
        # Create plugin
        workspace = detect_workspace(tmp_path)
        print(f"Detected workspace.root: {workspace.root}")
        print()
        
        # First, test direct ansible-lint command
        print("=" * 60)
        print("Testing direct ansible-lint command")
        print("=" * 60)
        cmd = ["ansible-lint", str(sample_playbook)]
        print(f"Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
        print(f"Exit code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        print()
        
        # Now test with the plugin
        print("=" * 60)
        print("Testing with LintPlugin")
        print("=" * 60)
        token_budget = TokenBudget()
        plugin = LintPlugin(workspace, token_budget)
        
        # Call with fixture path (relative)
        path = "tests/fixtures/sample_playbook.yml"
        print(f"Calling plugin.handle_tool_call('lint', {{'path': '{path}'}})")
        result = await plugin.handle_tool_call("lint", {"path": path})
        
        print(f"Result status: {result.status}")
        print(f"Result payload: {result.payload}")
        print()
        
        # Additional info
        if "exit_code" in result.payload:
            print(f"Exit code from result: {result.payload['exit_code']}")
        if "stdout" in result.payload:
            print(f"Stdout from result: {result.payload['stdout']}")
        if "stderr" in result.payload:
            print(f"Stderr from result: {result.payload['stderr']}")


if __name__ == "__main__":
    asyncio.run(main())
