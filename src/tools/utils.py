from datetime import datetime
import httpx
import markdown

from src.utils.server_config import mcp, RECRUITEE_COMPANY_ID, RECRUITEE_API_TOKEN



_API = f"https://api.recruitee.com/c/{RECRUITEE_COMPANY_ID}"
_HEADERS = {"Authorization": f"Bearer {RECRUITEE_API_TOKEN}"}
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


async def _get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(f"{_API}{path}", headers=_HEADERS, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Recruitee API failed: {e.response.status_code}, {e.response.text}")


def iso_to_unix(iso_string: str) -> int:
    """
    Converts an ISO 8601 formatted date string to a Unix timestamp (seconds since epoch).
    Args:
        iso_string (str): ISO date string like '2025-05-20T12:30:00Z' or '2025-05-20T12:30:00+00:00'
    Returns:
        int: Unix timestamp (seconds since 1970-01-01T00:00:00Z)
    """
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception as e:
        raise ValueError(f"Invalid ISO date string: {iso_string}") from e


@mcp.tool()
async def markdown_to_html(markdown_str: str) -> str:
    """Convert Markdown text to HTML and return URL to rendered HTML resource."""
    if not markdown_str:
        return ""
    try:
        html = markdown.markdown(
            markdown_str,
            extensions=["extra", "codehilite"]
        )
        
        # Use StaticResource instead of Resource
        from fastmcp.resources import StaticResource
        
        resource_uri = f"/html/{datetime.now().timestamp()}"
        resource = StaticResource(
            uri=resource_uri,
            content=html,
            mimeType="text/html"
        )
        
        resource_url = mcp.add_resource(resource)
        return resource_url
    except Exception as e:
        raise ValueError(f"Error converting Markdown to HTML: {e}") from e