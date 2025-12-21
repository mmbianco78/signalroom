"""Everflow reporting API source.

Ingests affiliate conversion and revenue data from Everflow's entity table API.
Groups by date and affiliate for daily performance tracking.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import dlt
import httpx
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


class EverflowClient:
    """Client for Everflow Network API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize Everflow client.

        Args:
            api_key: Everflow API key. Defaults to settings.
            base_url: Everflow base URL. Defaults to settings.
        """
        self.api_key = api_key or settings.everflow_api_key.get_secret_value()
        self.base_url = base_url or settings.everflow_base_url

        if not self.api_key:
            raise ValueError("Everflow API key not configured. Set EVERFLOW_API_KEY in .env")

    def _headers(self) -> dict[str, str]:
        """Get request headers with auth."""
        return {
            "X-Eflow-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def entity_table(
        self,
        start_date: str,
        end_date: str,
        advertiser_id: int | None = None,
        timezone_id: int = 80,  # 80 = America/New_York
        page: int = 1,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        """Fetch entity table report from Everflow.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            advertiser_id: Filter by advertiser (1=CCW, 2=EXP). None = all.
            timezone_id: Timezone ID (80 = America/New_York).
            page: Page number for pagination.
            limit: Max records per page.

        Returns:
            List of parsed report rows.
        """
        url = f"{self.base_url}/v1/networks/reporting/entity/table"

        # Build filters
        filters = []
        if advertiser_id is not None:
            filters.append({"advertiser_id": advertiser_id})

        payload = {
            "from": start_date,
            "to": end_date,
            "timezone_id": timezone_id,
            "currency_id": "USD",
            "columns": [
                {"column": "affiliate"},
                {"column": "advertiser"},
                {"column": "date"},
            ],
            "query": {
                "filters": filters,
                "page": page,
                "limit": limit,
            },
        }

        log.info(
            "everflow_api_request",
            url=url,
            start_date=start_date,
            end_date=end_date,
            advertiser_id=advertiser_id,
        )

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()

        # Parse response structure
        # {"table": [{"columns": [...], "reporting": {...}}, ...]}
        raw_rows = data.get("table", [])
        parsed_rows = []

        for row in raw_rows:
            columns = {c["column_type"]: c for c in row.get("columns", [])}
            reporting = row.get("reporting", {})

            # Extract column values
            affiliate = columns.get("affiliate", {})
            advertiser = columns.get("advertiser", {})
            date_col = columns.get("date", {})

            # Get advertiser ID and apply client-side filter if needed
            # (API filter may not be reliable)
            adv_id = int(advertiser.get("id", 0)) if advertiser.get("id") else None
            if advertiser_id is not None and adv_id != advertiser_id:
                continue

            # Convert epoch timestamp to date string
            epoch = int(date_col.get("id", 0))
            date_str = (
                datetime.fromtimestamp(epoch, tz=UTC).strftime("%Y-%m-%d")
                if epoch
                else None
            )

            parsed_rows.append(
                {
                    "date": date_str,
                    "affiliate_id": int(affiliate.get("id", 0)) if affiliate.get("id") else None,
                    "affiliate_label": affiliate.get("label"),
                    "advertiser_id": adv_id,
                    "advertiser_label": advertiser.get("label"),
                    "clicks": int(reporting.get("total_click", 0) or 0),
                    "conversions": int(reporting.get("cv", 0) or 0),
                    "revenue": float(reporting.get("revenue", 0) or 0),
                    "payout": float(reporting.get("payout", 0) or 0),
                    "profit": float(reporting.get("profit", 0) or 0),
                }
            )

        log.info("everflow_api_response", row_count=len(parsed_rows))
        return parsed_rows


# Initial value for incremental loading - set to current max date in database
# This ensures we don't re-fetch historical data on first run with incremental
EVERFLOW_INITIAL_DATE = "2025-12-20"


@dlt.source(name="everflow")
def everflow(
    advertiser_id: int | None = None,
    client_id: str = "713",
    api_key: str | None = None,
) -> list[DltResource]:
    """Source for Everflow affiliate performance data.

    Uses dlt incremental loading to automatically track the last processed date.
    On each run, fetches data from last processed date to yesterday.

    Args:
        advertiser_id: Filter by advertiser (1=CCW, 2=EXP). None = all.
        client_id: Client identifier for tagging data.
        api_key: Everflow API key. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    ef_client = EverflowClient(api_key=api_key)

    @dlt.resource(
        name="daily_stats",
        write_disposition="merge",
        primary_key=["date", "affiliate_id", "advertiser_id"],
    )
    def daily_stats(
        date_cursor: dlt.sources.incremental[str] = dlt.sources.incremental(
            "date",
            initial_value=EVERFLOW_INITIAL_DATE,
        ),
    ) -> Iterator[dict[str, Any]]:
        """Load daily affiliate stats from Everflow.

        Uses dlt incremental to track last processed date.
        Merge write disposition updates existing records if re-run.

        Args:
            date_cursor: dlt incremental tracker for the date field.
                Automatically tracks max(date) from yielded rows.
        """
        # Calculate date range:
        # - start_date: from incremental state (last processed date)
        # - end_date: yesterday (data is finalized at end of day)
        start_date = date_cursor.start_value
        end_date = (date.today() - timedelta(days=1)).isoformat()

        # Skip if we're already caught up (start > end can happen if run twice same day)
        if start_date > end_date:
            log.info(
                "everflow_already_current",
                start_value=start_date,
                end_date=end_date,
                message="No new data to fetch",
            )
            return

        log.info(
            "fetching_daily_stats",
            start_date=start_date,
            end_date=end_date,
            incremental_start_value=date_cursor.start_value,
            advertiser_id=advertiser_id,
        )

        rows = ef_client.entity_table(
            start_date=start_date,
            end_date=end_date,
            advertiser_id=advertiser_id,
        )

        for row in rows:
            # Add metadata columns
            row["_client_id"] = client_id
            row["_loaded_at"] = datetime.now(UTC).isoformat()
            yield row

        log.info(
            "everflow_fetch_complete",
            rows_yielded=len(rows),
            start_date=start_date,
            end_date=end_date,
        )

    return [daily_stats]
