from __future__ import annotations

import json
from typing import Dict, List, Optional, Literal

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


@alru_cache(ttl=900)
async def _fetch_offers() -> list[dict]:
    data = await _get("/offers")
    return data.get("offers", [])

@mcp.tool()
async def list_offers() -> list[dict]:
    """Return all job offers (ID + title)."""
    return [{"id": o["id"], "title": o["title"]} for o in await _fetch_offers()]

@mcp.tool()
async def get_offer(offer_id: int) -> dict:
    """Return full available offer data."""
    data = await _get(f"/offers/{offer_id}")
    return data.get("offer", {})


@alru_cache(ttl=900)
async def _fetch_talent_pools() -> list[dict]:
    data = await _get("/talent_pools")
    return data.get("talent_pools", [])

@mcp.tool()
async def list_talent_pools(scope: Literal["not_archived", "archived", "all"]="not_archived") -> list[dict]:
    """Return all talent pools (ID + name + status) with optional status filter."""
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

@mcp.tool()
async def get_talent_pool(talent_pool_id: int) -> dict:
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


@mcp.tool()
async def list_stages(offer_id: int) -> list[dict]:
    """Return all pipeline stages for the given offer (ID + name + category + group)."""
    data = await _get(f"/offers/{offer_id}")
    data = data.get("offer", {}).get("pipeline_template", {}).get("stages", [])
    return [
        {"id": s["id"], "name": s["name"], "category": s["category"], "group": s["group"]}
        for s in data
    ]



class CandidateSearchFilter(BaseModel):
    job_ids: Optional[List[int]] = Field(None, description="List of job/position ids on which the candidate applied from 'list_jobs'.")

    disqualify_reasons: Optional[List[str]] = Field(None, description="Rejection reason names from 'list_disqualify_reasons'.")
    is_disqualified: Optional[bool] = Field(None, description="True if the candidate is disqualified, False otherwise.")

    candidate_tag_ids: Optional[List[int]] = Field(None, description="Candidate tag ids from 'list_candidate_tags'.")

    skills: Optional[List[str]] = Field(None, description="Required skill keywords.")
    skills_combiner: Optional[Literal["in", "not_in", "contains", "not_contains", "has_all_of"]] = Field("in", description="Combiner for skills. This field is required if 'skills' is set.")

    talent_pools: Optional[List[int]] = Field(None, description="Talent-pool ids from 'list_talent_pools'.")
    talent_pools_combiner: Optional[Literal["in", "not_in", "all_in"]] = Field("in", description="Combiner for talent pools. This field is required if 'talent_pools' is set.")

    created_from: Optional[int] = Field(None, description="Earliest creation date (Unix timestamp)")
    created_to: Optional[int] = Field(None, description="Latest creation date (Unix timestamp)")

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
Helper tools convert human-readable names to IDs using cached look-ups.
    """

    filters: List[Dict] = []
    if search_filter.job_ids:
        filters.append({"filter": "jobs", "id": {"in": search_filter.job_ids}})

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

    if search_filter.created_from or search_filter.created_to:
        created = {}
        if search_filter.created_from:
            created["gte"] = search_filter.created_from
        if search_filter.created_to:
            created["lte"] = search_filter.created_to
        filters.append({"field": "created_at", **created})

    params = {
        "limit": search_filter.limit,
        "offset": search_filter.offset,
        "filters_json": json.dumps(filters),
    }

    data = await _get("/search/new/candidates", params=params)
    return [{"id": c["id"], "name": c["name"]} for c in data.get("hits", [])]

@mcp.tool()
async def get_candidate(candidate_id: int) -> dict:
    """Return full available candidate data."""
    data = await _get(f"/candidates/{candidate_id}")
    return data.get("candidate", {})


if __name__ == "__main__":
    import asyncio
    search_filters = CandidateSearchFilter(talent_pools=[2118301], is_disqualified=True)
    x = asyncio.run(search_candidates(search_filters))
    print(f"{x}\n{len(x)}")
