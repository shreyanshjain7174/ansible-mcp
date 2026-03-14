from __future__ import annotations

import argparse
import os
from pathlib import Path

from ansible_mcp.installer import install_client_config
from ansible_mcp.server import run_server


def _workspace_from_env_or_default(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_workspace = os.getenv("WORKSPACE_ROOT")
    if env_workspace:
        return Path(env_workspace).expanduser().resolve()
    return Path.cwd()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standalone MCP server for Ansible tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run MCP server")
    serve_parser.add_argument("--workspace-root", type=str, help="Workspace root path")
    serve_parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host to bind server transport",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000,
        help="Port to bind server transport",
    )

    transport_group = serve_parser.add_mutually_exclusive_group()
    transport_group.add_argument("--stdio", action="store_true", help="Run over stdio (default)")
    transport_group.add_argument("--http", action="store_true", help="Run over streamable HTTP")
    transport_group.add_argument("--sse", action="store_true", help="Run over SSE")
    serve_parser.add_argument(
        "--stateless-http",
        action="store_true",
        help="Enable stateless HTTP mode (used only with --http)",
    )

    install_parser = subparsers.add_parser(
        "install", help="Configure ansible-mcp for a supported MCP client"
    )
    install_parser.add_argument(
        "--client",
        choices=["copilot", "claude", "cursor"],
        required=True,
        help="Target MCP client",
    )
    install_parser.add_argument(
        "--scope",
        choices=["user", "project"],
        default="user",
        help="Where to install config (default: user)",
    )
    install_parser.add_argument(
        "--workspace-root",
        type=str,
        help="Workspace root path (required for project scope)",
    )
    install_parser.add_argument(
        "--name",
        type=str,
        default="ansible-mcp",
        help="Server name key in client config",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "serve":
        transport = "stdio"
        if args.http:
            transport = "streamable-http"
        elif args.sse:
            transport = "sse"

        workspace_root = _workspace_from_env_or_default(args.workspace_root)
        stateless_http = args.stateless_http if args.http else False
        run_server(
            workspace_root=workspace_root,
            transport=transport,
            host=args.host,
            port=args.port,
            stateless_http=stateless_http,
        )
        return 0

    if args.command == "install":
        install_workspace_root: Path | None = None
        if args.scope == "project":
            install_workspace_root = _workspace_from_env_or_default(args.workspace_root)

        result = install_client_config(
            client=args.client,
            scope=args.scope,
            server_name=args.name,
            workspace_root=install_workspace_root,
        )
        print(
            f"Configured '{result.server_name}' for {result.client} "
            f"({result.scope}) at {result.config_path}"
        )
        if result.client == "copilot":
            print("Next step: reload VS Code (Developer: Reload Window)")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
