"""S3 CSV exports source.

Ingests CSV files pushed daily to an S3 bucket (e.g., from Sticky.io).
Creates separate tables per prefix (orders_create, orders_update, etc.).
Tags all data with _client_id for multi-client support.
"""

from collections.abc import Iterator
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


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
    """Create a dlt resource for a specific S3 prefix."""
    table_name = _make_table_name(prefix)

    @dlt.resource(
        name=table_name,
        write_disposition="append",
        primary_key=["_file_name", "_row_id"],
    )
    def csv_resource() -> Iterator[dict[str, Any]]:
        """Load CSV files from S3 prefix."""
        import csv
        import s3fs

        fs = s3fs.S3FileSystem(
            key=settings.aws_access_key_id,
            secret=settings.aws_secret_access_key.get_secret_value(),
        )

        pattern = f"{bucket}/{prefix}/**/*.csv"
        files = fs.glob(pattern)

        if not files:
            # Try without recursive glob
            pattern = f"{bucket}/{prefix}/*.csv"
            files = fs.glob(pattern)

        log.info("found_s3_files", prefix=prefix, count=len(files), pattern=pattern)

        # Limit files if max_files is set (take most recent)
        files_to_process = sorted(files)
        if max_files and len(files_to_process) > max_files:
            files_to_process = files_to_process[-max_files:]  # Take last N (most recent)
            log.info("limiting_files", max_files=max_files, processing=len(files_to_process))

        for file_path in files_to_process:
            log.info("processing_file", file_path=file_path)

            try:
                with fs.open(file_path, "r") as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        # Add metadata columns
                        row["_file_name"] = file_path
                        row["_row_id"] = i
                        row["_file_date"] = _extract_date_from_filename(file_path)
                        row["_client_id"] = client_id
                        yield row
            except Exception as e:
                log.error("file_processing_error", file_path=file_path, error=str(e))
                raise

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
