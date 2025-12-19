"""Temporal workflows - orchestration logic."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from signalroom.temporal.activities import (
        PipelineInput,
        PipelineResult,
        run_pipeline_activity,
        send_notification_activity,
    )
    from signalroom.temporal.config import RETRY_POLICY


@dataclass
class SyncSourceInput:
    """Input for syncing a single source."""

    source_name: str
    source_kwargs: dict[str, Any] | None = None
    resources: list[str] | None = None
    notify_on_failure: bool = True
    notify_on_success: bool = False


@workflow.defn
class SyncSourceWorkflow:
    """Workflow to sync data from a single source.

    Runs the dlt pipeline and optionally sends notifications.
    """

    @workflow.run
    async def run(self, input: SyncSourceInput) -> PipelineResult:
        """Execute the sync workflow.

        Args:
            input: Sync configuration.

        Returns:
            Pipeline result.
        """
        workflow.logger.info(f"Starting sync for source: {input.source_name}")

        # Run the pipeline activity
        result = await workflow.execute_activity(
            run_pipeline_activity,
            PipelineInput(
                source_name=input.source_name,
                source_kwargs=input.source_kwargs,
                resources=input.resources,
            ),
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RETRY_POLICY,
        )

        # Send notifications based on result
        if not result.success and input.notify_on_failure:
            await workflow.execute_activity(
                send_notification_activity,
                args=[
                    "slack",
                    f"Pipeline failed: {input.source_name}\nError: {result.error_message}",
                    None,
                ],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY_POLICY,
            )

        if result.success and input.notify_on_success:
            total_rows = sum(result.row_counts.values())
            await workflow.execute_activity(
                send_notification_activity,
                args=[
                    "slack",
                    f"Pipeline completed: {input.source_name}\nLoaded {total_rows} rows",
                    None,
                ],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY_POLICY,
            )

        return result


@dataclass
class ScheduledSyncInput:
    """Input for scheduled sync of multiple sources."""

    sources: list[str]
    notify_on_failure: bool = True


@workflow.defn
class ScheduledSyncWorkflow:
    """Workflow to sync multiple sources on a schedule.

    Can be triggered by Temporal's cron scheduling.
    """

    @workflow.run
    async def run(self, input: ScheduledSyncInput) -> dict[str, PipelineResult]:
        """Execute syncs for all configured sources.

        Sources are run sequentially to avoid overwhelming the destination.
        For parallel execution, launch separate SyncSourceWorkflow instances.

        Args:
            input: List of sources to sync.

        Returns:
            Dict mapping source names to results.
        """
        results: dict[str, PipelineResult] = {}

        for source_name in input.sources:
            workflow.logger.info(f"Syncing source: {source_name}")

            result = await workflow.execute_activity(
                run_pipeline_activity,
                PipelineInput(source_name=source_name),
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RETRY_POLICY,
            )

            results[source_name] = result

            if not result.success:
                workflow.logger.error(f"Source {source_name} failed: {result.error_message}")

        # Summary notification
        failed = [name for name, r in results.items() if not r.success]
        if failed and input.notify_on_failure:
            await workflow.execute_activity(
                send_notification_activity,
                args=["slack", f"Scheduled sync completed with failures: {failed}", None],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY_POLICY,
            )

        return results
