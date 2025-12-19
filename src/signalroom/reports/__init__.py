"""Report generation module.

Provides templated reports for Slack, Email, and SMS channels using Jinja2.
"""

from signalroom.reports.registry import Report, get_report, list_reports, register_report
from signalroom.reports.renderer import render_report
from signalroom.reports.runner import render_alert, run_report

# Import definitions to register reports
from signalroom.reports import definitions as _definitions  # noqa: F401

__all__ = [
    "Report",
    "get_report",
    "list_reports",
    "register_report",
    "render_alert",
    "render_report",
    "run_report",
]
