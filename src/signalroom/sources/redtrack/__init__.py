"""Redtrack reporting API source.

Ingests conversion and campaign data from Redtrack's reporting API.
"""

from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


@dlt.source(name="redtrack")
def redtrack(
    api_key: str | None = None,
) -> list[DltResource]:
    """Source for Redtrack reporting data.

    Args:
        api_key: Redtrack API key. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    api_key = api_key or settings.redtrack_api_key.get_secret_value()

    @dlt.resource(
        name="conversions",
        write_disposition="append",
        primary_key="id",
    )
    def conversions(
        updated_after: dlt.sources.incremental[datetime] = dlt.sources.incremental(
            "created_at",
            initial_value=datetime.now() - timedelta(days=30),
        ),
    ) -> Iterator[dict[str, Any]]:
        """Load conversions from Redtrack."""
        import httpx

        # TODO: Implement actual Redtrack API calls
        # See Redtrack API documentation for exact endpoints and parameters
        log.info("fetching_redtrack_conversions", since=updated_after.last_value)

        # Placeholder - implement actual API calls
        yield from []

    @dlt.resource(
        name="campaigns",
        write_disposition="merge",
        primary_key="id",
    )
    def campaigns() -> Iterator[dict[str, Any]]:
        """Load campaign definitions from Redtrack."""
        log.info("fetching_redtrack_campaigns")
        # TODO: Implement
        yield from []

    return [conversions, campaigns]
