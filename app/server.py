import os
import argparse
import httpx

from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.server import Server

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

import uvicorn


# Load environment variables from .env file
load_dotenv()
RECRUITEE_COMPANY_ID = os.getenv("RECRUITEE_COMPANY_ID")
RECRUITEE_API_TOKEN = os.getenv("RECRUITEE_API_TOKEN")

# Initialize the MCP server
mcp = FastMCP(
    name="Recruitee Server",
    description="A server for Recruitee API",
)


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


@mcp.tool()
async def list_candidates() -> dict:
    """
    Lists all candidates from the Recruitee API using pagination.
    """
    base_url = f"https://api.recruitee.com/c/{RECRUITEE_COMPANY_ID}/candidates"
    headers = {
        "Authorization": f"Bearer {RECRUITEE_API_TOKEN}"
    }
    limit = 100  # Adjust as needed; Recruitee may have a maximum limit
    offset = 0
    all_candidates = []

    async with httpx.AsyncClient() as client:
        while True:
            params = {"limit": limit, "offset": offset}
            response = await client.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                break
            all_candidates.extend(candidates)
            offset += limit

    return {"candidates": all_candidates}


if __name__ == "__main__":
    # Set up argument parser
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
    args = parser.parse_args()

    if not os.getenv("RECRUITEE_API_TOKEN") or not os.getenv("RECRUITEE_COMPANY_ID"):
        raise ValueError("Please set RECRUITEE_COMPANY_ID and RECRUITEE_API_TOKEN in your environment variables.")

    mcp.host = args.host
    mcp.port = args.port

    if args.transport == "stdio":
        print("Starting MCP server in stdio mode...")
        mcp.run(transport="stdio")
    else:
        print(f"Starting MCP server in SSE mode at http://{args.host}:{args.port}/sse")
        mcp_server = mcp._mcp_server
        app = create_starlette_app(mcp_server, debug=True)
        uvicorn.run(app, host=args.host, port=args.port)
