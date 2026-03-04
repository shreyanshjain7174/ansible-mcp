#!/usr/bin/env python3
import asyncio
from pathlib import Path
import tempfile
import shutil
from ansible_mcp.context import detect_workspace
from ansible_mcp.plugins.lint import LintPlugin
from ansible_mcp.token_budget import TokenBudget

async def test():
    # Mimic fixture_workspace behavior
    repo_root = Path('/Users/sunny/Ansible/ansible-mcp')
    source_fixtures = repo_root / 'tests' / 'fixtures'
    
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        copied_fixtures = tmp_path / 'tests' / 'fixtures'
        copied_fixtures.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_fixtures, copied_fixtures)
        
        plugin = LintPlugin(detect_workspace(tmp_path), TokenBudget())
        
        print(f'Workspace root: {plugin.workspace.root}')
        print(f'Fixtures dir: {copied_fixtures}')
        print(f'Sample playbook path: {copied_fixtures / "sample_playbook.yml"}')
        print(f'Sample playbook exists: {(copied_fixtures / "sample_playbook.yml").exists()}')
        
        result = await plugin.handle_tool_call('lint', {'path': 'tests/fixtures/sample_playbook.yml'})
        print(f'Result status: {result.status}')
        print(f'Result exit_code: {result.payload.get("exit_code")}')
        print(f'Result stdout: {result.payload.get("stdout", "")[:200]}')
        print(f'Result stderr: {result.payload.get("stderr", "")[:200]}')

asyncio.run(test())
