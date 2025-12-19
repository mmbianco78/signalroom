"""PostHog analytics source.

Ingests events, feature flags, and experiment results from PostHog.
"""

from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


@dlt.source(name="posthog")
def posthog(
    api_key: str | None = None,
    project_id: str | None = None,
    host: str | None = None,
) -> list[DltResource]:
    """Source for PostHog analytics data.

    Args:
        api_key: PostHog personal API key. Defaults to settings.
        project_id: PostHog project ID. Defaults to settings.
        host: PostHog API host. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    api_key = api_key or settings.posthog_api_key.get_secret_value()
    project_id = project_id or settings.posthog_project_id
    host = (host or settings.posthog_host).rstrip("/")

    @dlt.resource(
        name="events",
        write_disposition="append",
        primary_key="uuid",
    )
    def events(
        after: dlt.sources.incremental[str] = dlt.sources.incremental(
            "timestamp",
            initial_value=(datetime.now() - timedelta(days=7)).isoformat(),
        ),
    ) -> Iterator[dict[str, Any]]:
        """Load events from PostHog."""
        import httpx

        log.info("fetching_posthog_events", since=after.last_value)

        with httpx.Client() as client:
            # PostHog events API with pagination
            url = f"{host}/api/projects/{project_id}/events"
            params = {
                "after": after.last_value,
                "limit": 100,
            }

            while True:
                response = client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    break

                yield from results

                # Handle pagination
                if data.get("next"):
                    url = data["next"]
                    params = {}  # Next URL includes params
                else:
                    break

    @dlt.resource(
        name="feature_flags",
        write_disposition="replace",  # Full refresh each time
    )
    def feature_flags() -> Iterator[dict[str, Any]]:
        """Load feature flag definitions from PostHog."""
        import httpx

        log.info("fetching_posthog_feature_flags")

        with httpx.Client() as client:
            response = client.get(
                f"{host}/api/projects/{project_id}/feature_flags",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            data = response.json()

            yield from data.get("results", [])

    @dlt.resource(
        name="experiments",
        write_disposition="merge",
        primary_key="id",
    )
    def experiments() -> Iterator[dict[str, Any]]:
        """Load experiments (A/B tests) with results from PostHog."""
        import httpx

        log.info("fetching_posthog_experiments")

        with httpx.Client() as client:
            response = client.get(
                f"{host}/api/projects/{project_id}/experiments",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            data = response.json()

            yield from data.get("results", [])

    return [events, feature_flags, experiments]
