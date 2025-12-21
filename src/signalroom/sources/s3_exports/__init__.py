"""S3 CSV exports source.

Ingests CSV files pushed daily to an S3 bucket (e.g., from Sticky.io).
Creates separate tables per prefix (orders_create, orders_update, etc.).
Tags all data with _client_id for multi-client support.

Uses dlt incremental loading to track the last processed file date.
Only processes files with dates >= the last loaded date.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)

# Initial value for incremental loading - set to current max date in database
# This ensures we don't re-fetch historical data on first run with incremental
S3_INITIAL_DATE = "2025-12-18"


def _make_table_name(prefix: str) -> str:
    """Convert S3 prefix to valid table name (e.g., 'orders-create' -> 'orders_create')."""
    return prefix.replace("-", "_").replace("/", "_").strip("_")


def _extract_date_from_filename(filename: str) -> str | None:
    """Extract date from filename if present (e.g., 'report_2025-09-22T1849_xxx.csv')."""
    import re

    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else None


def _create_csv_resource(
    bucket: str,
    prefix: str,
    client_id: str,
    max_files: int | None = None,
) -> DltResource:
    """Create a dlt resource for a specific S3 prefix.

    Uses dlt incremental to track the last processed file date.
    Only processes files with dates >= the incremental start value.
    """
    table_name = _make_table_name(prefix)

    @dlt.resource(
        name=table_name,
        write_disposition="append",
        primary_key=["_file_name", "_row_id"],
    )
    def csv_resource(
        date_cursor: dlt.sources.incremental[str] = dlt.sources.incremental(
            "_file_date",
            initial_value=S3_INITIAL_DATE,
        ),
    ) -> Iterator[dict[str, Any]]:
        """Load CSV files from S3 prefix.

        Uses dlt incremental to track last processed date.
        Filters files by date before processing for efficiency.

        Args:
            date_cursor: dlt incremental tracker for the _file_date field.
                Automatically tracks max(_file_date) from yielded rows.
        """
        import csv

        import s3fs

        fs = s3fs.S3FileSystem(
            key=settings.aws_access_key_id,
            secret=settings.aws_secret_access_key.get_secret_value(),
        )

        # Get incremental start value
        start_date = date_cursor.start_value

        log.info(
            "s3_incremental_fetch",
            prefix=prefix,
            start_date=start_date,
        )

        pattern = f"{bucket}/{prefix}/**/*.csv"
        all_files = fs.glob(pattern)

        if not all_files:
            # Try without recursive glob
            pattern = f"{bucket}/{prefix}/*.csv"
            all_files = fs.glob(pattern)

        log.info("found_s3_files", prefix=prefix, count=len(all_files), pattern=pattern)

        # Filter files by date BEFORE processing (efficiency)
        files_to_process: list[tuple[str, str | None]] = []
        for file_path in sorted(all_files):
            # fs.glob returns list[str], but pyright doesn't know that
            path_str = str(file_path)
            file_date = _extract_date_from_filename(path_str)
            # Include files with date >= start_date (or unknown dates)
            if file_date is None or file_date >= start_date:
                files_to_process.append((path_str, file_date))

        log.info(
            "filtered_s3_files",
            prefix=prefix,
            total_files=len(all_files),
            files_after_filter=len(files_to_process),
            start_date=start_date,
        )

        # Skip if no new files
        if not files_to_process:
            log.info(
                "s3_already_current",
                prefix=prefix,
                start_date=start_date,
                message="No new files to process",
            )
            return

        # Limit files if max_files is set (take most recent)
        if max_files and len(files_to_process) > max_files:
            files_to_process = files_to_process[-max_files:]  # Take last N (most recent)
            log.info("limiting_files", max_files=max_files, processing=len(files_to_process))

        total_rows = 0
        for file_path, file_date in files_to_process:
            log.info("processing_file", file_path=file_path, file_date=file_date)

            try:
                with fs.open(file_path, "r") as f:
                    # s3fs file handles work with csv.DictReader
                    reader = csv.DictReader(f)  # type: ignore[arg-type]
                    for i, row in enumerate(reader):
                        # Add metadata columns
                        row["_file_name"] = file_path
                        row["_row_id"] = i
                        row["_file_date"] = file_date
                        row["_client_id"] = client_id
                        row["_loaded_at"] = datetime.now(UTC).isoformat()
                        total_rows += 1
                        yield row
            except Exception as e:
                log.error("file_processing_error", file_path=file_path, error=str(e))
                raise

        log.info(
            "s3_fetch_complete",
            prefix=prefix,
            files_processed=len(files_to_process),
            rows_yielded=total_rows,
            start_date=start_date,
        )

    # Set the function name for dlt
    csv_resource.__name__ = table_name
    csv_resource.__qualname__ = table_name

    return csv_resource


@dlt.source(name="s3_exports")
def s3_exports(
    bucket: str | None = None,
    prefixes: list[str] | None = None,
    client_id: str = "713",
    max_files: int | None = None,
) -> list[DltResource]:
    """Source for CSV files from S3.

    Creates one table per prefix (e.g., orders_create, orders_update).
    Uses dlt incremental loading to track the last processed file date.
    Only processes files with dates >= the last loaded date.

    Args:
        bucket: S3 bucket name. Defaults to settings.
        prefixes: List of S3 prefixes. Defaults to settings.s3_prefix_list.
        client_id: Client identifier for tagging data.
        max_files: Limit files per prefix (takes most recent). None = all files.

    Returns:
        List of dlt resources (one per prefix).
    """
    bucket = bucket or settings.s3_bucket_name
    prefixes = prefixes or settings.s3_prefix_list

    if not bucket:
        raise ValueError("S3 bucket not configured. Set S3_BUCKET_NAME in .env")

    if not prefixes:
        raise ValueError("S3 prefixes not configured. Set S3_PREFIXES in .env")

    log.info("creating_s3_source", bucket=bucket, prefixes=prefixes, client_id=client_id)

    resources = []
    for prefix in prefixes:
        if prefix:  # Skip empty prefixes
            resource = _create_csv_resource(bucket, prefix, client_id, max_files)
            resources.append(resource)

    return resources
