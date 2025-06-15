import json
from typing import Dict, List, Optional, Literal
from datetime import datetime

import httpx
from async_lru import alru_cache
from pydantic import BaseModel, Field, field_validator

from server_config import mcp, RECRUITEE_COMPANY_ID, RECRUITEE_API_TOKEN



_API = f"https://api.recruitee.com/c/{RECRUITEE_COMPANY_ID}"
_HEADERS = {"Authorization": f"Bearer {RECRUITEE_API_TOKEN}"}
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


async def _get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"{_API}{path}", headers=_HEADERS, params=params)
        resp.raise_for_status()
        return resp.json()


def iso_to_unix(iso_string: str) -> int:
    """
    Converts an ISO 8601 formatted date string to a Unix timestamp (seconds since epoch).
    Args:
        iso_string (str): ISO date string like '2025-05-20T12:30:00Z' or '2025-05-20T12:30:00+00:00'
    Returns:
        int: Unix timestamp (seconds since 1970-01-01T00:00:00Z)
    """
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return int(dt.timestamp())


@alru_cache(ttl=900)
async def _fetch_offers() -> list[dict]:
    data = await _get("/offers")
    return data.get("offers", [])

@mcp.tool()
async def list_offers() -> list[dict]:
    """Return all job offers (ID + title)."""
    return [{"id": o["id"], "title": o["title"], "status": o["status"], "priority": o["priority"]} for o in await _fetch_offers()]

@mcp.tool()
async def get_offer_details(offer_id: int) -> dict:
    """Return full available offer data."""
    data = await _get(f"/offers/{offer_id}")
    return data.get("offer", {})

@mcp.tool()
async def get_offer_stages(offer_id: int) -> list[dict]:
    """Return all pipeline stages for the given offer (ID + name + category + group)."""
    data = await _get(f"/offers/{offer_id}")
    data = data.get("offer", {}).get("pipeline_template", {}).get("stages", [])
    return [
        {"id": s["id"], "name": s["name"], "category": s["category"], "group": s["group"]}
        for s in data
    ]


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
async def list_candidate_tags() -> list[dict]:
    """Return every configured candidate tag (ID + name + count)."""
    return [{"id": t["id"], "name": t["name"], "count": t["taggings_count"]} for t in await _fetch_tags()]


class CandidateSearchFilter(BaseModel):
    offer_ids: Optional[List[int]] = Field(None, description="List of offer ids on which the candidate applied from 'list_offers'.")

    disqualify_reasons: Optional[List[str]] = Field(None, description="Rejection reason names from 'list_disqualify_reasons'.")
    is_disqualified: Optional[bool] = Field(None, description="True if the candidate is disqualified, False otherwise.")

    candidate_tag_ids: Optional[List[int]] = Field(None, description="Candidate tag ids from 'list_candidate_tags'.")

    skills: Optional[List[str]] = Field(None, description="Required skill keywords.")
    skills_combiner: Optional[Literal["in", "not_in", "contains", "not_contains", "has_all_of"]] = Field("in", description="Combiner for skills. This field is required if 'skills' is set.")

    talent_pools: Optional[List[int]] = Field(None, description="Talent-pool ids from 'list_talent_pools'.")
    talent_pools_combiner: Optional[Literal["in", "not_in", "all_in"]] = Field("in", description="Combiner for talent pools. This field is required if 'talent_pools' is set.")

    has_stage: Optional[bool] = Field(None, description="True if the candidate has a stage, False otherwise.")
    on_stage: Optional[List[str]] = Field(None, description="Stage names from 'list_stages'.")

    gdpr_expires_from: Optional[str] = Field(None, description="Earliest GDPR expiration date (ISO 8601 formatted date string).")
    gdpr_expires_to: Optional[str] = Field(None, description="Latest GDPR expiration date (ISO 8601 formatted date string).")

    created_from: Optional[str] = Field(None, description="Earliest creation date (ISO 8601 formatted date string)")
    created_to: Optional[str] = Field(None, description="Latest creation date (ISO 8601 formatted date string)")

    limit: int = Field(100, description="Page size (max 10 000)")
    offset: int = Field(0, description="Paging offset")

    @field_validator("limit")
    def _limit_max(cls, v: int) -> int:
        if v > 10_000:
            raise ValueError("Recruitee caps limit at 10 000 per call.")
        return v

@mcp.tool()
async def search_candidates(search_filter: CandidateSearchFilter) -> list[dict]:
    """Return basic data for candidates who match a multi-field filter.
Helper tools convert human-readable names to IDs using cached look-ups."""

    filters: List[Dict] = []
    if search_filter.offer_ids:
        filters.append({"filter": "jobs", "id": {"in": search_filter.offer_ids}})

    if search_filter.disqualify_reasons:
        filters.append({"filter":"disqualifies", "reason":{"in":search_filter.disqualify_reasons}})

    if search_filter.is_disqualified is not None:
        if search_filter.is_disqualified:
            filters.append({"filter":"disqualifies", "reason":{"has_any":True}})
        else:
            filters.append({"filter":"disqualifies", "reason":{"has_none":True}})

    if search_filter.candidate_tag_ids:
        filters.append({"filter":"tags", "id":{"in":search_filter.candidate_tag_ids}})

    if search_filter.skills and search_filter.skills_combiner:
        filters.append({"filter":"skills", "text":{search_filter.skills_combiner: search_filter.skills}})

    if search_filter.talent_pools and search_filter.talent_pools_combiner:
        filters.append({"filter":"talent_pools", "id":{search_filter.talent_pools_combiner: search_filter.talent_pools}})

    if search_filter.has_stage is not None:
        if search_filter.has_stage:
            filters.append({"filter":"stages", "has_any":True})
        else:
            filters.append({"filter":"stages", "has_none":True})
    if search_filter.on_stage is not None:
        filters.append({"filter":"stages", "name": {"in": search_filter.on_stage}})

    if search_filter.gdpr_expires_from or search_filter.gdpr_expires_to:
        expires = {}
        if search_filter.created_from:
            expires["gte"] = iso_to_unix(search_filter.gdpr_expires_from)
        if search_filter.created_to:
            expires["lte"] = iso_to_unix(search_filter.gdpr_expires_to)
        filters.append({"field": "gdpr_expires_at", **expires})

    if search_filter.created_from or search_filter.created_to:
        created = {}
        if search_filter.created_from:
            created["gte"] = iso_to_unix(search_filter.created_from)
        if search_filter.created_to:
            created["lte"] = iso_to_unix(search_filter.created_to)
        filters.append({"field": "created_at", **created})

    params = {
        "limit": search_filter.limit,
        "offset": search_filter.offset,
        "filters_json": json.dumps(filters),
    }

    data = await _get("/search/new/candidates", params=params)
    return [{"id": c["id"], "name": c["name"], "emails": c["emails"]} for c in data.get("hits", [])]

@mcp.tool()
async def search_candidate_by_query(query: str, search_name: bool = False, limit: int = 100, offset: int = 0) -> list[dict]:
    """Search candidates using a full-text query across name, email, and other fields.
If `search_name` is False, only return candidates whose name exactly matches the query."""

    if not query:
        return []
    if limit > 10_000:
        raise ValueError("Recruitee caps limit at 10 000 per call.")

    filters = [{"field": "all", "query": query}]
    params = {
        "limit": limit,
        "offset": offset,
        "filters_json": json.dumps(filters),
    }
    data = await _get("/search/new/candidates", params=params)
    return [
        {"id": c["id"], "name": c["name"], "emails": c["emails"]}
        for c in data.get("hits", [])
        if not search_name or c["name"] == query
    ]

@mcp.tool()
async def get_candidates_details(candidate_ids: list[int], fields: list[str]) -> list[dict]:
    """Return specific fields or full available candidates data by their IDs.
If fields are empty, return all fields. Find available fields using 'list_candidate_fields'."""
    if not candidate_ids:
        return []

    details = []
    for candidate_id in candidate_ids:
        data = await _get(f"/candidates/{candidate_id}")
        candidate_data = data.get("candidate", {})
        if not fields:
            details.append(candidate_data)
        else:
            filtered_data = {field: candidate_data.get(field) for field in fields if field in candidate_data}
            details.append(filtered_data)

    return details

@mcp.tool()
async def list_candidate_fields() -> list[str]:
    """List all available candidate fields that can be requested in e.g. 'get_candidates_details'."""

    data = await _get("/search/new/candidates", params={"limit": 1, "offset": 0})
    data = data.get("hits", [])
    if len(data) == 0:
        return []
    example_id = data[0]["id"]
    candidate_details = await get_candidates_details([example_id], [])
    return list(candidate_details[0].keys())


@mcp.tool()
async def get_candidate_notes(candidate_id: int, limit: int = 100, offset: int = 0) -> list[dict]:
    """Fetch plain-text notes attached to a candidate profile."""
    params = {"limit": limit, "offset": offset}
    data = await _get(f"/candidates/{candidate_id}/notes", params=params)
    return data.get("notes", [])

@mcp.tool()
async def get_offer_notes(offer_id: int, limit: int = 100, offset: int = 0) -> list[dict]:
    """Fetch plain-text notes attached to an offer."""
    params = {"limit": limit, "offset": offset}
    data = await _get(f"/offers/{offer_id}/notes", params=params)
    return data.get("notes", [])


if __name__ == "__main__":
    import asyncio
    search_filters = CandidateSearchFilter(talent_pools=[1853826], is_disqualified=True, on_stage=["Applied"])
    x = asyncio.run(search_candidates(search_filters))

    print(f"{x}\n{len(x)}")
