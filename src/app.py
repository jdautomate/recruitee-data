import os
import argparse

import uvicorn
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import MutableHeaders

from src.utils.server_config import mcp
from src.utils.auth import BearerAuthMiddleware, LoginPasswordMiddleware, limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.tools import candidates, offers, lookup, metrics, utils  # noqa: F401
from src.prompts import prompts # noqa: F401



def mount_static_files(app):
    """Helper function to mount static files to the FastAPI app."""
    # Use Fly volume mount path for persistent storage
    documents_dir = os.getenv("DOCUMENTS_DIR") or "./data"
    
    # Ensure the directory exists
    os.makedirs(documents_dir, exist_ok=True)
    
    if os.path.exists(documents_dir):
        app.mount("/documents", StaticFiles(directory=documents_dir), name="documents")
        print(f"Static files mounted at /documents from {documents_dir}")
        return True
    else:
        print(f"Warning: Documents directory not found at {documents_dir}")
        return False


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

        mcp_path = args.path.rstrip("/") if args.path else "/mcp"

        @app.middleware("http")
        async def ensure_event_stream_accept(request, call_next):
            if request.url.path.rstrip("/") == mcp_path:
                headers = MutableHeaders(scope=request.scope)
                accept_header = headers.get("accept")

                if accept_header:
                    parts = [part.strip() for part in accept_header.split(",") if part.strip()]
                else:
                    parts = []

                has_application_json = any(
                    part.split(";")[0].strip().lower() == "application/json"
                    for part in parts
                )
                has_event_stream = any(
                    part.split(";")[0].strip().lower() == "text/event-stream"
                    for part in parts
                )

                updated_parts = list(parts)

                if not has_application_json:
                    updated_parts.insert(0, "application/json")

                if not has_event_stream:
                    updated_parts.append("text/event-stream")

                if not has_event_stream or not has_application_json:
                    headers["accept"] = ", ".join(updated_parts)

            response = await call_next(request)
            return response
        # Configure rate limiter
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        # Add security middlewares
        app.add_middleware(BearerAuthMiddleware, protected_paths=["/mcp"])
        app.add_middleware(LoginPasswordMiddleware, protected_paths=["/documents"])
        mount_static_files(app)
        uvicorn.run(app, host=args.host, port=args.port)

    elif args.transport == "sse":
        print(f"Starting MCP server in SSE mode at http://{args.host}:{args.port}{args.path}")
        mcp.run(
            transport=args.transport,
            path=args.path,
            host=args.host,
            port=args.port,
        )

