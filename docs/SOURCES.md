# Data Sources

> **API Reference**: For live documentation URLs and request/response examples, see [`docs/API_REFERENCE.md`](./API_REFERENCE.md).

## Status Matrix

| Source | Status | Incremental | State Tracking | Client Tagging | Tests |
|--------|--------|-------------|----------------|----------------|-------|
| s3_exports | ✅ Production | File-level | `resource_state()` | ✅ Yes | No |
| everflow | ✅ Production | Row-level | `dlt.sources.incremental` | ✅ Yes | No |
| redtrack | ✅ Production | Row-level | `dlt.sources.incremental` | ✅ Yes | No |
| posthog | Code complete | Row-level | `dlt.sources.incremental` | No | No |
| mautic | Code complete | No | No | No | No |
| google_sheets | Stubbed | - | - | - | No |

### Status Definitions

- **Production**: Actively running in production (Fly.io worker, Temporal schedules)
- **Code complete**: Implementation exists but not deployed to production
- **Stubbed**: Skeleton only, returns no data

---

## s3_exports

**Path**: `src/signalroom/sources/s3_exports/__init__.py`

**Purpose**: Ingest CSV files pushed to S3 by external systems (e.g., Sticky.io exports).

**Resources**:
| Resource | Write Mode | Primary Key | Description |
|----------|------------|-------------|-------------|
| orders_create | merge | _file_name, _row_id | New order records |
| orders_update | merge | _file_name, _row_id | Order status updates |
| prospects_create | merge | _file_name, _row_id | New prospect records (empty) |

**Current Implementation**:
- Creates one table per S3 prefix (orders-create → orders_create)
- Adds metadata columns: `_file_name`, `_row_id`, `_file_date`, `_client_id`
- Uses s3fs with AWS credentials from settings
- Supports `max_files` param for limiting files (takes most recent)
- **File-level state tracking** via `dlt.current.resource_state()` (not row-level incremental)
- Merge disposition with primary key prevents duplicates on re-run

**Why File-Level State (not `dlt.sources.incremental`)**:
- S3 files have 19,000+ rows sharing the same `_file_date` cursor value
- Row-level incremental causes O(n²) deduplication overhead
- File-level tracking: O(n) linear performance

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

**Purpose**: Pull ad spend data from Redtrack's reporting API for CPA calculations.

**Resources**:
| Resource | Write Mode | Primary Key | Description |
|----------|------------|-------------|-------------|
| daily_spend | merge | date, source_id | Daily spend by traffic source |

**Current Implementation**:
- Uses GET `/report` endpoint (POST returns 404)
- Groups by traffic source (`group=source`)
- One API call per day for date-level granularity
- Automatic retry with backoff on 429 rate limit
- Adds metadata: `_client_id`, `_loaded_at`
- Uses `conversions` field only (not `total_conversions` which includes all event types)

**Schema Details (daily_spend)**:
| Column | Type | Description |
|--------|------|-------------|
| date | text | Report date (YYYY-MM-DD) |
| source_id | text | Redtrack traffic source ID |
| source_name | text | Campaign/source name |
| source_alias | text | Platform alias (facebook, google) |
| clicks | int | Click count |
| conversions | int | Redtrack-tracked conversions |
| cost | float | Ad spend |
| _client_id | text | Client identifier |
| _loaded_at | text | Load timestamp |

**Loaded Data (December 2025)**:
| Period | Rows | Sources | Total Cost |
|--------|------|---------|------------|
| Dec 1-18 | 248 | 23 | $211,152.62 |

**Top Sources by Spend**:
| Source | Cost |
|--------|------|
| Facebook CCW | $140,845.10 |
| Meta CCW AWF2 Stephanie | $35,924.88 |
| Google Ads CCW | $22,304.42 |

**Rate Limiting**:
- 1 second delay between daily requests
- Exponential backoff on 429 (1s, 2s, 4s, max 3 retries)

**Configuration**:
```
REDTRACK_API_KEY=
REDTRACK_BASE_URL=https://api.redtrack.io
```

**Usage**:
```bash
# Run for date range
python -c "from signalroom.pipelines.runner import run_pipeline; print(run_pipeline('redtrack', source_kwargs={'start_date': '2025-12-01', 'end_date': '2025-12-18'}))"
```

**Example Queries**:
```sql
-- Daily spend by source
SELECT
    date,
    source_name,
    cost,
    clicks
FROM redtrack.daily_spend
ORDER BY date DESC, cost DESC;

-- Total spend by source
SELECT
    source_name,
    SUM(cost) as total_cost,
    SUM(clicks) as total_clicks
FROM redtrack.daily_spend
GROUP BY source_name
ORDER BY total_cost DESC;
```

**API Reference**: https://help.redtrack.io/hc/en-us/categories/360003146479-API

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

### Row-Level Incremental (for low-volume sources)

dlt supports incremental loading via `dlt.sources.incremental`:

```python
@dlt.resource(write_disposition="merge", primary_key="id")
def events(
    last_timestamp: dlt.sources.incremental[str] = dlt.sources.incremental(
        "timestamp",
        initial_value="2024-01-01T00:00:00Z"
    )
):
    # Only fetch events after last loaded timestamp
    yield from api.get_events(since=last_timestamp.last_value)
```

**Best for**: API sources with < 100 rows per cursor value (Everflow, Redtrack).

### File-Level State (for high-volume sources)

For sources with 1000+ rows sharing the same cursor value, use `dlt.current.resource_state()`:

```python
@dlt.resource(write_disposition="merge", primary_key=["file_name", "row_id"])
def csv_resource():
    state = dlt.current.resource_state()
    last_date = state.get("last_file_date", "2024-01-01")

    for file in get_files_since(last_date):
        yield from process_file(file)
        state["last_file_date"] = file.date
```

**Best for**: Bulk file imports (S3 CSV exports with 19k+ rows per file).

**Why**: `dlt.sources.incremental` tracks every row for deduplication. With many rows sharing the same cursor value, this causes O(n²) performance.

### State Storage

State is stored in `_dlt_pipeline_state` table in Postgres. State persists across runs but NOT across different pipeline instances.
