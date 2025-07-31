from typing import Literal

from async_lru import alru_cache

from src.utils.server_config import mcp
from src.tools.utils import _get



@alru_cache(ttl=900)
async def _fetch_talent_pools() -> list[dict]:
    data = await _get("/talent_pools")
    return data.get("talent_pools", [])

@mcp.tool()
async def list_talent_pools(scope: Literal["not_archived", "archived", "all"]="not_archived") -> list[dict]:
    """Return all talent pools (ID + name + status) with an optional status filter."""
    if scope == "all":
        return [
            {"id": tp["id"], "title": tp["title"], "status": tp["status"]}
            for tp in await _fetch_talent_pools()
        ]
    elif scope == "not_archived":
        return [
            {"id": tp["id"], "title": tp["title"], "status": tp["status"]}
            for tp in await _fetch_talent_pools()
            if tp["status"] != "archived"
        ]
    elif scope == "archived":
        return [
            {"id": tp["id"], "title": tp["title"], "status": tp["status"]}
            for tp in await _fetch_talent_pools()
            if tp["status"] == "archived"
        ]
    else:
        raise ValueError("Invalid scope. Use 'not_archived', 'archived', or 'all'.")

@mcp.tool()
async def get_talent_pool_details(talent_pool_id: int) -> dict:
    """Return full details for a specific talent pool by ID."""
    data = await _get(f"/talent_pools/{talent_pool_id}")
    return data.get("talent_pool", {})


@alru_cache(ttl=900)
async def _fetch_disqualify_reasons() -> list[dict]:
    data = await _get("/disqualify_reasons")
    return data.get("disqualify_reasons", [])

@mcp.tool()
async def list_disqualify_reasons() -> list[dict]:
    """Return every configured disqualify reason (ID + name)."""
    return [{"id": d["id"], "name": d["name"]} for d in await _fetch_disqualify_reasons()]


@alru_cache(ttl=900)
async def _fetch_tags() -> list[dict]:
    data = await _get("/tags")
    return data.get("tags", [])

@mcp.tool()
async def list_tags() -> list[dict]:
    """Return every configured candidate tag (ID + name + count)."""
    return [{"id": t["id"], "name": t["name"], "count": t["taggings_count"]} for t in await _fetch_tags()]


@alru_cache(ttl=900)
async def _fetch_custom_fields() -> list[dict]:
    data = await _get("/custom_fields/fields/searchable")
    return data.get("fields", [])

@mcp.tool()
async def list_custom_fields() -> list[dict]:
    """Return every searchable custom field."""
    data = await _fetch_custom_fields()
    return data


if __name__ == "__main__":
    import asyncio
    x = asyncio.run(list_tags())
    print(f"{x}\n{len(x)}")
