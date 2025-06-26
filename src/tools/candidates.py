from typing import Dict, List, Optional, Literal
import json

from pydantic import BaseModel, Field, field_validator

from src.utils.server_config import mcp
from src.tools.utils import _get, iso_to_unix



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

    custom_fields: Optional[str] = Field(None, description="Custom field 'search_key' from 'list_custom_fields'.")
    custom_fields_combiner: Optional[Literal["has_any", "has_none"]] = Field(None, description="Type of filter for custom fields. This field is required if 'custom_fields' is set.")

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

    if search_filter.custom_fields and search_filter.custom_fields_combiner:
        filters.append({"filter": search_filter.custom_fields, search_filter.custom_fields_combiner: True})

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

async def _get_candidates_details(candidate_ids: list[int], fields: list[str]) -> list[dict]:
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
async def get_candidates_details(candidate_ids: list[int], fields: list[str]) -> list[dict]:
    """Return specific fields or full available candidates data by their IDs.
If fields are empty, return all fields. Find available fields using 'list_candidate_fields'."""
    details = await _get_candidates_details(candidate_ids, fields)
    return details

@mcp.tool()
async def list_candidate_fields() -> list[str]:
    """List all available candidate fields that can be requested in e.g. 'get_candidates_details'."""

    data = await _get("/search/new/candidates", params={"limit": 1, "offset": 0})
    data = data.get("hits", [])
    if len(data) == 0:
        return []
    example_id = data[0]["id"]
    candidate_details = await _get_candidates_details([example_id], [])
    return list(candidate_details[0].keys())


@mcp.tool()
async def get_candidate_notes(candidate_id: int, limit: int = 100, offset: int = 0) -> list[dict]:
    """Fetch plain-text notes attached to a candidate profile."""
    params = {"limit": limit, "offset": offset}
    data = await _get(f"/candidates/{candidate_id}/notes", params=params)
    return data.get("notes", [])


if __name__ == "__main__":
    import asyncio

    search_filters = CandidateSearchFilter(talent_pools=[1853826], is_disqualified=True, on_stage=["Applied"])
    x = asyncio.run(search_candidates(search_filters))
    print(f"{x}\n{len(x)}")