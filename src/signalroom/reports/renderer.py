"""Report rendering using Jinja2 and MJML.

Supports multiple output channels:
- slack: Jinja2 -> Slack mrkdwn or Block Kit JSON
- email: Jinja2 + MJML -> responsive HTML
- sms: Jinja2 -> plain text
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import jinja2
import mjml

from signalroom.common import get_logger
from signalroom.reports.registry import Report, get_report

log = get_logger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"

# Jinja2 environment with custom filters
_env: jinja2.Environment | None = None


def _get_env() -> jinja2.Environment:
    """Get or create the Jinja2 environment."""
    global _env
    if _env is None:
        _env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
            autoescape=jinja2.select_autoescape(["html", "xml", "mjml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Add custom filters
        _env.filters["currency"] = _filter_currency
        _env.filters["number"] = _filter_number
        _env.filters["percent"] = _filter_percent
        _env.filters["date"] = _filter_date
        _env.filters["delta"] = _filter_delta
        _env.globals["now"] = datetime.now
    return _env


def _filter_currency(value: float | int | None, symbol: str = "$") -> str:
    """Format a number as currency."""
    if value is None:
        return f"{symbol}0.00"
    return f"{symbol}{value:,.2f}"


def _filter_number(value: float | int | None, decimals: int = 0) -> str:
    """Format a number with thousands separator."""
    if value is None:
        return "0"
    if decimals > 0:
        return f"{value:,.{decimals}f}"
    return f"{int(value):,}"


def _filter_percent(value: float | None, decimals: int = 1) -> str:
    """Format a number as percentage."""
    if value is None:
        return "0%"
    return f"{value:.{decimals}f}%"


def _filter_date(value: str | datetime | None, fmt: str = "%b %d, %Y") -> str:
    """Format a date string or datetime."""
    if value is None:
        return ""
    if isinstance(value, str):
        # Try to parse ISO format
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(fmt)


def _filter_delta(value: float | None, positive_prefix: str = "+") -> str:
    """Format a number as delta with +/- prefix."""
    if value is None:
        return "0"
    if value > 0:
        return f"{positive_prefix}{value:,.2f}"
    return f"{value:,.2f}"


def render_template(template_name: str, data: dict[str, Any]) -> str:
    """Render a Jinja2 template with data.

    Args:
        template_name: Template filename (e.g., "daily_ccw.slack.j2")
        data: Template context data

    Returns:
        Rendered template string
    """
    env = _get_env()
    template = env.get_template(template_name)
    return template.render(**data)


def render_mjml(template_name: str, data: dict[str, Any]) -> str:
    """Render an MJML template to HTML.

    Args:
        template_name: MJML template filename (e.g., "daily_ccw.email.mjml")
        data: Template context data

    Returns:
        Rendered HTML string
    """
    # First render Jinja2 variables in MJML
    mjml_content = render_template(template_name, data)

    # Then compile MJML to HTML
    result = mjml.mjml2html(mjml_content)
    return result


def render_report(
    report_name: str,
    channel: str,
    data: dict[str, Any],
) -> str:
    """Render a report for a specific channel.

    Args:
        report_name: Name of the registered report
        channel: Output channel ("slack", "email", "sms")
        data: Template context data

    Returns:
        Rendered content string (mrkdwn, HTML, or plain text)
    """
    report = get_report(report_name)
    template_path = report.get_template_path(channel)
    template_name = template_path.name

    log.info(
        "rendering_report",
        report=report_name,
        channel=channel,
        template=template_name,
    )

    # Choose renderer based on template extension
    if template_name.endswith(".mjml"):
        content = render_mjml(template_name, data)
    else:
        content = render_template(template_name, data)

    log.info(
        "report_rendered",
        report=report_name,
        channel=channel,
        length=len(content),
    )

    return content
