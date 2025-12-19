# Data Sources

## Status Matrix

| Source | Status | Incremental | State Tracking | Client Tagging | Tests |
|--------|--------|-------------|----------------|----------------|-------|
| s3_exports | ✅ Implemented | No | Via PK dedup | ✅ Yes | No |
| everflow | ✅ Implemented | No | Via PK merge | ✅ Yes | No |
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
| orders_create | append | _file_name, _row_id | New order records |
| orders_update | append | _file_name, _row_id | Order status updates |
| prospects_create | append | _file_name, _row_id | New prospect records (empty) |

**Current Implementation**:
- Creates one table per S3 prefix (orders-create → orders_create)
- Adds metadata columns: `_file_name`, `_row_id`, `_file_date`, `_client_id`
- Uses s3fs with AWS credentials from settings
- Supports `max_files` param for limiting files (takes most recent)
- Primary key deduplication prevents reloading same file

**Schema Details (orders_create)**:

Key columns (129 total):
| Column | Example Values | Notes |
|--------|---------------|-------|
| orders_id | "3770978" | Unique order ID |
| order_status | NEW, DECLINED, VOID/REFUNDED | No "approved" status |
| total_amount | "95", "19", "35", "105" | Stored as text |
| order_date | "2025-12-17" | Order creation date |
| billing_email | customer email | Customer contact |
| billing_state | "TX", "FL", "CA" | Geographic data |
| product_category | "CCW" | Project identifier |
| campaign_id | Campaign for attribution | Marketing source |
| afid, sid, c1-c3 | Affiliate tracking params | Attribution |
| chargeback_flag | "1" or empty | Risk indicator |
| refund_flag | "1" or empty | Risk indicator |

**Loaded Data (December 2025)**:
| Table | Rows | Days |
|-------|------|------|
| orders_create | 304,951 | 18 |
| orders_update | 346,044 | 18 |

**Configuration**:
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=sticky-713-data-repo
S3_PREFIXES=orders-create,orders-update,prospects-create
```

**Example Queries**:
```sql
-- Geographic breakdown of orders > $85
SELECT
  billing_state as state,
  COUNT(DISTINCT orders_id) as orders,
  ROUND(SUM(total_amount::numeric), 2) as revenue
FROM s3_exports.orders_create
WHERE order_status = 'NEW'
  AND total_amount::numeric > 85
GROUP BY billing_state
ORDER BY revenue DESC;

-- Daily revenue trend
SELECT
  _file_date as date,
  COUNT(DISTINCT orders_id) as orders,
  ROUND(SUM(total_amount::numeric), 2) as revenue
FROM s3_exports.orders_create
GROUP BY _file_date
ORDER BY _file_date;
```

---

## everflow

**Path**: `src/signalroom/sources/everflow/__init__.py`

**Purpose**: Pull affiliate conversion and revenue data from Everflow Network API.

**Resources**:
| Resource | Write Mode | Primary Key | Description |
|----------|------------|-------------|-------------|
| daily_stats | merge | date, affiliate_id, advertiser_id | Daily affiliate performance |

**Current Implementation**:
- Uses Entity Table API endpoint (`/v1/networks/reporting/entity/table`)
- Groups data by date, affiliate, and advertiser
- Adds metadata: `_client_id`, `_loaded_at`
- Merge mode allows re-running for same date range (updates existing)
- Client-side advertiser filtering (API filter unreliable)

**Schema Details (daily_stats)**:
| Column | Type | Description |
|--------|------|-------------|
| date | text | Report date (YYYY-MM-DD) |
| affiliate_id | int | Everflow affiliate ID |
| affiliate_label | text | Affiliate name |
| advertiser_id | int | Advertiser/brand ID |
| advertiser_label | text | Advertiser name (CCW, EXP) |
| clicks | int | Total click count |
| conversions | int | Conversion count |
| revenue | float | Gross revenue |
| payout | float | Affiliate payout |
| profit | float | Net profit (revenue - payout) |
| _client_id | text | Client identifier |
| _loaded_at | text | Load timestamp |

**Advertiser IDs**:
| ID | Label | Description |
|----|-------|-------------|
| 1 | CCW | Concealed Carry |
| 2 | EXP | Expungement |

**Loaded Data (December 2025)**:
| Advertiser | Rows | Conversions | Payout |
|------------|------|-------------|--------|
| CCW | 378 | 4,592 | $124,340 |
| EXP | 14 | 1 | $0 |
| Others | 52 | 2 | $293 |

**Configuration**:
```
EVERFLOW_API_KEY=
EVERFLOW_BASE_URL=https://api.eflow.team
```

**Usage**:
```bash
# Run for date range (all advertisers)
python -c "from signalroom.pipelines.runner import run_pipeline; print(run_pipeline('everflow', source_kwargs={'start_date': '2025-12-01', 'end_date': '2025-12-18'}))"

# Run for CCW only
python -c "from signalroom.pipelines.runner import run_pipeline; print(run_pipeline('everflow', source_kwargs={'start_date': '2025-12-17', 'end_date': '2025-12-18', 'advertiser_id': 1}))"
```

**Example Queries**:
```sql
-- Daily conversions by advertiser
SELECT
    date,
    advertiser_label,
    SUM(conversions) as conversions,
    ROUND(SUM(payout)::numeric, 2) as payout
FROM everflow.daily_stats
GROUP BY date, advertiser_label
ORDER BY date DESC, conversions DESC;

-- Top affiliates by conversion
SELECT
    affiliate_label,
    SUM(conversions) as total_conversions,
    ROUND(SUM(payout)::numeric, 2) as total_payout
FROM everflow.daily_stats
WHERE advertiser_label = 'CCW'
GROUP BY affiliate_label
ORDER BY total_conversions DESC
LIMIT 10;
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
