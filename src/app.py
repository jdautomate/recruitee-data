import os
import argparse

import uvicorn

from src.utils.server_config import mcp
from src.utils.auth import BearerAuthMiddleware

from src.tools import candidates, lookup, metrics, utils  # noqa: F401
from src.prompts import prompts # noqa: F401


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Recruitee MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport method for the server (default: stdio)."
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)."
    )
    parser.add_argument(
        "--path",
        required=False,
        help="Mount path for HTTP/SSE (default /mcp or /sse)."
    )

    parser_args = parser.parse_args()

    if parser_args.transport == "sse" and parser_args.path is None:
        parser_args.path = parser_args.path or "/sse"
    elif parser_args.transport == "streamable-http" and parser_args.path is None:
        parser_args.path = parser_args.path or "/mcp"
    else:
        parser_args.path = None
    return parser_args


if __name__ == "__main__":
    if not os.getenv("RECRUITEE_API_TOKEN") or not os.getenv("RECRUITEE_COMPANY_ID"):
        raise SystemExit("Please set RECRUITEE_COMPANY_ID and RECRUITEE_API_TOKEN in your environment variables.")

    args = parse_args()
    if args.transport == "stdio":
        print("Starting MCP server in stdio mode...")
        mcp.run(
            transport=args.transport,
        )

    elif args.transport == "streamable-http":
        print(f"Starting MCP server in streamable-http mode at http://{args.host}:{args.port}{args.path}")
        app = mcp.http_app(
            path=args.path,
        )
        app.add_middleware(BearerAuthMiddleware)
        uvicorn.run(app, host=args.host, port=args.port)

    elif args.transport == "sse":
        print(f"Starting MCP server in SSE mode at http://{args.host}:{args.port}{args.path}")
        mcp.run(
            transport=args.transport,
            path=args.path,
            host=args.host,
            port=args.port,
        )

