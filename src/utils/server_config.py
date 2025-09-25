import os
from typing import Literal

from dotenv import load_dotenv, find_dotenv
from fastmcp import FastMCP
from starlette.datastructures import MutableHeaders
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware


REQUIRED_MEDIA_TYPES: tuple[str, str] = ("application/json", "text/event-stream")


def _normalize_accept_header(raw_value: str | None) -> str:
    """Ensure the Accept header contains the required media types."""

    values: list[str] = []
    seen_media_types: set[str] = set()

    if raw_value:
        for part in raw_value.split(","):
            normalized = part.strip()
            if not normalized:
                continue
            values.append(normalized)
            media_type = normalized.split(";", 1)[0].strip().lower()
            seen_media_types.add(media_type)

    for media_type in REQUIRED_MEDIA_TYPES:
        if media_type not in seen_media_types:
            values.append(media_type)

    return ", ".join(values)


class MCPAcceptHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures MCP requests advertise required media types."""

    def __init__(self, app, *, mcp_path: str) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        normalized = mcp_path.rstrip("/") or "/"
        self._mcp_path = normalized

    def _should_mutate(self, request_path: str) -> bool:
        if self._mcp_path == "/":
            return True
        return request_path == self._mcp_path or request_path.startswith(f"{self._mcp_path}/")

    async def dispatch(self, request, call_next):  # type: ignore[override]
        if request.scope.get("type") == "http" and self._should_mutate(request.scope.get("path", "")):
            headers = MutableHeaders(scope=request.scope)
            headers["accept"] = _normalize_accept_header(headers.get("accept"))

        return await call_next(request)


class RecruiteeFastMCP(FastMCP):
    """FastMCP subclass that injects Accept header middleware for HTTP apps."""

    def http_app(
        self,
        path: str | None = None,
        middleware: list[Middleware] | None = None,
        json_response: bool | None = None,
        stateless_http: bool | None = None,
        transport: Literal["streamable-http", "sse"] = "streamable-http",
    ):
        app = super().http_app(
            path=path,
            middleware=middleware,
            json_response=json_response,
            stateless_http=stateless_http,
            transport=transport,
        )

        if transport == "streamable-http":
            target_path = path or getattr(app.state, "path", "/")
            app.add_middleware(MCPAcceptHeaderMiddleware, mcp_path=target_path)

        return app



_INSTRUCTIONS = """A server for Recruitee API"""

if find_dotenv() != "":
    load_dotenv(find_dotenv())

RECRUITEE_COMPANY_ID = os.getenv("RECRUITEE_COMPANY_ID")
RECRUITEE_API_TOKEN = os.getenv("RECRUITEE_API_TOKEN")
BASE_DEPLOY_URL = os.getenv("BASE_DEPLOY_URL")

# Initialize the MCP server
mcp = RecruiteeFastMCP(
    name="Recruitee Server",
    instructions=_INSTRUCTIONS,
)
