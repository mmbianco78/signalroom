"""Redtrack reporting API source.

Ingests ad spend and conversion data from Redtrack's reporting API.
Groups by date and traffic source for spend tracking and affiliate mapping.
"""

from collections.abc import Iterator
from datetime import date, datetime, timedelta
from typing import Any

import dlt
import httpx
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


class RedtrackClient:
    """Client for Redtrack Reporting API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize Redtrack client.

        Args:
            api_key: Redtrack API key. Defaults to settings.
            base_url: Redtrack base URL. Defaults to settings.
        """
        self.api_key = api_key or settings.redtrack_api_key.get_secret_value()
        self.base_url = (base_url or settings.redtrack_base_url).rstrip("/")

        if not self.api_key:
            raise ValueError("Redtrack API key not configured. Set REDTRACK_API_KEY in .env")

    def _headers(self) -> dict[str, str]:
        """Get request headers with auth."""
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def report(
        self,
        start_date: str,
        end_date: str,
        timezone: str = "America/New_York",
        group_by: list[str] | None = None,
        columns: list[str] | None = None,
        limit: int = 10000,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Fetch report data from Redtrack.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            timezone: Timezone for date boundaries.
            group_by: Grouping fields. Defaults to ["date", "traffic_source"].
            columns: Metrics to fetch. Defaults to ["clicks", "conversions", "cost"].
            limit: Max records per page.
            page: Page number for pagination.

        Returns:
            List of report rows.
        """
        url = f"{self.base_url}/report"

        # Default groupings for spend tracking
        group_by = group_by or ["date", "traffic_source"]
        columns = columns or ["clicks", "conversions", "cost"]

        payload = {
            "date_from": start_date,
            "date_to": end_date,
            "timezone": timezone,
            "group_by": group_by,
            "columns": columns,
            "filters": {},
            "limit": limit,
            "page": page,
        }

        log.info(
            "redtrack_api_request",
            url=url,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
        )

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()

        # Parse response - can be list or wrapped in object
        rows = []
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            # Try common wrapper keys
            for key in ("rows", "items", "data", "results", "table"):
                if key in data and isinstance(data[key], list):
                    rows = data[key]
                    break

        log.info("redtrack_api_response", row_count=len(rows))
        return rows

    def report_get(
        self,
        start_date: str,
        end_date: str,
        timezone: str = "America/New_York",
        group: str = "source",
        sort_by: str = "clicks",
        direction: str = "desc",
        max_retries: int = 3,
    ) -> list[dict[str, Any]]:
        """Fetch report data using GET endpoint (alternative to POST).

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            timezone: Timezone for date boundaries.
            group: Grouping key (e.g., "source" for traffic source).
            sort_by: Metric to sort by.
            direction: Sort direction (asc/desc).
            max_retries: Max retry attempts for rate limiting.

        Returns:
            List of report rows.
        """
        import time

        url = f"{self.base_url}/report"

        params = {
            "api_key": self.api_key,
            "date_from": start_date,
            "date_to": end_date,
            "timezone": timezone,
            "group": group,
            "sortby": sort_by,
            "direction": direction,
        }

        log.info(
            "redtrack_api_request_get",
            url=url,
            start_date=start_date,
            end_date=end_date,
            group=group,
        )

        # Retry logic with exponential backoff for rate limiting
        last_exception = None
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.get(url, headers=self._headers(), params=params)

                    # Handle rate limiting with retry
                    if response.status_code == 429:
                        wait_time = 2 ** attempt  # 1, 2, 4 seconds
                        log.warning(
                            "redtrack_rate_limited",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            wait_seconds=wait_time,
                        )
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    # Parse response
                    rows = []
                    if isinstance(data, list):
                        rows = data
                    elif isinstance(data, dict):
                        for key in ("rows", "items", "data", "results"):
                            if key in data and isinstance(data[key], list):
                                rows = data[key]
                                break

                    log.info("redtrack_api_response_get", row_count=len(rows))
                    return rows

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    last_exception = e
                    wait_time = 2 ** attempt
                    log.warning(
                        "redtrack_rate_limited",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_seconds=wait_time,
                    )
                    time.sleep(wait_time)
                    continue
                raise

        # All retries exhausted
        log.error("redtrack_rate_limit_exhausted", max_retries=max_retries)
        raise last_exception or Exception("Rate limit retries exhausted")


def _normalize_row(row: dict[str, Any], report_date: str | None = None) -> dict[str, Any]:
    """Normalize a Redtrack row to consistent field names.

    Args:
        row: Raw row from Redtrack API.
        report_date: Date to use if not in row (for single-day reports).

    Returns:
        Normalized row with consistent field names.
    """
    # Extract date - may be in various formats
    row_date = (
        row.get("date")
        or row.get("Date")
        or row.get("day")
        or report_date
    )

    # Extract source info - handle various field names
    source_id = str(
        row.get("source_id")
        or row.get("sourceId")
        or row.get("traffic_source_id")
        or row.get("trafficSourceId")
        or ""
    ).strip()

    source_name = (
        row.get("source")
        or row.get("traffic_source")
        or row.get("trafficSource")
        or row.get("source_name")
        or row.get("sourceName")
        or ""
    )

    source_alias = (
        row.get("source_alias")
        or row.get("sourceAlias")
        or row.get("traffic_source_alias")
        or ""
    )

    # Extract metrics with safe conversion
    def safe_float(val: Any) -> float:
        try:
            return float(val or 0)
        except (ValueError, TypeError):
            return 0.0

    def safe_int(val: Any) -> int:
        try:
            return int(float(val or 0))
        except (ValueError, TypeError):
            return 0

    # Use explicit None checks to handle 0 values correctly
    def get_first_valid(keys: list[str]) -> Any:
        """Get first non-None value from row for given keys."""
        for key in keys:
            val = row.get(key)
            if val is not None:
                return val
        return None

    return {
        "date": row_date,
        "source_id": source_id,
        "source_name": source_name,
        "source_alias": source_alias,
        "clicks": safe_int(get_first_valid(["clicks", "total_clicks"])),
        "conversions": safe_int(get_first_valid(["conversions"])),  # Only use conversions field
        "cost": safe_float(get_first_valid(["cost", "spend", "total_cost"])),
    }


@dlt.source(name="redtrack")
def redtrack(
    start_date: str | None = None,
    end_date: str | None = None,
    client_id: str = "713",
    api_key: str | None = None,
) -> list[DltResource]:
    """Source for Redtrack ad spend and conversion data.

    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to yesterday.
        end_date: End date (YYYY-MM-DD). Defaults to yesterday.
        client_id: Client identifier for tagging data.
        api_key: Redtrack API key. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    # Default to yesterday if no dates provided
    if not start_date:
        yesterday = date.today() - timedelta(days=1)
        start_date = yesterday.isoformat()
    if not end_date:
        end_date = start_date

    rt_client = RedtrackClient(api_key=api_key)

    @dlt.resource(
        name="daily_spend",
        write_disposition="merge",
        primary_key=["date", "source_id"],
    )
    def daily_spend() -> Iterator[dict[str, Any]]:
        """Load daily spend by traffic source from Redtrack.

        Uses merge write disposition to update existing records if re-run.
        Groups by source for each day in the date range.
        """
        from datetime import datetime as dt

        # Parse date range
        start_dt = dt.strptime(start_date, "%Y-%m-%d").date()
        end_dt = dt.strptime(end_date, "%Y-%m-%d").date()

        # Iterate through each day to get date-level granularity
        current_date = start_dt
        total_rows = 0

        while current_date <= end_dt:
            date_str = current_date.isoformat()

            log.info(
                "fetching_daily_spend",
                date=date_str,
            )

            # Use GET endpoint (POST returns 404 for this API)
            rows = rt_client.report_get(
                start_date=date_str,
                end_date=date_str,
            )

            for row in rows:
                normalized = _normalize_row(row, report_date=date_str)

                # Skip rows without source_id
                if not normalized["source_id"]:
                    continue

                # Add metadata columns
                normalized["_client_id"] = client_id
                normalized["_loaded_at"] = datetime.utcnow().isoformat()

                total_rows += 1
                yield normalized

            # Move to next day with small delay to avoid rate limiting
            current_date += timedelta(days=1)
            if current_date <= end_dt:
                import time
                time.sleep(1)  # 1 second delay between days

        log.info("daily_spend_complete", total_rows=total_rows)

    return [daily_spend]
