"""Report execution.

Fetches data from Supabase, renders templates, and sends notifications.
"""

from datetime import date, datetime, timedelta
from typing import Any

from signalroom.common import get_logger, settings
from signalroom.reports.registry import Report, get_report
from signalroom.reports.renderer import render_report

log = get_logger(__name__)


def execute_query(query: str, params: dict[str, Any]) -> dict[str, Any]:
    """Execute a SQL query against Supabase and return the result.

    Args:
        query: SQL query string with :param placeholders
        params: Parameter values

    Returns:
        Query result as dict (first row)
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    # Replace :param with %(param)s for psycopg2
    pg_query = query
    for key in params:
        pg_query = pg_query.replace(f":{key}", f"%({key})s")

    conn_string = settings.postgres_connection_string

    with psycopg2.connect(conn_string) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(pg_query, params)
            row = cur.fetchone()
            if row:
                return dict(row)
            return {}


def run_report(
    report_name: str,
    channel: str = "slack",
    params: dict[str, Any] | None = None,
    send: bool = False,
) -> str:
    """Execute a report and return rendered content.

    Args:
        report_name: Name of the registered report
        channel: Output channel ("slack", "email", "sms")
        params: Override default parameters
        send: If True, send the notification

    Returns:
        Rendered report content
    """
    report = get_report(report_name)

    # Merge default params with overrides
    merged_params = {**report.params, **(params or {})}

    # Default date to yesterday if not provided
    if "date" not in merged_params:
        yesterday = date.today() - timedelta(days=1)
        merged_params["date"] = yesterday.isoformat()

    log.info(
        "running_report",
        report=report_name,
        channel=channel,
        params=merged_params,
    )

    # Get and execute query
    query = report.get_query()
    data = execute_query(query, merged_params)

    if not data:
        log.warning("report_no_data", report=report_name, params=merged_params)
        data = {
            "report_date": merged_params.get("date"),
            "total_conversions": 0,
            "total_cost": 0,
            "overall_cpa": 0,
            "internal_conversions": 0,
            "internal_cost": 0,
            "internal_cpa": 0,
            "external_conversions": 0,
            "external_cost": 0,
            "external_cpa": 0,
            "top_affiliates": [],
        }

    # Parse JSON fields if needed
    if isinstance(data.get("top_affiliates"), str):
        import json
        data["top_affiliates"] = json.loads(data["top_affiliates"]) or []
    elif data.get("top_affiliates") is None:
        data["top_affiliates"] = []

    # Render template
    content = render_report(report_name, channel, data)

    log.info(
        "report_complete",
        report=report_name,
        channel=channel,
        content_length=len(content),
    )

    # Send if requested
    if send:
        import asyncio
        asyncio.run(_send_report(channel, content))

    return content


async def _send_report(channel: str, content: str, subject: str = "SignalRoom Report") -> None:
    """Send report content via the specified channel."""
    from signalroom.notifications.channels import send_email, send_slack, send_sms

    if channel == "slack":
        await send_slack(content)
    elif channel == "email":
        await send_email(
            to=settings.report_email_to or "reports@example.com",
            subject=subject,
            html=content,
        )
    elif channel == "sms":
        await send_sms(
            to=settings.report_sms_to or "+15551234567",
            message=content,
        )
    else:
        log.warning("unknown_channel", channel=channel)


def render_alert(
    title: str,
    message: str = "",
    level: str = "error",
    details: dict[str, Any] | None = None,
    source: str = "signalroom",
    channel: str = "slack",
) -> str:
    """Render an alert notification.

    Args:
        title: Alert title
        message: Alert message/description
        level: Severity level ("error", "warning", "info")
        details: Additional key-value details to include
        source: Source system/component
        channel: Output channel ("slack", "email", "sms")

    Returns:
        Rendered alert content
    """
    from datetime import datetime

    from signalroom.reports.renderer import render_report

    data = {
        "title": title,
        "message": message,
        "level": level,
        "details": details or {},
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return render_report("alert", channel, data)
