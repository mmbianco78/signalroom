"""Temporal workflows and activities for durable execution."""

from signalroom.temporal.activities import (
    ReportInput,
    ReportResult,
    run_pipeline_activity,
    run_report_activity,
    send_notification_activity,
)
from signalroom.temporal.config import RETRY_POLICY, get_temporal_client
from signalroom.temporal.workflows import (
    RunReportWorkflow,
    ScheduledSyncWorkflow,
    SyncSourceWorkflow,
)

__all__ = [
    # Workflows
    "SyncSourceWorkflow",
    "ScheduledSyncWorkflow",
    "RunReportWorkflow",
    # Activities
    "run_pipeline_activity",
    "run_report_activity",
    "send_notification_activity",
    # Config
    "get_temporal_client",
    "RETRY_POLICY",
    # Types
    "ReportInput",
    "ReportResult",
]
