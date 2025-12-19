# Roadmap

## Current State (December 2025)

### Completed
- [x] S3 exports source fully implemented (multi-prefix, client tagging)
- [x] 650k rows loaded to Supabase (orders_create + orders_update)
- [x] Temporal Cloud configured (signalroom-713.nzg5u)
- [x] Everflow/Redtrack credentials and API docs captured
- [x] SQL query library created
- [x] Core architecture working
- [x] **Everflow source implemented** (444 rows, Dec 1-18)
- [x] Documentation templates created
- [x] Client data organization (data/clients/713/)
- [x] **Redtrack source implemented** (248 rows, Dec 1-18, $211K spend)
- [x] **Merge logic complete** (affiliate_mapping table + daily_performance view)

### In Progress
- [ ] Temporal namespace activation
- [ ] Hourly scheduling (to replace automated-reporting)

### Pending
- [ ] Daily report Edge Function (port from automated-reporting)

---

## Implementation Plan

### Phase 1: Complete Data Sources (Priority: High)

#### 1.1 Everflow Source ✅ COMPLETE
**Goal**: Pull affiliate conversion and revenue data

| Task | Status | Notes |
|------|--------|-------|
| Implement entity table endpoint | DONE | POST `/v1/networks/reporting/entity/table` |
| Add date range and advertiser filtering | DONE | advertiser_id: 1=CCW, 2=EXP |
| Fields: clicks, conversions, revenue, payout, profit | DONE | Group by date, affiliate, advertiser |
| Merge write disposition | DONE | Safe for re-runs |
| Test with real API | DONE | 444 rows loaded (Dec 1-18) |

**Details**: See `docs/EVERFLOW_IMPLEMENTATION.md`

#### 1.2 Redtrack Source ✅ COMPLETE
**Goal**: Pull ad spend data for internal affiliates

| Task | Status | Notes |
|------|--------|-------|
| Implement report endpoint | DONE | GET `/report` (POST returns 404) |
| Add date range filtering | DONE | One API call per day |
| Fields: clicks, conversions, cost | DONE | Group by source |
| Rate limiting | DONE | 1s delay + backoff on 429 |
| Test with real API | DONE | 248 rows loaded (Dec 1-18) |

**Details**: See `docs/REDTRACK_IMPLEMENTATION.md`

#### 1.3 Merge Logic ✅ COMPLETE
**Goal**: Join Everflow conversions with Redtrack spend

| Task | Status | Notes |
|------|--------|-------|
| Create affiliate mapping table in Supabase | DONE | 18 sources mapped |
| Daily merge view/query | DONE | `public.daily_performance` view |
| Calculate CPA (cost/conversions) | DONE | Internal uses Redtrack, external uses Everflow payout |
| RLS policies | DONE | Security advisors clear |

**Usage**:
```sql
-- Daily CCW summary
SELECT affiliate_label, conversions, cost, cpa, is_internal
FROM public.daily_performance
WHERE date = '2025-12-19' AND advertiser_id = 1
ORDER BY conversions DESC;
```

---

### Phase 2: Scheduling & Automation

#### 2.1 Temporal Schedules
| Task | Status | Notes |
|------|--------|-------|
| Daily S3 sync (6am ET) | TODO | orders_create, orders_update |
| Daily Everflow sync (7am ET) | TODO | After S3 completes |
| Daily Redtrack sync (7am ET) | TODO | After S3 completes |
| Daily merge report | TODO | After both complete |

#### 2.2 Notifications
| Task | Status | Notes |
|------|--------|-------|
| Slack alerts on failure | TODO | Already stubbed |
| Daily summary to Slack | TODO | Row counts, revenue |
| SMS alerts for critical failures | TODO | Via Twilio |

---

### Phase 3: Reports & Analytics

#### 3.1 Daily Reports (port from automated-reporting)
| Report | Status | Notes |
|--------|--------|-------|
| Daily CCW Summary | TODO | Conversions, revenue, spend, CPA |
| Daily EXP Summary | TODO | Same format |
| Affiliate Leaderboard | TODO | Top performers by revenue |
| State Heatmap Data | TODO | Geographic breakdown |

#### 3.2 Dashboards
| Task | Status | Notes |
|------|--------|-------|
| Supabase SQL queries working | DONE | docs/QUERIES.sql |
| Connect to visualization tool | TODO | Metabase/Grafana/Retool? |

---

### Phase 4: Production Hardening

#### 4.1 State Tracking
| Task | Status | Notes |
|------|--------|-------|
| S3: Track processed files | TODO | Avoid reprocessing |
| Everflow: Incremental by date | TODO | |
| Redtrack: Incremental by date | TODO | |

#### 4.2 Error Handling
| Task | Status | Notes |
|------|--------|-------|
| Retry policies tuned | DONE | 5 attempts, exponential backoff |
| Dead letter queue | TODO | Archive failed payloads |
| Anomaly detection | TODO | Alert on 0 rows, missing data |

#### 4.3 Observability
| Task | Status | Notes |
|------|--------|-------|
| Structured logging | DONE | structlog |
| Metrics (Prometheus) | TODO | Row counts, duration |
| Tracing (OpenTelemetry) | TODO | |

---

## Open Questions (Resolved)

| Question | Answer |
|----------|--------|
| Supabase project? | 713 Main DB (foieoinshqlescyocbld) |
| S3 data structure? | 3 prefixes, 129 columns, consistent schema |
| Everflow/Redtrack access? | Credentials captured, APIs documented |
| Client tagging? | `_client_id` column implemented |
| Project mapping? | Via `product_category` column (CCW, EXP) |

---

## Immediate Next Steps

1. ~~**QA sign-off on Redtrack**~~ ✅ Validated against automated-reporting
2. ~~**Create affiliate mapping table**~~ ✅ 18 sources loaded
3. ~~**Build merge query**~~ ✅ `daily_performance` view with CPA
4. **Test Temporal Cloud connection** - Once namespace is active
5. **Set up hourly schedules** - Match automated-reporting (7am-11pm ET)
6. **Port daily report to Edge Function** - Slack notifications

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 (Sources) | 2-3 days | Everflow/Redtrack API access |
| Phase 2 (Scheduling) | 1 day | Temporal namespace active |
| Phase 3 (Reports) | 1-2 days | Sources complete |
| Phase 4 (Hardening) | Ongoing | Production usage |

**Target**: Automated daily syncs running within 1 week.
