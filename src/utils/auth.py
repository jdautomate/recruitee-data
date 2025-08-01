import os

from starlette.middleware.base import BaseHTTPMiddleware

from fastapi import Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.responses import RedirectResponse


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, protected_paths=None):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/mcp"]
    
    async def dispatch(self, request: Request, call_next):
        # Only apply Bearer auth to specific paths (like /mcp)
        path_requires_bearer = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        if not path_requires_bearer:
            return await call_next(request)
        
        expected = os.getenv("MCP_BEARER_TOKEN")
        if not expected:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Server misconfiguration - MCP_BEARER_TOKEN not set"})
        
        header = request.headers.get("authorization")
        if not header or not header.startswith("Bearer "):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Missing authorization header"})
        
        token = header.split(" ")[1] if len(header.split(" ")) > 1 else ""
        if token != expected:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Unauthorized"})
        
        return await call_next(request)


class LoginPasswordMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, protected_paths=None):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/documents"]
    
    async def dispatch(self, request: Request, call_next):
        # Only apply login/password auth to documents paths
        path_requires_login = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        if not path_requires_login:
            return await call_next(request)
        
        auth_token_secret = os.getenv("DOCUMENTS_TOKEN")
        docs_username = os.getenv("DOCUMENTS_USERNAME")
        docs_password = os.getenv("DOCUMENTS_PASSWORD")
        
        if not auth_token_secret:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Server misconfiguration - DOCUMENTS_TOKEN not set"})
        if not docs_username or not docs_password:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Server misconfiguration - DOCUMENTS_USERNAME or DOCUMENTS_PASSWORD not set"})
        
        auth_token = request.cookies.get("auth_token")
        if auth_token and self._verify_token(auth_token, auth_token_secret):
            return await call_next(request)
        
        if request.method == "POST":
            is_secure = request.url.scheme == "https"
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
            
            if username == docs_username and password == docs_password:
                response = RedirectResponse(url=str(request.url), status_code=302)
                response.set_cookie(
                    "auth_token", 
                    auth_token_secret,
                    max_age=3600*24*7,
                    httponly=True,
                    secure=is_secure,
                    samesite="strict",
                    path="/documents"
                )
                return response
            else:
                return self._show_login_form(error="Invalid username or password")
        return self._show_login_form()

    @staticmethod
    def _verify_token(token: str, expected_secret: str) -> bool:
        return token == expected_secret

    @staticmethod
    def _show_login_form(error: str = None):
        error_html = ""
        if error:
            error_html = f'<div class="error">{error}</div>'
        
        login_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Document Access - Recruitee MCP Server</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    max-width: 400px; 
                    margin: 100px auto; 
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h2 {{
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .form-group {{ 
                    margin: 20px 0; 
                }}
                label {{
                    display: block;
                    margin-bottom: 5px;
                    color: #555;
                    font-weight: 500;
                }}
                input[type="text"], input[type="password"] {{ 
                    width: 100%; 
                    padding: 12px; 
                    border: 1px solid #ddd; 
                    border-radius: 4px;
                    font-size: 14px;
                    box-sizing: border-box;
                }}
                input[type="text"]:focus, input[type="password"]:focus {{
                    border-color: #007bff;
                    outline: none;
                }}
                button {{ 
                    background: #007bff; 
                    color: white; 
                    padding: 12px 20px; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                    margin-top: 10px;
                }}
                button:hover {{ 
                    background: #0056b3; 
                }}
                .error {{
                    background: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    border: 1px solid #f5c6cb;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🔐 Document Access</h2>
                {error_html}
                <form method="post">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
                <div class="footer">
                    Recruitee MCP Server - Document Access
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=login_html)
