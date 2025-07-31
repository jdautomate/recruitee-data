from async_lru import alru_cache

from src.utils.server_config import mcp
from src.tools.utils import _get



@alru_cache(ttl=900)
async def _fetch_offers() -> list[dict]:
    data = await _get("/offers")
    return data.get("offers", [])

@mcp.tool()
async def list_offers() -> list[dict]:
    """Return all job offers (ID + title)."""
    return [{"id": o["id"], "title": o["title"], "status": o["status"], "priority": o["priority"]} for o in await _fetch_offers()]

async def _get_offers_details(offer_ids: list[int], fields: list[str]) -> dict[int, dict]:
    """Helper function to get offer details with optional field filtering."""
    if not offer_ids:
        return []

    details = {}
    for offer_id in offer_ids:
        data = await _get(f"/offers/{offer_id}")
        offer_data = data.get("offer", {})
        if not fields:
            details[offer_id] = offer_data
        else:
            filtered_data = {field: offer_data.get(field, "Field doesn't exist") for field in fields}
            details[offer_id] = filtered_data

    return details

@mcp.tool()
async def get_offers_details(offer_ids: list[int], fields: list[str]) -> dict[int, dict]:
    """Return specific fields or full available offer data by their IDs.
If fields are empty, return all fields. Find available fields using 'list_offer_fields'."""
    details = await _get_offers_details(offer_ids, fields)
    return details

@mcp.tool()
async def list_offer_fields() -> list[str]:
    """List all available offer fields that can be requested in e.g. 'get_offers_details'."""
    offers = await _fetch_offers()
    if len(offers) == 0:
        return []
    return list(offers[0].keys())

@mcp.tool()
async def get_offer_stages(offer_id: int) -> list[dict]:
    """Return all pipeline stages for the given offer (ID + name + category + group)."""
    data = await _get(f"/offers/{offer_id}")
    data = data.get("offer", {}).get("pipeline_template", {}).get("stages", [])
    return [
        {"id": s["id"], "name": s["name"], "category": s["category"], "group": s["group"]}
        for s in data
    ]

if __name__ == "__main__":
    import asyncio
    x = asyncio.run(get_offers_details([2218442, 2216242], ["created_at", "deleted_at"]))
    print(f"{x}\n{len(x)}")