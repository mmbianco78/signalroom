"""Everflow reporting API source.

Ingests conversion and click data from Everflow's reporting API.
"""

from collections.abc import Iterator
from datetime import date, datetime, timedelta
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)

# Everflow API base URL
API_BASE = "https://api.everflow.io/v1"


@dlt.source(name="everflow")
def everflow(
    api_key: str | None = None,
) -> list[DltResource]:
    """Source for Everflow reporting data.

    Args:
        api_key: Everflow API key. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    api_key = api_key or settings.everflow_api_key.get_secret_value()

    @dlt.resource(
        name="conversions",
        write_disposition="append",
        primary_key="conversion_id",
    )
    def conversions(
        updated_after: dlt.sources.incremental[datetime] = dlt.sources.incremental(
            "created_at",
            initial_value=datetime.now() - timedelta(days=30),
        ),
    ) -> Iterator[dict[str, Any]]:
        """Load conversions from Everflow."""
        import httpx

        # TODO: Implement actual Everflow API calls
        # This is a skeleton - see Everflow API docs for exact endpoints
        log.info(
            "fetching_conversions",
            since=updated_after.last_value,
        )

        with httpx.Client() as client:
            # Example API call structure (adjust to actual Everflow API)
            response = client.get(
                f"{API_BASE}/reports/conversions",
                headers={"Authorization": f"Bearer {api_key}"},
                params={
                    "start_date": updated_after.last_value.isoformat(),
                    "end_date": datetime.now().isoformat(),
                },
            )
            response.raise_for_status()
            data = response.json()

            for conversion in data.get("conversions", []):
                yield conversion

    @dlt.resource(
        name="clicks",
        write_disposition="append",
        primary_key="click_id",
    )
    def clicks(
        updated_after: dlt.sources.incremental[datetime] = dlt.sources.incremental(
            "created_at",
            initial_value=datetime.now() - timedelta(days=7),
        ),
    ) -> Iterator[dict[str, Any]]:
        """Load clicks from Everflow."""
        # TODO: Implement click data ingestion
        log.info("fetching_clicks", since=updated_after.last_value)
        yield from []  # Placeholder

    return [conversions, clicks]
