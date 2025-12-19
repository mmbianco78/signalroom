"""Temporal activities - units of retryable work."""

from dataclasses import dataclass
from typing import Any

from temporalio import activity

from signalroom.common import get_logger
from signalroom.pipelines import run_pipeline

log = get_logger(__name__)


@dataclass
class PipelineInput:
    """Input for running a dlt pipeline."""

    source_name: str
    source_kwargs: dict[str, Any] | None = None
    resources: list[str] | None = None


@dataclass
class PipelineResult:
    """Result from a dlt pipeline run."""

    pipeline_name: str
    load_id: str
    row_counts: dict[str, int]
    success: bool
    error_message: str | None = None


@activity.defn
async def run_pipeline_activity(input: PipelineInput) -> PipelineResult:
    """Run a dlt pipeline as a Temporal activity.

    This is the main activity that wraps dlt pipeline execution.
    Temporal handles retries, timeouts, and visibility.

    Args:
        input: Pipeline configuration.

    Returns:
        Pipeline result with row counts and status.
    """
    log.info(
        "activity_starting",
        source=input.source_name,
        resources=input.resources,
        activity_id=activity.info().activity_id,
    )

    try:
        # Run the dlt pipeline (synchronous)
        result = run_pipeline(
            source_name=input.source_name,
            source_kwargs=input.source_kwargs,
            resources=input.resources,
        )

        return PipelineResult(
            pipeline_name=result["pipeline_name"],
            load_id=result["load_id"],
            row_counts=result["row_counts"],
            success=True,
        )

    except Exception as e:
        log.error(
            "activity_failed",
            source=input.source_name,
            error=str(e),
            activity_id=activity.info().activity_id,
        )
        return PipelineResult(
            pipeline_name=input.source_name,
            load_id="",
            row_counts={},
            success=False,
            error_message=str(e),
        )


@activity.defn
async def send_notification_activity(
    channel: str,  # "slack", "email", "sms"
    message: str,
    recipient: str | None = None,
) -> bool:
    """Send a notification via the specified channel.

    Args:
        channel: Notification channel (slack, email, sms).
        message: Message content.
        recipient: Recipient (email address, phone number). Not needed for Slack.

    Returns:
        True if sent successfully.
    """
    from signalroom.notifications import send_email, send_slack, send_sms

    log.info("sending_notification", channel=channel, recipient=recipient)

    try:
        if channel == "slack":
            await send_slack(message)
        elif channel == "email":
            if not recipient:
                raise ValueError("Email recipient required")
            await send_email(recipient, "SignalRoom Alert", message)
        elif channel == "sms":
            if not recipient:
                raise ValueError("SMS recipient required")
            await send_sms(recipient, message)
        else:
            raise ValueError(f"Unknown notification channel: {channel}")

        return True

    except Exception as e:
        log.error("notification_failed", channel=channel, error=str(e))
        raise
