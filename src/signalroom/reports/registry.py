"""Report registry and definitions.

Reports are defined with:
- name: Unique identifier
- query: SQL query or path to .sql file
- templates: Dict of channel -> template path
- schedule: Optional cron expression
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from signalroom.common import get_logger

log = get_logger(__name__)

# Module-level registry
_REPORTS: dict[str, "Report"] = {}


@dataclass
class Report:
    """Report definition."""

    name: str
    description: str
    query: str  # SQL query string or path to .sql file
    templates: dict[str, str]  # channel -> template path (e.g., "slack": "daily_ccw.slack.j2")
    schedule: str | None = None  # Cron expression (e.g., "0 7 * * *")
    params: dict[str, Any] = field(default_factory=dict)  # Default parameters

    def get_query(self) -> str:
        """Get the SQL query, loading from file if needed."""
        if self.query.endswith(".sql"):
            # Load from queries/ directory
            query_path = Path(__file__).parent / "queries" / self.query
            if not query_path.exists():
                raise FileNotFoundError(f"Query file not found: {query_path}")
            return query_path.read_text()
        return self.query

    def get_template_path(self, channel: str) -> Path:
        """Get the template path for a channel."""
        if channel not in self.templates:
            raise ValueError(f"No template for channel '{channel}' in report '{self.name}'")
        return Path(__file__).parent / "templates" / self.templates[channel]


def register_report(report: Report) -> Report:
    """Register a report in the global registry."""
    if report.name in _REPORTS:
        log.warning("report_overwrite", name=report.name)
    _REPORTS[report.name] = report
    log.info("report_registered", name=report.name, channels=list(report.templates.keys()))
    return report


def get_report(name: str) -> Report:
    """Get a report by name."""
    if name not in _REPORTS:
        raise KeyError(f"Report not found: {name}")
    return _REPORTS[name]


def list_reports() -> list[str]:
    """List all registered report names."""
    return list(_REPORTS.keys())


def report(
    name: str,
    description: str = "",
    query: str = "",
    templates: dict[str, str] | None = None,
    schedule: str | None = None,
    **default_params: Any,
) -> Callable[[Callable], Report]:
    """Decorator to register a report with a data function.

    The decorated function should return a dict of data for template rendering.

    Example:
        @report(
            name="daily_ccw",
            description="Daily CCW performance summary",
            query="daily_ccw.sql",
            templates={"slack": "daily_ccw.slack.j2"},
            schedule="0 7 * * *",
            advertiser_id=1,
        )
        def daily_ccw_data(date: str, advertiser_id: int = 1) -> dict:
            # Fetch and transform data
            return {"conversions": 100, "revenue": 5000, ...}
    """

    def decorator(func: Callable) -> Report:
        report_obj = Report(
            name=name,
            description=description or func.__doc__ or "",
            query=query,
            templates=templates or {},
            schedule=schedule,
            params=default_params,
        )
        # Attach the data function to the report
        report_obj.data_func = func  # type: ignore
        return register_report(report_obj)

    return decorator
