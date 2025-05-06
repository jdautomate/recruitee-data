import os
import argparse

import uvicorn

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

from mcp.server.sse import SseServerTransport
from mcp.server import Server

from server_config import mcp
import tools    # noqa: F401



def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Recruitee MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="sse",
        help="Transport method to use: 'stdio' for standard input/output or 'sse' for Server-Sent Events."
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
    return parser.parse_args()

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    if not os.getenv("RECRUITEE_API_TOKEN") or not os.getenv("RECRUITEE_COMPANY_ID"):
        raise ValueError("Please set RECRUITEE_COMPANY_ID and RECRUITEE_API_TOKEN in your environment variables.")

    args = parse_args()
    if args.transport == "stdio":
        print("Starting MCP server in stdio mode...")
        mcp.run(transport="stdio")
    else:
        print(f"Starting MCP server in SSE mode at http://{args.host}:{args.port}/sse")
        mcp.host = args.host
        mcp.port = args.port
        app = create_starlette_app(mcp._mcp_server, debug=True)
        uvicorn.run(app, host=args.host, port=args.port)
