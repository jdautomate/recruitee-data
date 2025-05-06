from __future__ import annotations

from typing import Dict, List, Optional, Literal

import httpx
from async_lru import alru_cache
from pydantic import BaseModel, Field, validator

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
async def _fetch_offers(kind: str) -> list[dict]:
    data = await _get("/offers", params={"kind": kind})
    return data.get("offers", [])

@alru_cache(ttl=900)
async def _fetch_talent_pools() -> list[dict]:
    data = await _get("/talent_pools")
    return data.get("talent_pools", [])

@alru_cache(ttl=900)
async def _fetch_disqualify_reasons() -> list[dict]:
    data = await _get("/disqualify_reasons")
    return data.get("disqualify_reasons", [])



@mcp.tool()
async def list_jobs() -> list[dict]:
    """Return all job offers (ID + title)."""
    return [{"id": o["id"], "title": o["title"]} for o in await _fetch_offers("job")]


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
async def list_disqualify_reasons() -> list[dict]:
    """Return every configured disqualify reason (ID + name)."""
    return [{"id": d["id"], "name": d["name"]} for d in await _fetch_disqualify_reasons()]


class CandidateSearchFilter(BaseModel):
    skills: Optional[List[str]] = Field(None, description="Required skill keywords (AND-combined)")
    disqualify_reasons: Optional[List[str]] = Field(None, description="Rejection reason names")
    talent_pools: Optional[List[str]] = Field(None, description="Talent-pool names")
    job_titles: Optional[List[str]] = Field(None, description="Job/position titles")
    created_from: Optional[int] = Field(None, description="Earliest creation date (Unix timestamp)")
    created_to: Optional[int] = Field(None, description="Latest creation date (Unix timestamp)")
    limit: int = Field(100, description="Page size (max 10 000)")
    offset: int = Field(0, description="Paging offset")

    @validator("limit")
    def _limit_max(cls, v):
        if v > 10_000:
            raise ValueError("Recruitee caps limit at 10 000 per call.")
        return v



@mcp.tool()
async def search_candidates(filter: CandidateSearchFilter) -> list[dict]:
    """
    Return basic data for candidates who match a multi-field filter.
    Helper tools convert human-readable names to IDs using cached look-ups.
    """
    # ----- convert names → IDs ----------------------------------------------
    job_map = {j["title"]: j["id"] for j in await list_jobs()}
    pool_map = {p["name"]: p["id"] for p in await list_talent_pools()}
    dq_map = {d["name"]: d["id"] for d in await list_disqualify_reasons()}

    def _ids(requested: Optional[list[str]], mapping: dict[str, int]) -> list[int]:
        if not requested:
            return []
        missing = [n for n in requested if n not in mapping]
        if missing:
            raise ValueError(f"Unknown names: {', '.join(missing)}")
        return [mapping[n] for n in requested]

    job_ids = _ids(filter.job_titles, job_map)
    pool_ids = _ids(filter.talent_pools, pool_map)
    dq_ids = _ids(filter.disqualify_reasons, dq_map)

    # ----- build /search/new/candidates filter array ------------------------
    filters: List[Dict] = []
    if filter.skills:
        filters.append({"filter": "skills", "text": {"contains": filter.skills}})
    if dq_ids:
        filters.append({"filter": "disqualifies", "reason": {"in": dq_ids}})
    if pool_ids:
        filters.append({"filter": "talent_pools", "id": {"in": pool_ids}})
    if job_ids:
        filters.append({"filter": "jobs", "id": {"in": job_ids}})
    if filter.created_from or filter.created_to:
        created = {}
        if filter.created_from:
            created["gte"] = filter.created_from
        if filter.created_to:
            created["lte"] = filter.created_to
        filters.append({"field": "created_at", **created})

    params = {"filters": filters, "limit": filter.limit, "offset": filter.offset}
    data = await _get("/search/new/candidates", params=params)
    return [{"id": c["id"], "name": c["name"]} for c in data.get("candidates", [])]