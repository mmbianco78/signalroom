"""Google Sheets source.

Thin wrapper around dlt's verified Google Sheets source.
See: https://dlthub.com/docs/dlt-ecosystem/verified-sources/google_sheets
"""

from collections.abc import Iterator
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


@dlt.source(name="google_sheets")
def google_sheets(
    spreadsheet_id: str,
    sheet_names: list[str] | None = None,
    credentials_path: str | None = None,
) -> list[DltResource]:
    """Source for Google Sheets data.

    Args:
        spreadsheet_id: Google Sheets document ID (from URL).
        sheet_names: List of sheet names to load. If None, loads all sheets.
        credentials_path: Path to service account JSON. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    credentials_path = credentials_path or settings.google_sheets_credentials_path

    # TODO: Use dlt's verified Google Sheets source when available
    # For now, implement a basic version using gspread or google-api-python-client

    @dlt.resource(
        name="sheets_data",
        write_disposition="replace",  # Full refresh each sync
    )
    def sheets_data() -> Iterator[dict[str, Any]]:
        """Load data from Google Sheets."""
        log.info(
            "fetching_google_sheets",
            spreadsheet_id=spreadsheet_id,
            sheet_names=sheet_names,
        )

        # TODO: Implement actual Google Sheets API calls
        # Option 1: Use dlt's verified source (recommended)
        # Option 2: Use gspread library
        # Option 3: Use google-api-python-client directly

        # Placeholder
        yield from []

    return [sheets_data]


def load_sheet_range(
    spreadsheet_id: str,
    range_name: str,
    credentials_path: str | None = None,
) -> list[dict[str, Any]]:
    """Load a specific range from a Google Sheet.

    Utility function for one-off loads outside of dlt pipelines.

    Args:
        spreadsheet_id: Google Sheets document ID.
        range_name: A1 notation range (e.g., "Sheet1!A1:D100").
        credentials_path: Path to service account JSON.

    Returns:
        List of row dicts with headers as keys.
    """
    # TODO: Implement
    raise NotImplementedError("Google Sheets integration not yet implemented")
