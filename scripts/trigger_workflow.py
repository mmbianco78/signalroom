#!/usr/bin/env python
"""Trigger a Temporal workflow manually (for testing/debugging)."""

import argparse
import asyncio

from signalroom.common import get_logger
from signalroom.common.logging import configure_logging
from signalroom.pipelines.runner import SOURCES
from signalroom.temporal.config import get_temporal_client
from signalroom.temporal.workflows import SyncSourceInput, SyncSourceWorkflow

log = get_logger(__name__)


async def trigger_sync(
    source_name: str,
    resources: list[str] | None = None,
    wait: bool = False,
) -> None:
    """Trigger a SyncSourceWorkflow.

    Args:
        source_name: Source to sync.
        resources: Specific resources to sync.
        wait: If True, wait for workflow to complete.
    """
    client = await get_temporal_client()

    workflow_id = f"sync-{source_name}-manual"

    handle = await client.start_workflow(
        SyncSourceWorkflow.run,
        SyncSourceInput(
            source_name=source_name,
            resources=resources,
            notify_on_failure=True,
            notify_on_success=False,
        ),
        id=workflow_id,
        task_queue="api-tasks",
    )

    log.info("workflow_started", workflow_id=workflow_id, run_id=handle.result_run_id)
    print(f"Workflow started: {workflow_id}")
    print(f"View in UI: http://localhost:8080/namespaces/default/workflows/{workflow_id}")

    if wait:
        print("Waiting for completion...")
        result = await handle.result()
        print(f"Result: {result}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Trigger a sync workflow")
    parser.add_argument(
        "source",
        choices=list(SOURCES.keys()),
        help="Source to sync",
    )
    parser.add_argument(
        "--resources",
        "-r",
        nargs="+",
        help="Specific resources to sync (default: all)",
    )
    parser.add_argument(
        "--wait",
        "-w",
        action="store_true",
        help="Wait for workflow to complete",
    )
    args = parser.parse_args()

    configure_logging(json_output=False, level="INFO")

    asyncio.run(trigger_sync(args.source, args.resources, args.wait))


if __name__ == "__main__":
    main()
