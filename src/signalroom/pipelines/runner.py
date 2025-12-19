"""Generic pipeline runner for dlt sources."""

from typing import Any

import dlt
from dlt.pipeline import Pipeline

from signalroom.common import get_logger, settings

log = get_logger(__name__)

# Registry of available sources
SOURCES = {
    "s3_exports": "signalroom.sources.s3_exports:s3_exports",
    "everflow": "signalroom.sources.everflow:everflow",
    "redtrack": "signalroom.sources.redtrack:redtrack",
    "posthog": "signalroom.sources.posthog:posthog",
    "mautic": "signalroom.sources.mautic:mautic",
    "google_sheets": "signalroom.sources.google_sheets:google_sheets",
}


def get_pipeline(source_name: str) -> Pipeline:
    """Create a dlt pipeline for the given source.

    Args:
        source_name: Name of the source (e.g., "s3_exports").

    Returns:
        Configured dlt pipeline.
    """
    # Create Postgres destination with credentials
    destination = dlt.destinations.postgres(
        credentials=settings.postgres_connection_string,
    )

    return dlt.pipeline(
        pipeline_name=source_name,
        destination=destination,
        dataset_name=source_name,
    )


def get_source(source_name: str, **kwargs: Any) -> Any:
    """Import and instantiate a dlt source by name.

    Args:
        source_name: Name of the source (e.g., "s3_exports").
        **kwargs: Additional arguments passed to the source function.

    Returns:
        dlt source instance.
    """
    if source_name not in SOURCES:
        raise ValueError(f"Unknown source: {source_name}. Available: {list(SOURCES.keys())}")

    module_path, func_name = SOURCES[source_name].rsplit(":", 1)

    # Dynamic import
    import importlib

    module = importlib.import_module(module_path)
    source_func = getattr(module, func_name)

    return source_func(**kwargs)


def run_pipeline(
    source_name: str,
    source_kwargs: dict[str, Any] | None = None,
    resources: list[str] | None = None,
) -> dict[str, Any]:
    """Run a dlt pipeline for the given source.

    Args:
        source_name: Name of the source (e.g., "s3_exports").
        source_kwargs: Additional arguments for the source function.
        resources: Specific resources to run. If None, runs all.

    Returns:
        Dict with load info including row counts and status.
    """
    source_kwargs = source_kwargs or {}

    log.info("pipeline_starting", source=source_name, resources=resources)

    pipeline = get_pipeline(source_name)
    source = get_source(source_name, **source_kwargs)

    # Select specific resources if requested
    if resources:
        source = source.with_resources(*resources)

    # Run the pipeline
    load_info = pipeline.run(source)

    # Extract useful info for logging/tracking
    result = {
        "pipeline_name": source_name,
        "load_ids": load_info.loads_ids,
        "destination": str(load_info.destination_name),
        "dataset": load_info.dataset_name,
        "started_at": str(load_info.started_at),
        "finished_at": str(load_info.finished_at) if load_info.finished_at else None,
        "has_failed_jobs": load_info.has_failed_jobs,
    }

    if load_info.has_failed_jobs:
        log.error("pipeline_failed", **result)
        raise RuntimeError(f"Pipeline {source_name} had failed jobs: {load_info}")

    log.info("pipeline_completed", **result)
    return result
