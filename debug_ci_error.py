#!/usr/bin/env python3
"""Debug CI ansible-lint failure."""

import asyncio
import subprocess
import sys
from pathlib import Path

async def main():
    # Check ansible-lint version
    print("=== Checking ansible-lint version ===")
    result = subprocess.run(["ansible-lint", "--version"], capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    
    # Check which sample_playbook file we're using
    print("\n=== Checking for sample playbook ===")
    for path in [
        Path("examples/sample_playbook"),
        Path("tests/fixtures/sample_playbook"),
        Path("sample_playbook"),
        Path("tests/integration/fixtures/sample_playbook"),
    ]:
        if path.exists():
            print(f"✓ Found: {path}")
            if path.is_file():
                print(f"  Content preview:")
                with open(path) as f:
                    for i, line in enumerate(f):
                        if i < 5:
                            print(f"    {line.rstrip()}")
                        else:
                            break
        else:
            print(f"✗ Not found: {path}")
    
    # Try running ansible-lint on each found playbook
    print("\n=== Running ansible-lint on sample playbooks ===")
    for path in Path(".").rglob("sample_playbook"):
        print(f"\nTesting: {path}")
        result = subprocess.run(
            ["ansible-lint", str(path)],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Stdout:\n{result.stdout}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr}")

if __name__ == "__main__":
    asyncio.run(main())
