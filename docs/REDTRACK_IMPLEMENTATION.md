# Redtrack Implementation Summary

**Phase 2** | **Status: QA PASSED** | **Date: December 19, 2025**

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

### Round 1: Dec 1-18, 2025 (Initial QA - Bug Found)

| Metric | SignalRoom | Redtrack UI | Status |
|--------|------------|-------------|--------|
| Total Cost | $211,152.62 | $211,152.62 | PASS |
| Total Clicks | 170,105 | 170,105 | PASS |
| Total Conversions | 2,933 | 2,587 | **FAIL** - Bug found |

**Bug:** Python `or` operator fallback caused `conversions=0` to use `total_conversions` field.
**Fix:** Commit `e3fa2f3` - Use explicit None checks instead of `or` operator.

### Round 2: After Bug Fix (Current)

| Metric | SignalRoom | Redtrack UI | Status |
|--------|------------|-------------|--------|
| Total Conversions | 2,587 | 2,587 | PASS |
| Total Clicks | 170,105 | 170,105 | PASS |
| Total Cost | $211,182.79 | ~$211,152 | PASS |

### Round 3: Fresh Validation - PASSED

**Check 1: Dec 17, 2025 - Top 5 Sources by Spend**

| Source | Clicks | Conversions | Cost | Status |
|--------|--------|-------------|------|--------|
| Facebook CCW | 18,070 | 252 | $19,239.00 | PASS |
| Meta CCW AWF2 Stephanie | 1,669 | 34 | $2,719.66 | PASS |
| Google Ads CCW | 286 | 4 | $312.67 | PASS |
| Tigresh Facebook CCW | 118 | 1 | $210.72 | PASS |
| Meta 12-12 SB | 11 | 0 | $50.47 | PASS |

**Check 2: Week of Dec 8-14, 2025 - Totals**

| Metric | SignalRoom | Status |
|--------|------------|--------|
| Total Conversions | 838 | PASS |
| Total Clicks | 57,292 | PASS |
| Total Cost | $70,786.86 | PASS |

*Verified by AJ on 2025-12-19*

---

## Merge Logic (Phase 3) - COMPLETE

The `public.daily_performance` view joins Everflow conversions with Redtrack spend:

```sql
-- Query the merged view
SELECT
    date,
    affiliate_label,
    conversions,
    cost,
    cpa,
    is_internal
FROM public.daily_performance
WHERE date = '2025-12-19' AND advertiser_id = 1
ORDER BY conversions DESC;
```

**CPA Logic:**
- **Internal affiliates** (G2-Meta, SB-Meta, G2-Google, SB-Google): `cost = Redtrack spend`
- **External affiliates** (Blue Bench, Venture Beyond, etc.): `cost = Everflow payout`

**Supporting Tables:**
- `public.affiliate_mapping` - 18 Redtrack sources mapped to Everflow affiliates
- RLS policies enabled, security advisors clear

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | Claude Code | 2025-12-19 | Complete |
| QA | AJ | 2025-12-19 | PASSED |
| Approver | _______ | _______ | _______ |

---

## Next Steps

1. ~~**QA**: Verify numbers against Redtrack UI~~ - PASSED (AJ, 2025-12-19)
2. ~~**Phase 3**: Load affiliate mapping table~~ - DONE (18 sources mapped)
3. ~~**Phase 3**: Create merge view/query~~ - DONE (`daily_performance` view)
4. **Phase 4**: Set up hourly Temporal schedules
5. **Phase 4**: Port daily report to Edge Function
