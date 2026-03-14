# VS Code Marketplace Compatibility

This repository ships a standalone MCP server (`ansible-mcp`) and is compatible with VS Code MCP configuration today. This document summarizes official compatibility points and practical guidance for Marketplace distribution.

## Current compatibility (no extension required)

VS Code supports MCP server configuration in `mcp.json` at user/workspace scope.

- User scope location (macOS): `~/Library/Application Support/Code/User/mcp.json`
- Project scope location: `.vscode/mcp.json`

`ansible-mcp install --client copilot` writes the required server entry automatically.

## Official source references

- VS Code MCP server setup and config model:
  - https://code.visualstudio.com/docs/copilot/chat/mcp-servers
- VS Code Extension Marketplace and publishing flow:
  - https://code.visualstudio.com/api/working-with-extensions/publishing-extension

## What Marketplace can provide

Publishing a VS Code extension does not replace this Python package. Instead, it can provide a wrapper UX:

- one-click install from Marketplace
- command palette action to register the MCP server in user or workspace `mcp.json`
- optional diagnostics (verify `ansible-mcp` is installed and runnable)

## Recommended approach

1. Keep `ansible-mcp` as the runtime server distributed via PyPI.
2. Optionally create a thin VS Code companion extension for onboarding UX.
3. In extension docs, clearly state runtime dependency (`ansible-mcp` executable available in PATH).

This model preserves portability to non-VS Code clients while still enabling Marketplace discoverability.
