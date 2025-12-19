# Roadmap

## Sprint Goal: Replace automated-reporting

**Objective**: Get SignalRoom running in production, sending the same daily reports that automated-reporting currently sends.

**Success Criteria**:
- [ ] Hourly data syncs (Everflow, Redtrack) running on schedule
- [ ] Daily CCW summary report sent to Slack
- [ ] Running on Fly.io (or similar)
- [ ] automated-reporting can be decommissioned

---

## Current State (December 2025)

### Completed
- [x] S3 exports source (multi-prefix, client tagging)
- [x] Everflow source (daily_stats, merge by PK)
- [x] Redtrack source (daily_spend, merge by PK)
- [x] Merge logic (`daily_performance` view with CPA)
- [x] Temporal Cloud configured (signalroom-713.nzg5u)
- [x] Notification channels stubbed (Slack, Email, SMS)
- [x] 650k+ rows loaded to Supabase

### Unblocked
- [x] Temporal namespace activation (active as of Dec 2025)

---

## Sprint Phases

### Phase 1: Data Sources ✅ COMPLETE

All sources needed for daily reporting are implemented.

| Source | Status | Table | Notes |
|--------|--------|-------|-------|
| Everflow | ✅ Done | `everflow.daily_stats` | Conversions, payout by affiliate |
| Redtrack | ✅ Done | `redtrack.daily_spend` | Ad spend by source |
| Merge View | ✅ Done | `public.daily_performance` | Joined with CPA calculation |

---

### Phase 2: Temporal Scheduling ✅ COMPLETE

**Goal**: Replicate automated-reporting's hourly schedule.

| Task | Status | Notes |
|------|--------|-------|
| Test Temporal Cloud connection | ✅ Done | Connected to signalroom-713.nzg5u |
| Create `SyncSourceWorkflow` | ✅ Done | In `temporal/workflows.py` |
| Create `RunReportWorkflow` | ✅ Done | For scheduled report sending |
| Everflow hourly sync (7am-11pm ET) | ✅ Done | Schedule: hourly-sync-everflow-redtrack |
| Redtrack hourly sync (7am-11pm ET) | ✅ Done | Combined with Everflow schedule |
| S3 daily sync (6am ET) | ✅ Done | Schedule: daily-sync-s3 |
| Daily CCW report (7am ET) | ✅ Done | Schedule: daily-report-ccw |
| Workflow error handling | ✅ Done | Retry + Slack notification on failure |

**Active Schedules** (Temporal Cloud):
```
hourly-sync-everflow-redtrack  - Hourly 7am-11pm ET: Sync Everflow + Redtrack
daily-sync-s3                  - Daily 6am ET: Sync S3 exports
```

**Note**: Report schedules are currently disabled while we validate data quality.

---

### Phase 3: Report Templates (Jinja2) ✅ COMPLETE

**Goal**: Templated reports for Slack, Email, SMS using Jinja2.

| Task | Status | Notes |
|------|--------|-------|
| Add Jinja2 dependency | ✅ Done | `jinja2` |
| Add MJML dependency | ✅ Done | `mjml` |
| Create `reports/` module structure | ✅ Done | registry, renderer, runner |
| Implement report registry | ✅ Done | Report dataclass with templates |
| Daily CCW Summary (Slack) | ✅ Done | `daily_ccw.slack.j2` |
| Daily CCW Summary (Email) | ✅ Done | `daily_ccw.email.mjml` |
| Daily CCW Summary (SMS) | ✅ Done | `daily_ccw.sms.j2` |
| Alert templates (all channels) | ✅ Done | slack, email, sms |

**Templates Implemented**:
- `daily_ccw.slack.j2` - Slack mrkdwn with affiliate breakdown
- `daily_ccw.email.mjml` - Responsive HTML email
- `daily_ccw.sms.j2` - Short summary (160 chars)
- `alert.slack.j2` - Error/warning/info with icons
- `alert.email.mjml` - Responsive HTML alert
- `alert.sms.j2` - Alert text with level prefix

**Notification Channel Integration**: Pending (to be done one-by-one)

---

### Phase 4: Deployment (Fly.io) ✅ COMPLETE

**Goal**: Run Temporal worker in production.

| Task | Status | Notes |
|------|--------|-------|
| Create Fly.io account/app | ✅ Done | `signalroom-worker` |
| Configure secrets | ✅ Done | All API keys, Supabase pooler, Temporal Cloud |
| Deploy worker container | ✅ Done | 247MB image (no Playwright) |
| Worker connects to Temporal | ✅ Done | signalroom-713.nzg5u namespace |
| Test end-to-end sync | ✅ Done | Everflow + Redtrack syncing successfully |
| Test report via Temporal | ✅ Done | test_sync report sent to Slack |

**Production URLs**:
- Fly.io: https://fly.io/apps/signalroom-worker
- Temporal Cloud: https://cloud.temporal.io/namespaces/signalroom-713.nzg5u/workflows

**Key Configuration**:
- Supabase connection via pooler (port 6543)
- User format: `postgres.{project_ref}` (not just `postgres`)
- Secrets with special characters must be set via Fly.io dashboard (not CLI)

---

### Phase 5: Go-Live ← **IN PROGRESS**

**Goal**: Switch from automated-reporting to SignalRoom.

| Task | Status | Notes |
|------|--------|-------|
| Data syncs running in production | ✅ Done | Everflow + Redtrack hourly, S3 daily |
| Validate data quality | 🔄 In Progress | Comparing with automated-reporting |
| Enable report schedules | TODO | After data validation |
| Run parallel for 1 week | TODO | Both systems sending reports |
| Compare outputs | TODO | Verify data matches |
| Disable automated-reporting | TODO | After validation |
| Monitor for issues | TODO | First week in production |

---

## Future Phases (Post Go-Live)

### Production Hardening
| Task | Notes |
|------|-------|
| State tracking for S3 | Avoid reprocessing files |
| Incremental loading | Only fetch new data |
| Dead letter queue | Archive failed payloads |
| Anomaly detection | Alert on 0 rows, missing data |
| Prometheus metrics | Row counts, duration |
| OpenTelemetry tracing | Distributed tracing |

### Additional Reports
| Report | Notes |
|--------|-------|
| Daily EXP Summary | Same format as CCW |
| Affiliate Leaderboard | Top performers |
| State Heatmap Data | Geographic breakdown |
| Weekly Rollup | Week-over-week comparison |

### Additional Sources
| Source | Notes |
|--------|-------|
| PostHog | Product analytics |
| Mautic | Email marketing |
| Google Sheets | Manual data entry |

### Dashboards
| Task | Notes |
|------|-------|
| Evaluate BI tools | Metabase/Grafana/Retool |
| Build CCW dashboard | Real-time metrics |

### Infrastructure Improvements
See `docs/FUTURE_IMPROVEMENTS.md` for:
- Additional Everflow API endpoints
- Offer-based affiliate mapping (AFFID)
- Redtrack campaign/offer grouping

---

## Immediate Next Steps

1. ~~**Temporal namespace activation**~~ ✅ Active
2. ~~**Add Jinja2 + report module skeleton**~~ ✅ Complete
3. ~~**Port daily CCW report logic**~~ ✅ Complete
4. ~~**Fly.io setup**~~ ✅ Complete
5. ~~**Deploy worker**~~ ✅ Complete
6. ~~**End-to-end test**~~ ✅ Complete
7. **Validate data quality** ← **CURRENT**
8. **Enable report schedules** - After validation
9. **Parallel run with automated-reporting** - 1 week comparison

---

## Open Questions (Resolved)

| Question | Answer |
|----------|--------|
| Supabase project? | 713 Main DB (foieoinshqlescyocbld) |
| Temporal namespace? | signalroom-713.nzg5u |
| Report templating? | Jinja2 + MJML (Python-native) |
| Deployment target? | Fly.io |
