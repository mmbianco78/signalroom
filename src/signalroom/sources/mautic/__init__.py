"""Mautic marketing automation source.

Ingests contacts, emails, and campaign data from a self-hosted Mautic instance.
Uses Mautic's REST API v3.
"""

from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


@dlt.source(name="mautic")
def mautic(
    base_url: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> list[DltResource]:
    """Source for Mautic marketing automation data.

    Args:
        base_url: Mautic instance URL. Defaults to settings.
        client_id: OAuth client ID. Defaults to settings.
        client_secret: OAuth client secret. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    base_url = (base_url or settings.mautic_base_url).rstrip("/")
    client_id = client_id or settings.mautic_client_id
    client_secret = client_secret or settings.mautic_client_secret.get_secret_value()

    def _get_access_token() -> str:
        """Get OAuth access token from Mautic."""
        import httpx

        # TODO: Implement token caching and refresh
        response = httpx.post(
            f"{base_url}/oauth/v2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _paginate_mautic(
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Paginate through Mautic API results."""
        import httpx

        token = _get_access_token()
        params = params or {}
        params.setdefault("limit", 100)
        params.setdefault("start", 0)

        with httpx.Client() as client:
            while True:
                response = client.get(
                    f"{base_url}/api/{endpoint}",
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                # Mautic returns data keyed by entity type
                # e.g., {"contacts": [...], "total": 100}
                entity_key = endpoint.split("/")[0]
                items = data.get(entity_key, [])

                if not items:
                    break

                # Mautic returns dict with ID keys, not a list
                if isinstance(items, dict):
                    yield from items.values()
                else:
                    yield from items

                # Check if more pages
                total = data.get("total", 0)
                params["start"] += params["limit"]
                if params["start"] >= total:
                    break

    @dlt.resource(
        name="contacts",
        write_disposition="merge",
        primary_key="id",
    )
    def contacts(
        modified_after: dlt.sources.incremental[str] = dlt.sources.incremental(
            "dateModified",
            initial_value=(datetime.now() - timedelta(days=30)).isoformat(),
        ),
    ) -> Iterator[dict[str, Any]]:
        """Load contacts from Mautic."""
        log.info("fetching_mautic_contacts", since=modified_after.last_value)

        params = {
            "search": f"dateModified:>={modified_after.last_value}",
            "orderBy": "dateModified",
            "orderByDir": "asc",
        }

        yield from _paginate_mautic("contacts", params)

    @dlt.resource(
        name="emails",
        write_disposition="merge",
        primary_key="id",
    )
    def emails() -> Iterator[dict[str, Any]]:
        """Load email templates and stats from Mautic."""
        log.info("fetching_mautic_emails")
        yield from _paginate_mautic("emails")

    @dlt.resource(
        name="campaigns",
        write_disposition="merge",
        primary_key="id",
    )
    def campaigns() -> Iterator[dict[str, Any]]:
        """Load campaign definitions from Mautic."""
        log.info("fetching_mautic_campaigns")
        yield from _paginate_mautic("campaigns")

    @dlt.resource(
        name="email_stats",
        write_disposition="append",
    )
    def email_stats() -> Iterator[dict[str, Any]]:
        """Load email send/open/click stats from Mautic."""
        # TODO: Implement email stats endpoint
        log.info("fetching_mautic_email_stats")
        yield from []

    return [contacts, emails, campaigns, email_stats]
