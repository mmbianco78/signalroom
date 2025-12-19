# Data Sources

## Status Matrix

| Source | Status | Incremental | State Tracking | Client Tagging | Tests |
|--------|--------|-------------|----------------|----------------|-------|
| s3_exports | Partial | No | No | No | No |
| everflow | Stubbed | - | - | - | No |
| redtrack | Stubbed | - | - | - | No |
| posthog | Implemented | Yes | No | No | No |
| mautic | Implemented | No | No | No | No |
| google_sheets | Stubbed | - | - | - | No |

### Status Definitions

- **Implemented**: Core functionality works, may have gaps
- **Partial**: Some functionality, known TODOs
- **Stubbed**: Skeleton only, returns no data

---

## s3_exports

**Path**: `src/signalroom/sources/s3_exports/__init__.py`

**Purpose**: Ingest CSV files pushed to S3 by external systems (e.g., Sticky.io exports).

**Resources**:
| Resource | Write Mode | Primary Key | Description |
|----------|------------|-------------|-------------|
| daily_exports | append | _file_name, _row_id | All CSV rows with file metadata |

**Current Implementation**:
- Reads all `*.csv` files matching `bucket/prefix/**/*.csv`
- Adds metadata columns: `_file_name`, `_row_id`, `_file_date`
- Uses s3fs with AWS credentials from settings

**Known Gaps**:
- [ ] No file tracking state (reprocesses all files every run)
- [ ] No client_id tagging
- [ ] Single resource - doesn't split by data type (orders vs prospects)
- [ ] No schema validation

**Configuration**:
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=sticky-713-data-repo
S3_PREFIX=orders-create
```

---

## everflow

**Path**: `src/signalroom/sources/everflow/__init__.py`

**Purpose**: Pull conversion and click data from Everflow affiliate tracking.

**Status**: Stubbed - API structure defined but not implemented.

**Expected Resources**:
| Resource | Write Mode | Primary Key | Description |
|----------|------------|-------------|-------------|
| conversions | append | conversion_id | Affiliate conversions |
| clicks | append | click_id | Click events |

**Configuration**:
```
EVERFLOW_API_KEY=
```

**API Reference**: https://developers.everflow.io/

---

## redtrack

**Path**: `src/signalroom/sources/redtrack/__init__.py`

**Purpose**: Pull campaign and conversion data from Redtrack.

**Status**: Stubbed - skeleton only.

**Configuration**:
```
REDTRACK_API_KEY=
```

---

## posthog

**Path**: `src/signalroom/sources/posthog/__init__.py`

**Purpose**: Pull product analytics data from PostHog.

**Resources**:
| Resource | Write Mode | Primary Key | Incremental | Description |
|----------|------------|-------------|-------------|-------------|
| events | append | uuid | Yes (timestamp) | User events |
| feature_flags | replace | id | No | Feature flag definitions |
| experiments | replace | id | No | A/B test definitions |

**Current Implementation**:
- Paginated API calls with proper cursor handling
- Incremental loading for events (by timestamp)
- Full replace for flags/experiments

**Known Gaps**:
- [ ] No dlt state persistence (incremental resets on restart)
- [ ] No client_id tagging
- [ ] No error handling for rate limits

**Configuration**:
```
POSTHOG_API_KEY=
POSTHOG_PROJECT_ID=
POSTHOG_HOST=https://app.posthog.com
```

---

## mautic

**Path**: `src/signalroom/sources/mautic/__init__.py`

**Purpose**: Pull contacts, campaigns, and email data from self-hosted Mautic.

**Resources**:
| Resource | Write Mode | Primary Key | Description |
|----------|------------|-------------|-------------|
| contacts | merge | id | Contact records |
| emails | merge | id | Email templates |
| campaigns | merge | id | Campaign definitions |
| email_stats | append | - | Email performance (stubbed) |

**Current Implementation**:
- OAuth2 client credentials flow
- Paginated API calls
- Merge mode for mutable entities

**Known Gaps**:
- [ ] Token fetched on every pagination call (wasteful)
- [ ] No token caching/refresh logic
- [ ] email_stats resource not implemented
- [ ] No client_id tagging

**Configuration**:
```
MAUTIC_BASE_URL=https://mautic.yourdomain.com
MAUTIC_CLIENT_ID=
MAUTIC_CLIENT_SECRET=
```

---

## google_sheets

**Path**: `src/signalroom/sources/google_sheets/__init__.py`

**Purpose**: Pull data from Google Sheets (manual data entry, mappings, etc.).

**Status**: Stubbed - TODO placeholder only.

**Configuration**:
```
GOOGLE_SHEETS_CREDENTIALS_PATH=
# Or inline JSON:
GOOGLE_SHEETS_CREDENTIALS_JSON=
```

---

## Adding a New Source

### 1. Create source module

```bash
mkdir -p src/signalroom/sources/my_source
touch src/signalroom/sources/my_source/__init__.py
```

### 2. Implement dlt source

```python
# src/signalroom/sources/my_source/__init__.py
import dlt
from signalroom.common import settings, get_logger

log = get_logger(__name__)

@dlt.source(name="my_source")
def my_source():
    """My data source."""

    @dlt.resource(
        write_disposition="append",  # or "merge", "replace"
        primary_key="id",
    )
    def my_resource():
        """Fetch data from API."""
        # Implement pagination, API calls, etc.
        yield from fetch_data()

    return [my_resource]
```

### 3. Register in runner

```python
# src/signalroom/pipelines/runner.py
SOURCES = {
    ...
    "my_source": "signalroom.sources.my_source:my_source",
}
```

### 4. Add configuration

```python
# src/signalroom/common/config.py
class Settings(BaseSettings):
    ...
    my_source_api_key: SecretStr = SecretStr("")
```

```bash
# .env
MY_SOURCE_API_KEY=xxx
```

### 5. Test locally

```bash
python scripts/run_pipeline.py my_source --dry-run
python scripts/run_pipeline.py my_source
```

---

## Write Dispositions

| Mode | Use Case | Behavior |
|------|----------|----------|
| `append` | Immutable events (clicks, conversions) | Always insert new rows |
| `merge` | Mutable entities (contacts, campaigns) | Upsert by primary key |
| `replace` | Reference data (feature flags) | Drop and recreate table |

## Incremental Loading

dlt supports incremental loading via `dlt.sources.incremental`:

```python
@dlt.resource(write_disposition="append", primary_key="id")
def events(
    last_timestamp: dlt.sources.incremental[str] = dlt.sources.incremental(
        "timestamp",
        initial_value="2024-01-01T00:00:00Z"
    )
):
    # Only fetch events after last loaded timestamp
    yield from api.get_events(since=last_timestamp.last_value)
```

**Note**: Incremental state is stored in dlt's state store. Currently we use Postgres destination which stores state in `_dlt_pipeline_state` table. State persists across runs but NOT across different pipeline instances.
