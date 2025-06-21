import json
from typing import Dict, List, Optional, Literal
from datetime import datetime

import httpx
from async_lru import alru_cache
from pydantic import BaseModel, Field, field_validator

from src.utils.server_config import mcp, RECRUITEE_COMPANY_ID, RECRUITEE_API_TOKEN



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


@alru_cache(ttl=900)
async def _fetch_metrics() -> list[dict]:
    """Fetch metrics data from Recruitee API with caching."""
    data = await _get("/report/metrics")
    return data.get("metrics", [])

@mcp.tool()
async def list_metrics() -> list[dict]:
    """Return available recruitment metrics and statistics. Use 'get_metric_details' to fetch specific metric data."""
    return [{"metric": m["metric"], "name": m["name"], "resource": m["resource"], "kind": m["kind"]} for m in await _fetch_metrics()]

@mcp.tool()
async def get_metric_details(metric: str | list[str]) -> list[dict]:
    """Fetch detailed data for specific metrics, including available filters or groups"""
    # TODO Drop useless fields
    if isinstance(metric, str):
        metric = [metric]
    if not metric:
        return []
    metrics = await _fetch_metrics()
    return [m for m in metrics if m["metric"] in metric]


class MetricQueryParams(BaseModel):
    metric: str = Field(description="Metric type. From list_metrics")
    filters: Optional[str] = Field(None, description="Filters in format type:value;type:value (e.g., job:5;department:10). From get_metric_details -> available_filters")
    primary_group: Optional[str] = Field(None, description="Attribute used to aggregate results. From get_metric_details -> available_groups")

    sort_by: Optional[str] = Field(None, description="Sort results by field. Available when get_metric_details -> is_sortable=true")
    sort_order: Optional[Literal["asc", "desc"]] = Field(None, description="Sort order. Default is descending")

    date_range: Optional[Literal[
        "range", "today", "yesterday", "this_week", "last_week", "this_month", "last_month",
        "this_quarter", "last_quarter", "this_year", "last_year", "last_7_days",
        "last_14_days", "last_30_days", "last_60_days", "last_90_days", "last_365_days"
    ]] = Field(None, description="Date filter range. From get_metric_details -> available_date_filters")
    date_start: Optional[str] = Field(None, description="Start date when using date_range='range'. Format: 'YYYY-MM-DD'.")
    date_end: Optional[str] = Field(None, description="End date when using date_range='range'. Format: 'YYYY-MM-DD'.")

    page: Optional[int] = Field(None, description="Page number used for pagination. Used only with the limit option. Defaults to 1.")
    limit: Optional[int] = Field(None, description="Limit number of results. Defaults to 30.")

    @field_validator("limit")
    def _limit_max(cls, v: int) -> int:
        if v > 10_000:
            raise ValueError("Limit cannot exceed 10,000.")
        return v

    @field_validator("date_start", "date_end")
    def _validate_date_format(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"{info.field_name} must be in 'YYYY-MM-DD' format.")
        return v

class SingleMetricQueryParams(MetricQueryParams):
    date_field: Optional[str] = Field(None, description="Field used for date calculations. From get_metric_details -> available_date_fields")
    date_resource: Optional[str] = Field(None, description="Resource used for filtering by date.")
    include_archived_jobs: Optional[bool] = Field(None, description="Include archived jobs.")
    include_deleted_candidates: Optional[bool] = Field(None, description="Include results for deleted candidates.")

class TrendMetricQueryParams(MetricQueryParams):
    date_field: Optional[str] = Field(None, description="Field used for date calculations. From get_metric_details -> available_date_fields")
    date_resource: Optional[str] = Field(None, description="Resource used for filtering by date.")
    interval: Optional[Literal[
        "daily", "weekly", "monthly", "quarterly"
    ]] = Field("monthly", description="Interval used to group results. Can be: daily, weekly, monthly, quarterly.")
    include_archived_jobs: Optional[bool] = Field(None, description="Include archived jobs.")
    include_deleted_candidates: Optional[bool] = Field(None, description="Include results for deleted candidates.")


class BreakdownMetricQueryParams(MetricQueryParams):
    date_field: Optional[str] = Field(None, description="Field used for date calculations. From get_metric_details -> available_date_fields")
    date_resource: Optional[str] = Field(None, description="Resource used for filtering by date.")
    secondary_group: Optional[str] = Field(None, description="Attribute used for additional, secondary grouping of the results. From get_metric_details -> secondary_groups")
    include_archived_jobs: Optional[bool] = Field(True, description="Include archived jobs.")
    include_archived_requisitions: Optional[bool] = Field(None, description="Include archived requisitions.")
    include_deleted_candidates: Optional[bool] = Field(None, description="Include results for deleted candidates.")
    show_all_data: Optional[bool] = Field(None, description="Disable filtering by date.")

class FunnelMetricQueryParams(MetricQueryParams):
    date_field: Optional[str] = Field(None, description="Field used for date calculations. From get_metric_details -> available_date_fields")
    date_resource: Optional[str] = Field(None, description="Resource used for filtering by date.")

class TimeBasedMetricQueryParams(MetricQueryParams):
    start_point: Optional[Literal[
        "candidate_applied", "candidate_hired", "job_created", "job_published",
        "requisition_approved", "requisition_created", "requisition_sent_for_approval"
    ]] = Field(None, description="Start point for calculating time difference.")
    end_point: Optional[Literal[
        "candidate_disqualified", "candidate_hired", "candidate_start_date",
        "job_closed", "job_created", "job_filled", "job_published",
        "requisition_approved", "requisition_filled", "requisition_sent_for_approval"
    ]] = Field(None, description="End point used to calculate time difference. Possible values are limited based on provided ‘start_point’ parameter.")

    include_archived_jobs: Optional[bool] = Field(None, description="Include archived jobs.")
    include_archived_requisitions: Optional[bool] = Field(None, description="Include archived requisitions.")
    include_deleted_candidates: Optional[bool] = Field(None, description="Include results for deleted candidates.")


@mcp.tool()
async def get_single_metric_data(mqp: SingleMetricQueryParams) -> dict:
    """Fetch data for a single metric based on the provided query parameters, e.g., `fill_rate`. Must match the metric kind"""
    params = mqp.model_dump(exclude_none=True, exclude_defaults=False)
    data = await _get(f"/report/single_metric", params=params)
    return {
        "results": data.get("results", {}),
        "meta": data.get("meta", {})
    }

@mcp.tool()
async def get_trend_metric_data(mqp: TrendMetricQueryParams) -> dict:
    """Fetch trend data for a metric based on the provided query parameters, e.g., `disqualifications_over_time`. Must match the metric kind"""
    params = mqp.model_dump(exclude_none=True, exclude_defaults=False)
    data = await _get(f"/report/trend", params=params)
    return {
        "results": data.get("results", {}),
        "meta": data.get("meta", {})
    }

@mcp.tool()
async def get_breakdown_metric_data(mqp: BreakdownMetricQueryParams) -> dict:
    """Fetch breakdown data for a metric based on the provided query parameters, e.g., `jobs`. Must match the metric kind"""
    params = mqp.model_dump(exclude_none=True, exclude_defaults=False)
    data = await _get(f"/report/breakdown", params=params)
    return {
        "results": data.get("results", {}),
        "meta": data.get("meta", {})
    }

@mcp.tool()
async def get_funnel_metric_data(mqp: FunnelMetricQueryParams) -> dict:
    """Fetch funnel data for a metric based on the provided query parameters, e.g., `dropoff_rate`. Must match the metric kind"""
    params = mqp.model_dump(exclude_none=True, exclude_defaults=False)
    data = await _get(f"/report/funnel", params=params)
    return {
        "results": data.get("results", {}),
        "meta": data.get("meta", {})
    }

@mcp.tool()
async def get_time_based_metric_data(mqp: TimeBasedMetricQueryParams) -> dict:
    """Fetch data for `custom_time_based` metric on the provided query parameters."""
    params = mqp.model_dump(exclude_none=True, exclude_defaults=False)
    data = await _get(f"/report/time_based", params=params)
    return {
        "results": data.get("results", {}),
        "meta": data.get("meta", {})
    }


if __name__ == "__main__":
    import asyncio
    # search_filters = CandidateSearchFilter(talent_pools=[1853826], is_disqualified=True, on_stage=["Applied"])
    # x = asyncio.run(search_candidates(search_filters))

    metric_params = BreakdownMetricQueryParams(metric="disqualifications", primary_group="disqualify-reason", filters="job:2114902")
    x = asyncio.run(get_breakdown_metric_data(metric_params))

    print(f"{x}\n{len(x)}")
