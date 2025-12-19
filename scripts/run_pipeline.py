#!/usr/bin/env python
"""Run a dlt pipeline manually (for testing/debugging)."""

import argparse
import sys

from signalroom.common import get_logger
from signalroom.common.logging import configure_logging
from signalroom.pipelines import run_pipeline
from signalroom.pipelines.runner import SOURCES

log = get_logger(__name__)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run a dlt pipeline manually")
    parser.add_argument(
        "source",
        choices=list(SOURCES.keys()),
        help="Source to run",
    )
    parser.add_argument(
        "--resources",
        "-r",
        nargs="+",
        help="Specific resources to run (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without running",
    )
    args = parser.parse_args()

    configure_logging(json_output=False, level="DEBUG")

    if args.dry_run:
        log.info("dry_run", source=args.source, resources=args.resources)
        print(f"Would run pipeline: {args.source}")
        print(f"Resources: {args.resources or 'all'}")
        return

    try:
        result = run_pipeline(
            source_name=args.source,
            resources=args.resources,
        )
        print(f"\nPipeline completed successfully!")
        print(f"Load ID: {result['load_id']}")
        print(f"Row counts: {result['row_counts']}")

    except Exception as e:
        log.error("pipeline_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
