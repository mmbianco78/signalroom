# [Source Name] Implementation Summary

**Date**: YYYY-MM-DD
**Status**: Phase X Complete - Pending Team Sign-off
**Branch**: `phase-X-source-name`

---

## Overview

[1-2 sentence description of what this integration does and where data lands.]

**Destination Table**: `schema.table_name`

---

## Data Filtering

### What We Pull

| Dimension | Filter Applied | Current Behavior |
|-----------|----------------|------------------|
| **[Dimension 1]** | None/Yes | Description |
| **[Dimension 2]** | None/Yes | Description |
| **Date Range** | Manual param | Date range loaded |

### [Dimension] Breakdown (Currently Loaded)

| ID | Name | Rows | Key Metric 1 | Key Metric 2 |
|----|------|------|--------------|--------------|
| 1 | Example | 100 | 500 | $1,000 |

### Filtering Options

[Describe how to filter at runtime with example commands]

```bash
# Example: Filter by X
python -c "from signalroom.pipelines.runner import run_pipeline; \
  run_pipeline('source_name', source_kwargs={'filter_param': 'value'})"
```

**Recommendation**: [State recommended approach - e.g., load all, filter at query time]

---

## Date Range & Timeline

### Currently Loaded

| Metric | Value |
|--------|-------|
| Earliest date | YYYY-MM-DD |
| Latest date | YYYY-MM-DD |
| Days loaded | X |
| Total rows | X |

### Available (Not Yet Loaded)

| Month | Days Available | Status |
|-------|----------------|--------|
| YYYY-MM | X | Not loaded |
| YYYY-MM | X | **Loaded** |

### Backfill Options

| Option | Date Range | Est. Rows | Command |
|--------|------------|-----------|---------|
| Full history | Date - Date | ~X | `start_date='YYYY-MM-DD'` |
| Recent only | Date - Date | ~X | Already done |

---

## Scheduling Strategy

### Current System (if replacing existing)

[Describe what system is being replaced and its schedule]

| Schedule | Frequency | Notes |
|----------|-----------|-------|
| Example | Hourly | 7am-11pm ET |

### SignalRoom Target Schedule

| Schedule | Time | Date Range | Purpose |
|----------|------|------------|---------|
| **Primary sync** | X:00 AM ET | Today/Yesterday | Main data ingestion |
| **Backup sync** | X:00 AM ET | Last N days | Safety net |

### Key Requirements

1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

### Write Disposition

The pipeline uses **[append/merge/replace]** mode with primary key `(field1, field2)`:
- [Behavior description]
- [Idempotency note]

---

## Technical Details

### API Endpoint

```
[METHOD] https://api.example.com/endpoint
```

### Authentication

```
Header: X-API-Key: {api_key}
```

### Schema

| Column | Type | Description |
|--------|------|-------------|
| field_1 | text | Description |
| field_2 | integer | Description |
| _client_id | text | Client identifier |
| _loaded_at | text | ETL timestamp |

### Primary Key

```sql
PRIMARY KEY (field_1, field_2)
```

---

## QA Checklist

Please verify the following stats against the source system UI and report any discrepancies.

### 1. Total Summary Check

**SignalRoom values** (query in Supabase):
```sql
SELECT
    COUNT(*) as rows,
    SUM(metric_1) as total_metric_1
FROM schema.table_name
WHERE date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD';
```

| Metric | SignalRoom Value | Source UI Value | Match? |
|--------|------------------|-----------------|--------|
| Rows | X | ___________ | |
| Metric 1 | X | ___________ | |

### 2. Single Day Spot Check

**SignalRoom values**:
```sql
SELECT SUM(metric_1) FROM schema.table_name WHERE date = 'YYYY-MM-DD';
```

| Metric | SignalRoom Value | Source UI Value | Match? |
|--------|------------------|-----------------|--------|
| Metric 1 | X | ___________ | |

### 3. Breakdown Check

**SignalRoom values**:
```sql
SELECT dimension, SUM(metric_1) as total
FROM schema.table_name
GROUP BY dimension
ORDER BY total DESC
LIMIT 5;
```

| Rank | Dimension | SignalRoom Value | Source UI | Match? |
|------|-----------|------------------|-----------|--------|
| 1 | Example | X | _______ | |
| 2 | Example | X | _______ | |

---

## Sign-off

| Reviewer | Date | Status | Notes |
|----------|------|--------|-------|
| | | Pending | |
| | | Pending | |

### Approval Criteria

- [ ] QA metrics match source UI (within 1% tolerance)
- [ ] All expected dimensions present
- [ ] Date range correct
- [ ] No duplicate records
- [ ] Schema looks correct

---

## Next Steps (Post Sign-off)

1. **Merge Phase X** → `main` branch
2. **Backfill decision** → Full history or recent only?
3. **Phase X+1** → Next source implementation
