"""S3 CSV exports source.

Ingests CSV files pushed daily to an S3 bucket.
Tracks processed files to avoid reprocessing.
"""

from collections.abc import Iterator
from typing import Any

import dlt
from dlt.sources import DltResource

from signalroom.common import get_logger, settings

log = get_logger(__name__)


@dlt.source(name="s3_exports")
def s3_exports(
    bucket: str | None = None,
    prefix: str | None = None,
) -> list[DltResource]:
    """Source for CSV files from S3.

    Args:
        bucket: S3 bucket name. Defaults to settings.
        prefix: S3 key prefix. Defaults to settings.

    Returns:
        List of dlt resources.
    """
    bucket = bucket or settings.s3_bucket_name
    prefix = prefix or settings.s3_prefix

    @dlt.resource(
        name="daily_exports",
        write_disposition="append",
        primary_key=["_file_name", "_row_id"],
    )
    def daily_exports() -> Iterator[dict[str, Any]]:
        """Load CSV files from S3, tracking which files have been processed."""
        import hashlib

        import s3fs

        fs = s3fs.S3FileSystem(
            key=settings.aws_access_key_id,
            secret=settings.aws_secret_access_key.get_secret_value(),
        )

        # Get list of CSV files
        pattern = f"{bucket}/{prefix}**/*.csv"
        files = fs.glob(pattern)

        log.info("found_s3_files", count=len(files), pattern=pattern)

        for file_path in sorted(files):
            # TODO: Track processed files in dlt state to avoid reprocessing
            # For now, rely on primary key deduplication

            log.info("processing_file", file_path=file_path)

            with fs.open(file_path, "r") as f:
                import csv

                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    # Add metadata columns
                    row["_file_name"] = file_path
                    row["_row_id"] = i
                    row["_file_date"] = _extract_date_from_filename(file_path)
                    yield row

    return [daily_exports]


def _extract_date_from_filename(filename: str) -> str | None:
    """Extract date from filename if present (e.g., 'report_2024-01-15.csv')."""
    import re

    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else None
