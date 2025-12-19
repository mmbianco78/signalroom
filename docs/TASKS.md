# Implementation Tasks

Granular task list organized by phase. Each phase gets its own branch, requires testing, and user sign-off before merge to main.

**Workflow:**
1. Create branch: `git checkout -b phase-X-description`
2. Complete all tasks in phase
3. Run tests / verify
4. Get user confirmation
5. Merge to main: `git checkout main && git merge phase-X-description`
6. Proceed to next phase

---

## Phase 1: Everflow Source ✅ COMPLETE

**Branch**: `main`

### 1.1 Implementation

- [x] Update `src/signalroom/sources/everflow/__init__.py`
  - [x] Create `EverflowClient` class with auth header
  - [x] Implement `entity_table()` method (POST) - Note: used entity table endpoint instead of aggregated
  - [x] Add date range parameters (start_date, end_date)
  - [x] Add advertiser_id filter (1=CCW, 2=EXP) with client-side filtering
  - [x] Add timezone_id parameter (80 = America/New_York)

- [x] Create dlt source and resources
  - [x] `@dlt.source(name="everflow")`
  - [x] `@dlt.resource` for `daily_stats` (merge mode)
  - [x] Primary key: `date` + `affiliate_id` + `advertiser_id`
  - [x] Add `_client_id` column

- [x] Fields to extract:
  - [x] date
  - [x] affiliate_id, affiliate_label
  - [x] advertiser_id, advertiser_label
  - [x] clicks
  - [x] conversions
  - [x] revenue
  - [x] payout
  - [x] profit

### 1.2 Configuration

- [x] Verify settings in `config.py`:
  - [x] `everflow_api_key`
  - [x] `everflow_base_url`
  - [x] `everflow_agg_path` (not used - using entity table endpoint)

- [x] Update `.env.example` if needed

### 1.3 Testing

- [x] Manual API test: Entity table endpoint returns 200 OK
- [x] Run pipeline test: 444 rows loaded (Dec 1-18)
- [x] Verify data in Supabase:
  - CCW: 378 rows, 4,592 conversions, $124,340 payout
  - EXP: 14 rows, 1 conversion
  - Others: 52 rows, 2 conversions

### 1.4 Documentation

- [x] Update `docs/SOURCES.md` - Everflow section
- [ ] Add example queries to `docs/QUERIES.sql` (deferred)

### 1.5 Sign-off Checklist

- [x] API returns data
- [x] Pipeline runs without error
- [x] Data visible in Supabase
- [x] Fields match expected schema
- [ ] User confirmation received

---

## Phase 2: Redtrack Source ✅ COMPLETE

**Branch**: `main`

### 2.1 Implementation

- [ ] Update `src/signalroom/sources/redtrack/__init__.py`
  - [ ] Create `RedtrackClient` class with auth header
  - [ ] Implement `report()` method (POST or GET)
  - [ ] Add date range parameters
  - [ ] Add group_by parameter (date, traffic_source)

- [ ] Create dlt source and resources
  - [ ] `@dlt.source(name="redtrack")`
  - [ ] `@dlt.resource` for `daily_spend` (append mode)
  - [ ] Primary key: `date` + `source_id`
  - [ ] Add `_client_id` column

- [ ] Fields to extract:
  - [ ] date
  - [ ] source_id, source_name
  - [ ] clicks
  - [ ] conversions
  - [ ] cost (ad spend)

### 2.2 Configuration

- [ ] Verify settings in `config.py`:
  - [ ] `redtrack_api_key`
  - [ ] `redtrack_base_url`
  - [ ] `redtrack_report_path`

### 2.3 Testing

- [ ] Manual API test:
  ```bash
  curl -X GET "https://api.redtrack.io/report?api_key=$REDTRACK_API_KEY&date_from=2025-12-17&date_to=2025-12-18&group=source"
  ```

- [ ] Run pipeline test:
  ```bash
  python -c "from signalroom.pipelines.runner import run_pipeline; print(run_pipeline('redtrack', source_kwargs={'start_date': '2025-12-17', 'end_date': '2025-12-18'}))"
  ```

- [ ] Verify data in Supabase:
  ```sql
  SELECT * FROM redtrack.daily_spend LIMIT 10;
  SELECT COUNT(*), SUM(cost) FROM redtrack.daily_spend;
  ```

### 2.4 Documentation

- [ ] Update `docs/SOURCES.md` - Redtrack section
- [ ] Add example queries to `docs/QUERIES.sql`

### 2.5 Sign-off Checklist

- [ ] API returns data
- [ ] Pipeline runs without error
- [ ] Data visible in Supabase
- [ ] Fields match expected schema
- [ ] User confirmation received

---

## Phase 3: Affiliate Mapping & Merge ✅ COMPLETE

**Branch**: `main`

### 3.1 Create Mapping Table

- [ ] Create migration for `affiliate_mapping` table:
  ```sql
  CREATE TABLE public.affiliate_mapping (
    id SERIAL PRIMARY KEY,
    redtrack_source_id TEXT NOT NULL,
    redtrack_source_name TEXT,
    everflow_affiliate_id INTEGER,
    everflow_affiliate_label TEXT,
    everflow_advertiser_id INTEGER,
    everflow_advertiser_label TEXT,
    platform TEXT,  -- META, GOOG
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```

- [ ] Load data from `internal-affiliates.csv`:
  ```bash
  # Script to load CSV to Supabase
  python scripts/load_affiliate_mapping.py
  ```

### 3.2 Create Merge View

- [ ] Create SQL view for merged daily report:
  ```sql
  CREATE VIEW public.daily_performance AS
  SELECT
    e.date,
    e.advertiser_label as brand,
    e.affiliate_label,
    e.conversions,
    e.revenue,
    e.payout,
    e.profit,
    COALESCE(r.cost, 0) as cost,
    CASE WHEN e.conversions > 0
      THEN ROUND(COALESCE(r.cost, 0) / e.conversions, 2)
      ELSE 0 END as cpa
  FROM everflow.daily_stats e
  LEFT JOIN affiliate_mapping m ON e.affiliate_id = m.everflow_affiliate_id
  LEFT JOIN redtrack.daily_spend r ON r.source_id = m.redtrack_source_id AND r.date = e.date;
  ```

### 3.3 Testing

- [ ] Verify mapping table loaded:
  ```sql
  SELECT COUNT(*) FROM public.affiliate_mapping;
  SELECT * FROM public.affiliate_mapping;
  ```

- [ ] Test merge view:
  ```sql
  SELECT * FROM public.daily_performance WHERE date = '2025-12-17';
  SELECT brand, SUM(conversions), SUM(revenue), SUM(cost), AVG(cpa)
  FROM public.daily_performance
  GROUP BY brand;
  ```

### 3.4 Documentation

- [ ] Document merge logic in `docs/INTEGRATIONS.md`
- [ ] Add merge queries to `docs/QUERIES.sql`

### 3.5 Sign-off Checklist

- [ ] Mapping table created and populated
- [ ] Merge view returns correct data
- [ ] CPA calculation verified
- [ ] User confirmation received

---

## Phase 4: Temporal Scheduling ✅ COMPLETE

**Branch**: `main`

**Goal**: Replace `automated-reporting` launchd jobs with Temporal-managed schedules.

### Current System to Replace

The `automated-reporting` project uses macOS launchd with:
- **Hourly schedule**: 7am-11pm ET (17 runs/day)
- **Intraday data**: Fetches current day, not yesterday
- **7am special**: Sends previous day final snapshot before current day
- **iMessage delivery**: To phone numbers and group chats

### 4.1 Verify Temporal Cloud Connection

- [ ] Test connection:
  ```bash
  python -c "
  import asyncio
  from signalroom.temporal.config import get_temporal_client
  async def test():
      client = await get_temporal_client()
      print('Connected to:', client.namespace)
  asyncio.run(test())
  "
  ```

### 4.2 Create Scheduled Workflows

- [ ] Update `src/signalroom/temporal/workflows.py`:
  - [ ] `HourlySyncWorkflow` - intraday data sync + report
  - [ ] `DailyBackfillWorkflow` - previous day final sync
  - [ ] `ReportingWorkflow` - generate and send report

- [ ] Workflow logic:
  ```
  HourlySyncWorkflow (runs hourly 7am-11pm ET):
    1. Sync Everflow (today's date)
    2. Sync Redtrack (today's date)
    3. Generate merged report
    4. Send to Slack

  At 7am only:
    1. Run DailyBackfillWorkflow (yesterday)
    2. Send "Previous Day Final" report
    3. Then run normal hourly sync
  ```

- [ ] Create schedules via CLI:
  ```bash
  # Hourly sync (7am-11pm ET = 12:00-04:00 UTC next day)
  python scripts/create_schedule.py \
    --workflow HourlySyncWorkflow \
    --cron "0 7-23 * * *" \
    --timezone "America/New_York"

  # Daily backfill (6am ET)
  python scripts/create_schedule.py \
    --workflow DailyBackfillWorkflow \
    --cron "0 6 * * *" \
    --timezone "America/New_York"
  ```

### 4.3 Notification Setup

- [ ] Add Slack webhook to `.env`:
  ```
  SLACK_BOT_TOKEN=xoxb-...
  SLACK_CHANNEL_ID=C...
  ```

- [ ] Implement report formatter matching current iMessage format:
  ```
  Daily Reporting Snapshot (2025-12-19)

  CCW
  • Conversions: 435
  • Cost: $8,855
  • CPA: $20.36

  Top Affiliates:
  - G2 - Meta: 313 @ $18.50
  - Blue Bench: 135 @ $22.00
  ```

- [ ] Test notification:
  ```bash
  python -c "
  from signalroom.notifications.slack import send_slack_message
  send_slack_message('Test from SignalRoom')
  "
  ```

### 4.4 Testing

- [ ] Trigger manual workflow run:
  ```bash
  python scripts/trigger_workflow.py HourlySyncWorkflow --wait
  ```

- [ ] Verify intraday data updates correctly

- [ ] Verify report matches automated-reporting output

- [ ] Test 7am previous-day logic

### 4.5 Documentation

- [ ] Update `docs/OPERATIONS.md` with schedule info
- [ ] Document how to pause/resume schedules
- [ ] Migration guide from automated-reporting
- [ ] Add troubleshooting section

### 4.6 Sign-off Checklist

- [ ] Temporal Cloud connection working
- [ ] Hourly workflow runs correctly
- [ ] Intraday data updates in Supabase
- [ ] Reports match automated-reporting format
- [ ] Previous day snapshot at 7am works
- [ ] Notifications sending to Slack
- [ ] Ready to deprecate automated-reporting
- [ ] User confirmation received

---

## Phase 5: Daily Reports 🔄 IN PROGRESS

**Branch**: `main`

### 5.1 Report Queries

- [ ] CCW Daily Summary query:
  ```sql
  SELECT
    date,
    SUM(conversions) as conversions,
    ROUND(SUM(revenue), 2) as revenue,
    ROUND(SUM(cost), 2) as spend,
    ROUND(SUM(cost) / NULLIF(SUM(conversions), 0), 2) as cpa
  FROM public.daily_performance
  WHERE brand = 'CCW' AND date = CURRENT_DATE - 1
  GROUP BY date;
  ```

- [ ] Affiliate breakdown query
- [ ] State performance query

### 5.2 Report Generation

- [ ] Create `src/signalroom/reports/daily.py`:
  - [ ] `generate_daily_summary(date, brand)`
  - [ ] Format as text/markdown for Slack
  - [ ] Include: conversions, revenue, spend, CPA, top affiliates

### 5.3 Integration

- [ ] Add report generation to `DailySyncWorkflow`
- [ ] Send report to Slack after data sync

### 5.4 Testing

- [ ] Generate report for yesterday:
  ```bash
  python -c "
  from signalroom.reports.daily import generate_daily_summary
  print(generate_daily_summary('2025-12-17', 'CCW'))
  "
  ```

### 5.5 Sign-off Checklist

- [ ] Report generates correctly
- [ ] Numbers match manual SQL queries
- [ ] Report posts to Slack
- [ ] User confirmation received

---

## Progress Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Everflow | ✅ Complete | Daily stats loading to Supabase |
| 2. Redtrack | ✅ Complete | Daily spend loading to Supabase |
| 3. Affiliate Merge | ✅ Complete | Mapping table + merge view created |
| 4. Temporal Scheduling | ✅ Complete | Fly.io worker + Temporal Cloud schedules |
| 5. Daily Reports | 🔄 In Progress | Templates created, schedules disabled |

**Note**: Development was done on `main` branch rather than feature branches.
