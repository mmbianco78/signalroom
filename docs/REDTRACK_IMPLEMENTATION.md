# Redtrack Implementation Summary

**Phase 2** | **Status: Ready for QA** | **Date: December 19, 2025**

---

## Overview

The Redtrack source ingests ad spend data from Redtrack's reporting API, grouped by traffic source (campaign) and date. This data enables CPA calculations when joined with Everflow conversion data.

---

## Data Filtering Breakdown

### API Behavior

| Layer | What Happens | Details |
|-------|--------------|---------|
| API Endpoint | GET `/report` | POST endpoint returns 404 |
| Grouping | `group=source` | Groups by traffic source |
| Date Range | One call per day | Ensures date-level granularity |
| Rate Limiting | 1 req/sec | Automatic retry with backoff on 429 |

### What's Included

| Field | Description | Example |
|-------|-------------|---------|
| `source_id` | Redtrack traffic source ID | `66c79f91be26fd4634569658` |
| `source_name` | Campaign/source name | `Facebook CCW` |
| `source_alias` | Platform alias | `facebook` |
| `cost` | Ad spend | `$26,269.20` |
| `clicks` | Total clicks | `26,135` |
| `conversions` | Redtrack-tracked conversions | `573` |

### Source-to-Affiliate Mapping

The `source_id` maps to Everflow affiliates via `internal-affiliates.csv`:

| Source Name | Source ID | Everflow Affiliate |
|-------------|-----------|-------------------|
| Facebook CCW | `66c79f91be26fd4634569658` | G2 - Meta |
| Meta CCW AWF2 Stephanie | `6807d9120ee9ffc623c1d7e5` | SB - Meta |
| Google Ads CCW | `62b29551c6880d00014d8c73` | G2 - Google |

---

## Date Range

### Current Load

| Period | Rows | Sources | Total Cost |
|--------|------|---------|------------|
| Dec 1-18, 2025 | 248 | 23 | $211,152.62 |

### Available Data

Redtrack API provides data going back at least 30+ days.

### Backfill Options

1. **Full backfill** - Match Everflow range
2. **Rolling window** - Last N days on each run
3. **Incremental** - Daily updates only

---

## Scheduling Plan

### Current System (automated-reporting)

- Hourly 7am-11pm ET (17 runs/day)
- Same-day spend data
- Merges with Everflow for CPA

### SignalRoom Schedule

| Time | Action | Notes |
|------|--------|-------|
| Hourly 7am-11pm ET | Sync current day | ~18 seconds per day |
| 7am | Previous day final | Final spend numbers |

### Rate Limit Handling

- 1 second delay between daily requests
- Exponential backoff on 429 (1s, 2s, 4s)
- Max 3 retries before failing

---

## Technical Details

### API Endpoint

```
GET https://api.redtrack.io/report
Headers:
  X-API-KEY: {api_key}
Params:
  api_key: {api_key}
  date_from: YYYY-MM-DD
  date_to: YYYY-MM-DD
  timezone: America/New_York
  group: source
  sortby: clicks
  direction: desc
```

### Response Structure

```json
[
  {
    "source": "Facebook CCW",
    "source_alias": "facebook",
    "source_id": "66c79f91be26fd4634569658",
    "cost": 26269.20,
    "clicks": 26135,
    "conversions": 573,
    ...
  }
]
```

### Supabase Schema

```sql
-- Schema: redtrack
-- Table: daily_spend
CREATE TABLE redtrack.daily_spend (
    date TEXT,
    source_id TEXT,
    source_name TEXT,
    source_alias TEXT,
    clicks BIGINT,
    conversions BIGINT,
    cost DOUBLE PRECISION,
    _client_id TEXT,
    _loaded_at TEXT,
    PRIMARY KEY (date, source_id)
);
```

### Write Disposition

- **merge** by `(date, source_id)` - safe for re-runs and intraday updates

---

## QA Checklist

Compare these values against Redtrack UI:

### Total Spend (Dec 1-18, 2025)

| Metric | SignalRoom | Redtrack UI |
|--------|------------|-------------|
| Total Cost | $211,152.62 | _______ |
| Total Clicks | 170,105 | _______ |
| Total Conversions | 2,933 | _______ |

### Single Day: Dec 18, 2025

| Metric | SignalRoom | Redtrack UI |
|--------|------------|-------------|
| Facebook CCW Cost | $26,269.20 | _______ |
| Total Sources | 16 | _______ |

### Top Sources by Spend (Dec 1-18)

| Source | SignalRoom | Redtrack UI |
|--------|------------|-------------|
| Facebook CCW | $140,845.10 | _______ |
| Meta CCW AWF2 Stephanie | $35,924.88 | _______ |
| Google Ads CCW | $22,304.42 | _______ |

---

## Merge Logic (Phase 3)

With both Everflow and Redtrack loaded, the merge query:

```sql
-- Join Redtrack spend with Everflow conversions
SELECT
    e.date,
    m.everflow_affiliate_label as affiliate,
    e.conversions as ef_conversions,
    e.payout as ef_payout,
    r.cost as rt_spend,
    r.clicks as rt_clicks,
    CASE
        WHEN m.everflow_affiliate_label IN ('G2 - Meta', 'G2 - Google', 'SB - Meta', 'SB - Google')
        THEN r.cost  -- Use Redtrack spend for internal affiliates
        ELSE e.payout  -- Use Everflow payout for external affiliates
    END as final_cost,
    e.conversions / NULLIF(CASE ... END, 0) as cpa
FROM everflow.daily_stats e
JOIN public.affiliate_mapping m ON e.affiliate_id = m.everflow_affiliate_id
LEFT JOIN redtrack.daily_spend r ON r.date = e.date AND r.source_id = m.redtrack_source_id
WHERE e._client_id = '713'
```

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | Claude Code | 2025-12-19 | Ready |
| QA | _______ | _______ | _______ |
| Approver | _______ | _______ | _______ |

---

## Next Steps

1. **QA**: Verify numbers against Redtrack UI
2. **Phase 3**: Load affiliate mapping table
3. **Phase 3**: Create merge view/query
4. **Phase 4**: Set up hourly Temporal schedules
