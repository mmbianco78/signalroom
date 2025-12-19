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

### Blocking
- [ ] Temporal namespace activation (waiting on Temporal Cloud)

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

### Phase 2: Temporal Scheduling

**Goal**: Replicate automated-reporting's hourly schedule.

| Task | Status | Notes |
|------|--------|-------|
| Test Temporal Cloud connection | TODO | Waiting on namespace activation |
| Create `SyncSourceWorkflow` | DONE | In `temporal/workflows.py` |
| Everflow hourly sync (7am-11pm ET) | TODO | Current day data |
| Redtrack hourly sync (7am-11pm ET) | TODO | Current day data |
| S3 daily sync (6am ET) | TODO | orders_create, orders_update |
| Workflow error handling | TODO | Retry + notification on failure |

**Schedule** (matches automated-reporting):
```
Hourly 7am-11pm ET: Sync Everflow + Redtrack (current day)
Daily 6am ET: Sync S3 exports
Daily 7am ET: Send daily summary report
```

---

### Phase 3: Report Templates (Jinja2)

**Goal**: Templated reports for Slack, Email, SMS using Jinja2.

| Task | Status | Notes |
|------|--------|-------|
| Add Jinja2 dependency | TODO | `uv add jinja2` |
| Add MJML dependency | TODO | `uv add mjml` (for responsive emails) |
| Create `reports/` module structure | TODO | See below |
| Implement report registry | TODO | Report definitions with SQL + template |
| Daily CCW Summary (Slack) | TODO | Port from automated-reporting |
| Daily CCW Summary (Email) | TODO | MJML template |
| Alert template (SMS) | TODO | Simple text |
| Slack Block Kit builder | TODO | Consider `blockkit` or `slackblocks` |

**Module Structure**:
```
src/signalroom/reports/
├── __init__.py
├── registry.py              # Report definitions
├── renderer.py              # Jinja2 + MJML rendering
├── templates/
│   ├── daily_ccw.slack.j2   # Slack markdown/blocks
│   ├── daily_ccw.email.mjml # Responsive email
│   └── alert.sms.j2         # SMS text
└── queries/
    └── daily_ccw.sql        # SQL for report data
```

**Report Definition Pattern**:
```python
@report(
    name="daily_ccw",
    schedule="0 7 * * *",  # 7am daily
    channels=["slack", "email"],
)
def daily_ccw_report(date: str, advertiser_id: int = 1):
    # Returns data dict for template rendering
    ...
```

---

### Phase 4: Deployment (Fly.io)

**Goal**: Run Temporal worker in production.

| Task | Status | Notes |
|------|--------|-------|
| Create Fly.io account/app | TODO | `fly launch` |
| Configure secrets | TODO | API keys, Supabase, Temporal |
| Deploy worker container | TODO | `fly deploy` |
| Set up health checks | TODO | Worker heartbeat |
| Configure auto-restart | TODO | On failure |
| Test end-to-end | TODO | Trigger workflow, verify report |

**Fly.io Config** (`fly.toml`):
```toml
app = "signalroom-worker"
primary_region = "iad"  # US East

[build]
  dockerfile = "Dockerfile"

[env]
  TEMPORAL_NAMESPACE = "signalroom-713.nzg5u"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.http_checks]]
    interval = "15s"
    timeout = "2s"
    path = "/health"
```

---

### Phase 5: Go-Live

**Goal**: Switch from automated-reporting to SignalRoom.

| Task | Status | Notes |
|------|--------|-------|
| Run parallel for 1 week | TODO | Both systems sending reports |
| Compare outputs | TODO | Verify data matches |
| Disable automated-reporting | TODO | After validation |
| Monitor for issues | TODO | First week in production |
| Document runbook | TODO | How to debug/restart |

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

1. **Temporal namespace activation** - Unblocks everything
2. **Add Jinja2 + report module skeleton** - Can start without Temporal
3. **Port daily CCW report logic** - SQL + Slack template
4. **Fly.io setup** - Account, app, secrets
5. **End-to-end test** - Manual trigger → Slack message

---

## Open Questions (Resolved)

| Question | Answer |
|----------|--------|
| Supabase project? | 713 Main DB (foieoinshqlescyocbld) |
| Temporal namespace? | signalroom-713.nzg5u |
| Report templating? | Jinja2 + MJML (Python-native) |
| Deployment target? | Fly.io |
