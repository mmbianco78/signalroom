# External Integrations

Documentation for Everflow and Redtrack integrations, based on the existing `automated-reporting` CLI tool.

> **API Reference**: For live documentation URLs, authentication details, and request/response examples, see [`docs/API_REFERENCE.md`](./API_REFERENCE.md).

---

## Everflow (Affiliate Tracking)

**Purpose**: Pull conversion and revenue data from Everflow affiliate network.

### Authentication

| Variable | Value | Notes |
|----------|-------|-------|
| `EVERFLOW_API_KEY` | `IKC8TYdpSvG9yJBxGGB7Dg` | Required |
| `EVERFLOW_BASE_URL` | `https://api.eflow.team` | Default |
| `EVERFLOW_AGG_PATH` | `/reporting/network/aggregated-data` | May vary by account |

**Auth Header**: `X-Eflow-API-Key: {api_key}`

### API Endpoints

**1. Aggregated Report** (primary)
```
POST https://api.eflow.team/reporting/network/aggregated-data
Headers:
  X-Eflow-API-Key: {api_key}
  Content-Type: application/json

Payload:
{
  "date_from": "2025-01-01",
  "date_to": "2025-01-07",
  "timezone": "UTC",
  "grouping": ["date"],
  "columns": ["clicks", "conversions", "revenue", "payout", "profit"],
  "filters": [],
  "limit": 10000,
  "page": 1
}
```

**2. Entity Table** (affiliate-level detail)
```
POST https://api.eflow.team/v1/networks/reporting/entity/table
Headers:
  X-Eflow-API-Key: {api_key}
  Content-Type: application/json

Payload:
{
  "from": "2025-01-01",
  "to": "2025-01-07",
  "timezone_id": 80,  // 80 = America/New_York
  "currency_id": "USD",
  "columns": [{"column": "affiliate"}, {"column": "date"}],
  "query": {
    "filters": [{"advertiser_id": 1}],
    "page": 1,
    "limit": 10000
  }
}
```

### Data Fields

| Field | Type | Description |
|-------|------|-------------|
| clicks | int | Click count |
| conversions | int | Conversion count |
| revenue | float | Gross revenue |
| payout | float | Affiliate payout |
| profit | float | Net profit (revenue - payout) |
| date | string | Date (YYYY-MM-DD) |
| affiliate_id | int | Affiliate ID |
| affiliate_label | string | Affiliate name |
| advertiser_id | int | Advertiser/brand ID |

### Advertiser IDs (Brands)

| ID | Label | Description |
|----|-------|-------------|
| 1 | CCW | Concealed Carry |
| 2 | EXP | Expungement |

---

## Redtrack (Ad Spend Tracking)

**Purpose**: Pull ad spend/cost data from Redtrack to merge with Everflow conversions.

### Authentication

| Variable | Value | Notes |
|----------|-------|-------|
| `REDTRACK_API_KEY` | `jdPOWa01R8An7MRXvAgV` | Required |
| `REDTRACK_BASE_URL` | `https://api.redtrack.io` | Default |
| `REDTRACK_REPORT_PATH` | `/report` | Default |

**Auth Header**: `X-API-KEY: {api_key}` (or `api_key` as query param for GET)

### API Endpoints

**1. Report (POST)**
```
POST https://api.redtrack.io/report
Headers:
  X-API-KEY: {api_key}
  Content-Type: application/json

Payload:
{
  "date_from": "2025-01-01",
  "date_to": "2025-01-07",
  "timezone": "UTC",
  "group_by": ["date", "traffic_source"],
  "columns": ["clicks", "conversions", "cost"],
  "filters": {},
  "limit": 10000,
  "page": 1
}
```

**2. Report (GET)** - Alternative
```
GET https://api.redtrack.io/report?api_key={api_key}&date_from=2025-01-01&date_to=2025-01-07&group=source
```

### Data Fields

| Field | Type | Description |
|-------|------|-------------|
| clicks | int | Click count |
| conversions | int | Conversion count |
| cost | float | Ad spend |
| date | string | Date (YYYY-MM-DD) |
| traffic_source | string | Traffic source name |
| source_id | string | Source ID (for mapping) |

---

## Affiliate Mapping (Redtrack → Everflow)

Internal affiliates run ads on Meta/Google tracked in Redtrack. This mapping links Redtrack sources to Everflow affiliates for merged reporting.

### Mapping Table

| Redtrack Source | Platform | Everflow Affiliate | Advertiser |
|-----------------|----------|-------------------|------------|
| Facebook CCW | Meta | G2 - Meta | CCW |
| Meta CCW AWF2 Stephanie | Meta | SB - Meta | CCW |
| Meta CCW SB Political | Meta | SB - Meta | CCW |
| Facebook EXP | Meta | G2 - Meta | EXP |
| Google Ads CCW (No-redirect) | Google | G2 - Google | CCW |
| Google Ads AWF2 SB | Google | SB - Google | CCW |
| Facebook CCW BHS | Meta | BHS | CCW |

### Source IDs (Redtrack)

| Source | Source ID |
|--------|-----------|
| Facebook CCW | 66c79f91be26fd4634569658 |
| Meta CCW AWF2 Stephanie | 6807d9120ee9ffc623c1d7e5 |
| Meta CCW SB Political | 68b87e99882b48e6620a3116 |
| Facebook EXP | 67c097f0aee15ff71f3f99aa |
| Google Ads CCW | 62b29551c6880d00014d8c73 |

---

## Daily Merge Report

The existing `automated-reporting` CLI merges Everflow + Redtrack data daily:

### Report Fields

| Field | Source | Description |
|-------|--------|-------------|
| date | Both | Report date |
| conversions | Everflow | Total conversions |
| revenue | Everflow | Gross revenue |
| payout | Everflow | Affiliate payouts |
| profit | Everflow | Net profit |
| cost | Redtrack | Ad spend (internal affiliates only) |
| cpa | Calculated | cost / conversions |

### CLI Commands (from automated-reporting)

```bash
# CCW daily merge
python -m reporting_cli merge daily-ccw \
  --date 2025-12-18 \
  --tz America/New_York \
  --advertiser-id 1 \
  --out-csv outputs/merged_2025-12-18_ccw.csv \
  --print-affiliates \
  --top-affiliates 12

# EXP daily merge
python -m reporting_cli merge daily-ccw \
  --date 2025-12-18 \
  --tz America/New_York \
  --advertiser-id 2 \
  --out-csv outputs/merged_2025-12-18_exp.csv
```

---

## Implementation Status in SignalRoom

| Source | Status | Notes |
|--------|--------|-------|
| everflow | Stubbed | API structure defined, needs implementation |
| redtrack | Stubbed | API structure defined, needs implementation |

### Next Steps

1. Implement Everflow source using aggregated report endpoint
2. Implement Redtrack source using report endpoint
3. Create merge workflow to join data by date + affiliate
4. Port internal-affiliates.csv mapping to database table
5. Set up scheduled sync via Temporal

---

## Reference: automated-reporting Location

Original implementation: `/Users/marcobianco/code/automated-reporting`

Key files:
- `reporting_cli/everflow.py` - Everflow API client
- `reporting_cli/redtrack.py` - Redtrack API client
- `internal-affiliates.csv` - Affiliate mapping table
- `scripts/run_daily_merge.sh` - Daily merge wrapper
