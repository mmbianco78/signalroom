# Roadmap

## Current State: Foundation Complete (~60% production-ready)

The core architecture is solid:
- Temporal integration working
- dlt pipeline runner working
- 2 of 6 sources implemented (posthog, mautic)
- 1 source partially implemented (s3_exports)
- Notifications working
- Docker/compose ready

**Not ready for production data flows** due to gaps below.

---

## Critical Gaps

### 1. No State Tracking / Resumability

**Problem**: If a pipeline fails mid-run, we restart from scratch. No checkpointing.

**Impact**:
- Wasted compute re-processing already-loaded data
- Risk of duplicates if failure happens after partial Postgres insert
- Can't resume from where we left off

**Solution**:
- [ ] Implement dlt state tracking for s3_exports (track processed files)
- [ ] Implement incremental loading with state persistence
- [ ] Add activity-level checkpointing for large batches

**Example** (s3_exports):
```python
@dlt.resource
def daily_exports():
    # Get state of processed files
    processed = dlt.current.resource_state().setdefault("processed_files", [])

    for file_path in files:
        if file_path in processed:
            continue  # Skip already processed

        yield from process_file(file_path)

        # Mark as processed
        processed.append(file_path)
```

---

### 2. No Client Tagging

**Problem**: `clients.py` exists but is never used. Data has no `_client_id` column.

**Impact**:
- Can't filter data by client
- Can't run per-client analytics
- Can't isolate client data

**Solution**:
- [ ] Pass `client_id` through pipeline chain
- [ ] Inject `_client_id` column in all sources
- [ ] Update workflows to accept client_id parameter

---

### 3. No Tests

**Problem**: Only `conftest.py` exists. Zero test coverage.

**Impact**:
- Can't refactor safely
- Can't catch regressions
- No confidence in changes

**Solution**:
- [ ] Unit tests for each source (mock API responses)
- [ ] Integration tests with DuckDB destination
- [ ] Workflow tests with Temporal test framework

---

### 4. Stubbed Sources

**Problem**: 3 of 6 sources are stubs returning no data.

| Source | Status | Priority |
|--------|--------|----------|
| everflow | Stubbed | High (affiliate data) |
| redtrack | Stubbed | Medium |
| google_sheets | Stubbed | Low |

**Solution**:
- [ ] Implement everflow source with reporting API
- [ ] Implement redtrack source
- [ ] Implement google_sheets source

---

### 5. No Cron Scheduling

**Problem**: `ScheduledSyncWorkflow` exists but no cron trigger.

**Impact**: Must manually trigger syncs or use external cron.

**Solution**:
- [ ] Add Temporal schedules for daily/hourly syncs
- [ ] Make schedule configurable per source

---

### 6. No Metrics / Observability

**Problem**: Logging only. No metrics, no traces.

**Impact**:
- Can't track rows loaded over time
- Can't measure pipeline duration trends
- No alerting on anomalies (e.g., 0 rows loaded)

**Solution**:
- [ ] Add Prometheus metrics (row counts, duration, errors)
- [ ] Add OpenTelemetry tracing
- [ ] Add anomaly detection (e.g., "loaded 0 rows, expected 1000+")

---

### 7. No Dead Letter Handling

**Problem**: Failed activities are logged but not archived for replay.

**Impact**:
- Can't inspect failed payloads
- Can't retry specific failures
- Lost visibility into error patterns

**Solution**:
- [ ] Archive failed activity inputs to a DLQ table
- [ ] Add retry-from-DLQ capability
- [ ] Dashboard for failure analysis

---

## Priority Order

### Phase 1: Make It Work (Before first real data)

| Task | Why | Effort |
|------|-----|--------|
| Add client_id tagging | Core requirement for multi-client | 2h |
| Implement s3_exports state tracking | Avoid reprocessing files | 4h |
| Fix s3_exports to use S3_PREFIXES | Support multiple paths | 1h |
| Basic tests for s3_exports | Confidence before real data | 4h |

### Phase 2: Make It Reliable (Before production)

| Task | Why | Effort |
|------|-----|--------|
| Implement everflow source | Key affiliate data | 8h |
| Add Temporal cron schedules | Automated syncs | 4h |
| Activity idempotency checks | Prevent duplicates | 4h |
| Integration tests | Catch regressions | 8h |

### Phase 3: Make It Observable (Production-ready)

| Task | Why | Effort |
|------|-----|--------|
| Prometheus metrics | Track health | 4h |
| Anomaly alerting | Catch issues early | 4h |
| Dead letter queue | Debug failures | 8h |
| Distributed tracing | Debug slow pipelines | 4h |

### Phase 4: Make It Complete

| Task | Why | Effort |
|------|-----|--------|
| Implement redtrack source | More data sources | 8h |
| Implement google_sheets source | Manual data entry | 4h |
| Schema validation | Catch breaking changes | 4h |
| Workflow versioning | Safe deploys | 4h |

---

## Open Questions

### Architecture

1. **Single vs Multiple Datasets**: Should each client have its own Postgres schema (e.g., `client_713.orders`) or shared schema with `_client_id` column?

2. **Project Mapping**: How do we map data to projects (CCW, Expungement)? Lookup tables vs naming conventions?

3. **Browser Worker**: When do we need headless browser automation? Which sources require it?

### Operations

4. **Supabase Project**: Which Supabase project is the production destination? Need connection details.

5. **Alerting Channels**: Slack only, or also email/SMS? Who gets notified?

6. **Backup Strategy**: How often to backup? Who owns Supabase backups?

### Sources

7. **S3 Data Structure**: Do the CSVs in `orders-create`, `orders-update`, `prospects-create` have consistent schemas? Do they need different tables?

8. **Everflow/Redtrack Access**: Do we have API credentials? What endpoints do we need?

9. **Historical Data**: How much historical data to backfill? Date ranges?

---

## Definition of Done: Production-Ready

- [ ] All sources implemented and tested
- [ ] Client tagging working
- [ ] State tracking for incremental loads
- [ ] Cron schedules configured
- [ ] Metrics dashboard
- [ ] Alerting on failures and anomalies
- [ ] Runbook documented
- [ ] At least one successful week of automated syncs

---

## Technical Debt

| Item | Location | Notes |
|------|----------|-------|
| TODO: Track processed files | s3_exports/__init__.py:58 | Needs dlt state |
| TODO: Token caching | mautic/__init__.py | Wasteful token refresh |
| Empty sources list | clients.py:29,34 | Never configured |
| Hardcoded Slack | workflows.py:67,79 | Should be configurable |
| No error classification | temporal/config.py | All errors retry same way |
