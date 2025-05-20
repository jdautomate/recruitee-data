import os

from starlette.middleware.base import BaseHTTPMiddleware

from fastapi import Request, status
from fastapi.responses import JSONResponse



class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        expected = os.getenv("MCP_BEARER_TOKEN")
        header = request.headers.get("authorization")

        if expected and header != f"Bearer {expected}":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Unauthorized"},
            )
        return await call_next(request)
