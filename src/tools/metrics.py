from typing import Optional, Literal
from datetime import datetime

from async_lru import alru_cache
from pydantic import BaseModel, Field, field_validator

from src.utils.server_config import mcp
from src.tools.utils import _get



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
        "last_14_days", "last_30_days", "last_60_days", "last_90_days", "last_365_days", "all_time"
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

    metric_params = BreakdownMetricQueryParams(metric="disqualifications", primary_group="disqualify-reason", filters="job:2114902")
    x = asyncio.run(get_breakdown_metric_data(metric_params))
    print(f"{x}")