# Everflow Implementation Summary

**Date**: December 19, 2025
**Status**: Phase 1 Complete - Pending Team Sign-off
**Branch**: `phase-1-everflow`

---

## Overview

SignalRoom now ingests affiliate performance data from Everflow's Network API into Supabase. Data is grouped by date, affiliate, and advertiser for daily reporting and analysis.

**Destination Table**: `everflow.daily_stats`

---

## Data Filtering

### What We Pull

| Dimension | Filter Applied | Current Behavior |
|-----------|----------------|------------------|
| **Advertisers** | None | All 9 advertisers loaded |
| **Affiliates** | None | All 37 affiliates loaded |
| **Date Range** | Manual param | Dec 1-18, 2025 loaded |
| **Metrics** | None | All metrics included |

### Advertiser Breakdown (Currently Loaded)

| ID | Advertiser | Rows | Conversions | Clicks | Payout |
|----|------------|------|-------------|--------|--------|
| 1 | **CCW** | 378 | 4,592 | 116,202 | $124,340 |
| 2 | **EXP** | 14 | 1 | 21 | $0 |
| 5 | Concussion Media | 1 | 0 | 1 | $0 |
| 6 | USM | 1 | 0 | 2 | $0 |
| 8 | Parasite | 2 | 0 | 2 | $0 |
| 9 | Zevay | 12 | 0 | 384 | $0 |
| 10 | Adprecise 3rd Party | 18 | 0 | 547 | $0 |
| 11 | Habit Buddy | 10 | 1 | 367 | $0 |
| 12 | Bizlago | 8 | 1 | 93 | $293 |

### Filtering Options

The pipeline supports optional filtering at runtime:

```bash
# All advertisers (current default)
python -c "from signalroom.pipelines.runner import run_pipeline; \
  run_pipeline('everflow', source_kwargs={'start_date': '2025-12-01', 'end_date': '2025-12-18'})"

# CCW only (advertiser_id=1)
python -c "from signalroom.pipelines.runner import run_pipeline; \
  run_pipeline('everflow', source_kwargs={'start_date': '2025-12-01', 'end_date': '2025-12-18', 'advertiser_id': 1})"

# EXP only (advertiser_id=2)
python -c "from signalroom.pipelines.runner import run_pipeline; \
  run_pipeline('everflow', source_kwargs={'advertiser_id': 2})"
```

**Recommendation**: Load all advertisers, filter at query time in SQL for flexibility.

---

## Date Range & Timeline

### Currently Loaded

| Metric | Value |
|--------|-------|
| Earliest date | 2025-12-01 |
| Latest date | 2025-12-18 |
| Days loaded | 18 |
| Total rows | 444 |

### Available in Everflow (Not Yet Loaded)

| Month | Days Available | Status |
|-------|----------------|--------|
| 2025-01 | 15 (starts Jan 10) | Not loaded |
| 2025-02 | 25 | Not loaded |
| 2025-03 | 31 | Not loaded |
| 2025-04 | 30 | Not loaded |
| 2025-05 | 31 | Not loaded |
| 2025-06 | 30 | Not loaded |
| 2025-07 | 31 | Not loaded |
| 2025-08 | 31 | Not loaded |
| 2025-09 | 30 | Not loaded |
| 2025-10 | 31 | Not loaded |
| 2025-11 | 30 | Not loaded |
| 2025-12 | 18 | **Loaded** |

**Total available**: 5,515 rows (Jan 10 - Dec 18, 2025)

### Backfill Options

| Option | Date Range | Est. Rows | Command |
|--------|------------|-----------|---------|
| Full 2025 | Jan 10 - Dec 18 | ~5,515 | `start_date='2025-01-10', end_date='2025-12-18'` |
| Q4 2025 | Oct 1 - Dec 18 | ~2,000 | `start_date='2025-10-01', end_date='2025-12-18'` |
| Keep Dec only | Dec 1 - Dec 18 | 444 | Already done |

---

## Scheduling Strategy

### Planned Schedule (Phase 4)

| Schedule | Time | Date Range | Purpose |
|----------|------|------------|---------|
| **Daily sync** | 6:00 AM ET | Yesterday | Primary data ingestion |
| **Weekly catchup** | Sunday 7:00 AM ET | Last 7 days | Safety net for missed syncs |

### Default Behavior

When no dates are specified, the pipeline automatically fetches **yesterday's data**:

```python
# Defaults to yesterday
run_pipeline('everflow')
# Equivalent to: start_date=yesterday, end_date=yesterday
```

### Write Disposition: Merge

The pipeline uses **merge** (upsert) mode with primary key `(date, affiliate_id, advertiser_id)`:
- Re-running the same date range updates existing records
- No duplicates created
- Safe to backfill or re-sync any date range

---

## Technical Details

### API Endpoint

```
POST https://api.eflow.team/v1/networks/reporting/entity/table
```

### Authentication

```
Header: X-Eflow-API-Key: {api_key}
```

### Schema

| Column | Type | Description |
|--------|------|-------------|
| date | text | Report date (YYYY-MM-DD) |
| affiliate_id | integer | Everflow affiliate ID |
| affiliate_label | text | Affiliate name |
| advertiser_id | integer | Advertiser/brand ID |
| advertiser_label | text | Advertiser name |
| clicks | integer | Total click count |
| conversions | integer | Conversion count |
| revenue | numeric | Gross revenue |
| payout | numeric | Affiliate payout |
| profit | numeric | Net profit (revenue - payout) |
| _client_id | text | Client identifier (713) |
| _loaded_at | text | ETL timestamp |

### Primary Key

```sql
PRIMARY KEY (date, affiliate_id, advertiser_id)
```

---

## QA Checklist

Please verify the following stats against Everflow's reporting UI and report any discrepancies.

### 1. December 2025 Totals (CCW - Advertiser ID 1)

**SignalRoom values** (query in Supabase):
```sql
SELECT
    SUM(conversions) as conversions,
    SUM(clicks) as clicks,
    ROUND(SUM(payout)::numeric, 2) as payout
FROM everflow.daily_stats
WHERE advertiser_id = 1
  AND date BETWEEN '2025-12-01' AND '2025-12-18';
```

| Metric | SignalRoom Value | Everflow UI Value | Match? |
|--------|------------------|-------------------|--------|
| Conversions | 4,592 | ___________ | |
| Clicks | 116,202 | ___________ | |
| Payout | $124,340.00 | ___________ | |

### 2. Single Day Spot Check (Dec 17, 2025 - CCW)

**SignalRoom values**:
```sql
SELECT
    SUM(conversions) as conversions,
    SUM(clicks) as clicks,
    ROUND(SUM(payout)::numeric, 2) as payout
FROM everflow.daily_stats
WHERE advertiser_id = 1 AND date = '2025-12-17';
```

| Metric | SignalRoom Value | Everflow UI Value | Match? |
|--------|------------------|-------------------|--------|
| Conversions | 435 | ___________ | |
| Clicks | 11,981 | ___________ | |
| Payout | $8,855.00 | ___________ | |

### 3. Top Affiliates Check (Dec 1-18, CCW)

**SignalRoom values**:
```sql
SELECT
    affiliate_label,
    SUM(conversions) as conversions
FROM everflow.daily_stats
WHERE advertiser_id = 1
GROUP BY affiliate_label
ORDER BY conversions DESC
LIMIT 5;
```

| Rank | Affiliate | SignalRoom Conversions | Everflow UI | Match? |
|------|-----------|------------------------|-------------|--------|
| 1 | G2 - Meta | 1,678 | _______ | |
| 2 | Blue Bench Media LLC | 1,226 | _______ | |
| 3 | SB - Meta | 471 | _______ | |
| 4 | Venture Beyond | 362 | _______ | |
| 5 | ProfitFuel | 359 | _______ | |

### 4. Advertiser Count Check

**SignalRoom values**:
```sql
SELECT COUNT(DISTINCT advertiser_id) as advertisers
FROM everflow.daily_stats;
```

| Metric | SignalRoom Value | Expected | Match? |
|--------|------------------|----------|--------|
| Distinct advertisers | 9 | _______ | |

---

## Sign-off

| Reviewer | Date | Status | Notes |
|----------|------|--------|-------|
| | | Pending | |
| | | Pending | |

### Approval Criteria

- [ ] QA metrics match Everflow UI (within 1% tolerance)
- [ ] All expected advertisers present
- [ ] Date range correct
- [ ] No duplicate records
- [ ] Schema looks correct

---

## Next Steps (Post Sign-off)

1. **Merge Phase 1** → `main` branch
2. **Backfill decision** → Full 2025 or Q4 only?
3. **Phase 2** → Redtrack source implementation
4. **Phase 3** → Affiliate mapping (Redtrack ↔ Everflow)
5. **Phase 4** → Temporal scheduling (daily automated syncs)
