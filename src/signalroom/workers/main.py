"""Main Temporal worker entry point."""

import argparse
import asyncio
import signal
import sys

from temporalio.worker import Worker

from signalroom.common import get_logger, settings
from signalroom.common.logging import configure_logging
from signalroom.temporal.activities import run_pipeline_activity, send_notification_activity
from signalroom.temporal.config import get_temporal_client
from signalroom.temporal.workflows import ScheduledSyncWorkflow, SyncSourceWorkflow

log = get_logger(__name__)


async def run_worker(task_queue: str) -> None:
    """Run the Temporal worker.

    Args:
        task_queue: Task queue to poll.
    """
    log.info(
        "worker_starting",
        task_queue=task_queue,
        temporal_address=settings.temporal_address,
        namespace=settings.temporal_namespace,
    )

    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            SyncSourceWorkflow,
            ScheduledSyncWorkflow,
        ],
        activities=[
            run_pipeline_activity,
            send_notification_activity,
        ],
    )

    # Handle graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        log.info("shutdown_signal_received")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    log.info("worker_ready", task_queue=task_queue)

    # Run until shutdown
    async with worker:
        await shutdown_event.wait()

    log.info("worker_stopped")


def main() -> None:
    """CLI entry point for the worker."""
    parser = argparse.ArgumentParser(description="SignalRoom Temporal Worker")
    parser.add_argument(
        "--queue",
        "-q",
        default=settings.temporal_task_queue,
        help="Task queue to poll (default: api-tasks)",
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Output JSON logs (for production)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level",
    )
    args = parser.parse_args()

    # Reconfigure logging based on CLI args
    configure_logging(json_output=args.json_logs, level=args.log_level)

    try:
        asyncio.run(run_worker(args.queue))
    except KeyboardInterrupt:
        log.info("worker_interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()
