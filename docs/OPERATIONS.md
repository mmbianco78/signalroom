# Operations Runbook

## Quick Reference

| Task | Command |
|------|---------|
| Start everything | `make dev` |
| Start in background | `make up` |
| Stop everything | `make down` |
| View logs | `make logs` |
| Run pipeline manually | `python scripts/run_pipeline.py s3_exports` |
| Trigger via Temporal | `python scripts/trigger_workflow.py s3_exports -w` |
| Test report | `python -c "from signalroom.reports import run_report; print(run_report('daily_ccw'))"` |
| Setup schedules | `python scripts/setup_schedules.py` |
| Test Temporal connection | `python scripts/test_temporal_connection.py` |
| Open Temporal UI | http://localhost:8080 |

---

## Starting the System

### Development (foreground, with logs)

```bash
make dev
```

This starts:
- Temporal server (port 7233)
- Temporal UI (port 8080)
- Temporal Postgres (port 5433)
- API Worker

### Production-like (background)

```bash
make up
make logs  # tail logs
```

### Verify services are running

```bash
docker compose ps
```

Expected output:
```
NAME                      STATUS
signalroom-temporal       running
signalroom-temporal-ui    running
signalroom-temporal-db    running (healthy)
signalroom-worker         running
```

---

## Running Pipelines

### Direct execution (bypasses Temporal)

Use for testing and debugging. Runs synchronously in your terminal.

```bash
# Activate venv
source .venv/bin/activate

# Run a pipeline
python scripts/run_pipeline.py s3_exports

# Dry run (shows what would happen)
python scripts/run_pipeline.py s3_exports --dry-run

# Run specific resources only
python scripts/run_pipeline.py posthog -r events
```

### Via Temporal (production pattern)

Runs as a workflow with retries, visibility, and durability.

```bash
# Trigger and return immediately
python scripts/trigger_workflow.py s3_exports

# Trigger and wait for completion
python scripts/trigger_workflow.py s3_exports -w

# With specific resources
python scripts/trigger_workflow.py posthog -r events -w
```

View in Temporal UI: http://localhost:8080/namespaces/default/workflows

---

## Monitoring

### Temporal UI

Open http://localhost:8080

**Key views**:
- **Workflows**: See all running and completed workflows
- **Workflow Detail**: Click a workflow to see execution history
- **Pending Activities**: See activities waiting for workers

### Logs

```bash
# All services
make logs

# Worker only (most relevant for debugging pipelines)
make logs-worker

# Temporal server
make logs-temporal
```

### Log format

In development, logs are human-readable:
```
2024-01-15 10:30:00 [info] pipeline_starting source=s3_exports
2024-01-15 10:30:05 [info] found_s3_files count=15 pattern=bucket/prefix/**/*.csv
2024-01-15 10:30:30 [info] pipeline_completed load_id=1705312345 row_counts={"daily_exports": 1523}
```

In production (Docker), logs are JSON for aggregation:
```json
{"timestamp": "2024-01-15T10:30:00Z", "level": "info", "event": "pipeline_starting", "source": "s3_exports"}
```

---

## Troubleshooting

### Pipeline fails with "Unknown source"

```
ValueError: Unknown source: foo. Available: ['s3_exports', 'everflow', ...]
```

**Cause**: Source not registered in `src/signalroom/pipelines/runner.py`

**Fix**: Add source to SOURCES dict

### Pipeline fails with credentials error

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Cause**: Missing or invalid AWS credentials in `.env`

**Fix**: Verify `.env` has correct values:
```bash
grep AWS .env
```

### Worker not picking up tasks

**Symptoms**: Workflow starts but activity never runs

**Check**:
1. Worker is running: `docker compose ps worker`
2. Worker is connected to correct queue: Check worker logs for "Started worker"
3. Temporal is healthy: `docker compose ps temporal`

**Fix**:
```bash
make restart-worker
```

### "Postgres connection refused"

```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Cause**: Supabase credentials wrong or Supabase project paused

**Check**:
1. Verify `.env` has correct Supabase values
2. Check if Supabase project is active (not paused)
3. Try connecting manually:
```bash
psql "postgresql://user:pass@db.xxx.supabase.co:5432/postgres"
```

### Activity timeout

```
temporalio.exceptions.ActivityError: activity timed out
```

**Cause**: Pipeline took longer than 30 minutes

**Fix**: Either:
1. Process less data per run (filter resources)
2. Increase timeout in `workflows.py` (not recommended for huge increases)

### Workflow stuck in "Running"

**Check Temporal UI** for the workflow → see pending activities

**Common causes**:
1. No worker running for the task queue
2. Activity repeatedly failing and retrying
3. Activity blocked on external service

**Fix**: Check worker logs, restart worker, check external service health

---

## Restarting Services

### Restart worker (after code changes)

```bash
make restart-worker
```

### Restart everything

```bash
make down
make up
```

### Nuclear option (remove volumes)

**Warning**: This deletes Temporal's workflow history

```bash
docker compose down -v
make up
```

---

## Database Operations

### Connect to Supabase (your data)

```bash
# Get connection string from .env
source .env
psql "postgresql://${SUPABASE_DB_USER}:${SUPABASE_DB_PASSWORD}@${SUPABASE_DB_HOST}:${SUPABASE_DB_PORT}/${SUPABASE_DB_NAME}"
```

### Check loaded data

```sql
-- List tables created by dlt
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;

-- Check row counts
SELECT COUNT(*) FROM s3_exports.daily_exports;

-- Check dlt metadata
SELECT * FROM s3_exports._dlt_loads ORDER BY inserted_at DESC LIMIT 5;
```

### Connect to Temporal's Postgres (internal state)

```bash
psql "postgresql://temporal:temporal@localhost:5433/temporal"
```

---

## Scheduled Syncs

Schedules are configured in **Temporal Cloud** (namespace: signalroom-713.nzg5u).

### Active Schedules

| Schedule ID | When | What |
|-------------|------|------|
| `hourly-sync-everflow-redtrack` | Hourly 7am-11pm ET | Sync Everflow + Redtrack |
| `daily-sync-s3` | Daily 6am ET | Sync S3 exports |

**Note**: Report schedules are currently disabled. Only data sync schedules are active.

### Managing Schedules

```bash
# View schedules in Temporal Cloud UI
# https://cloud.temporal.io/namespaces/signalroom-713.nzg5u/schedules

# Create/update schedules
python scripts/setup_schedules.py

# Delete all schedules
python scripts/setup_schedules.py --delete

# List schedules via script
python -c "
import asyncio
from signalroom.temporal.config import get_temporal_client
async def main():
    client = await get_temporal_client()
    async for s in await client.list_schedules():
        print(f'{s.id}')
asyncio.run(main())
"
```

### Production Worker (Fly.io)

The worker runs on Fly.io and processes all scheduled workflows.

```bash
# Deploy to Fly.io
fly deploy

# View logs
fly logs

# Check worker status
fly status

# Check secrets
fly secrets list
```

**Fly.io Dashboard**: https://fly.io/apps/signalroom-worker
**Temporal Cloud UI**: https://cloud.temporal.io/namespaces/signalroom-713.nzg5u/workflows

---

## Alerts and Notifications

Notifications are sent via Slack on pipeline failures (if configured).

### Configure Slack

1. Create Slack app with `chat:write` scope
2. Add to `.env`:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C0123456789
```

### Test notifications

```python
# In Python shell
from signalroom.notifications import send_slack
import asyncio
asyncio.run(send_slack("Test message"))
```

---

## Reports

Reports are templated using Jinja2 (Slack/SMS) and MJML (responsive emails).

### Available Reports

| Report | Channels | Description |
|--------|----------|-------------|
| `daily_ccw` | slack, email, sms | Daily CCW performance summary |
| `test_sync` | slack | Simple test report (Everflow + Redtrack totals) |
| `alert` | slack, email, sms | Error/warning/info alerts |

### Running Reports Manually

```bash
# Run report and print output (no send)
python -c "
from signalroom.reports import run_report
print(run_report('daily_ccw', channel='slack'))
"

# Run report for specific date
python -c "
from signalroom.reports import run_report
print(run_report('daily_ccw', params={'date': '2025-12-18'}))
"

# Render an alert
python -c "
from signalroom.reports import render_alert
print(render_alert('Test Alert', 'This is a test', level='warning'))
"
```

### Template Locations

```
src/signalroom/reports/
├── templates/
│   ├── daily_ccw.slack.j2    # Slack mrkdwn
│   ├── daily_ccw.email.mjml  # Responsive HTML email
│   ├── daily_ccw.sms.j2      # Short SMS
│   ├── alert.slack.j2        # Alert for Slack
│   ├── alert.email.mjml      # Alert email
│   └── alert.sms.j2          # Alert SMS
└── queries/
    └── daily_ccw.sql         # SQL for report data
```

---

## Health Checks

### Manual health check script

```bash
#!/bin/bash
# Check all services are up

echo "Checking Temporal..."
curl -s http://localhost:8080 > /dev/null && echo "OK" || echo "FAIL"

echo "Checking worker..."
docker compose ps worker | grep -q "running" && echo "OK" || echo "FAIL"

echo "Checking Supabase connection..."
source .env
pg_isready -h $SUPABASE_DB_HOST -p $SUPABASE_DB_PORT && echo "OK" || echo "FAIL"
```

---

## Backup and Recovery

### Temporal state

Temporal's state (workflow history) is in `temporal-db-data` Docker volume.

```bash
# Backup
docker run --rm -v signalroom_temporal-db-data:/data -v $(pwd):/backup alpine tar czf /backup/temporal-backup.tar.gz /data

# Restore
docker run --rm -v signalroom_temporal-db-data:/data -v $(pwd):/backup alpine tar xzf /backup/temporal-backup.tar.gz -C /
```

### Your data (Supabase)

Supabase handles backups automatically. For manual backup, use pg_dump or Supabase dashboard.

---

## CLI Reference

### Pipeline Commands

```bash
# Run pipeline directly (bypasses Temporal)
python scripts/run_pipeline.py s3_exports
python scripts/run_pipeline.py everflow
python scripts/run_pipeline.py redtrack

# With specific date range
python scripts/run_pipeline.py everflow --start-date 2025-12-17 --end-date 2025-12-18

# Dry run
python scripts/run_pipeline.py everflow --dry-run
```

### Temporal Commands

```bash
# Test connection
python scripts/test_temporal_connection.py

# Trigger workflow (returns immediately)
python scripts/trigger_workflow.py everflow

# Trigger and wait for completion
python scripts/trigger_workflow.py everflow -w

# Trigger with notification
python scripts/trigger_workflow.py everflow -w --notify

# Setup/update schedules
python scripts/setup_schedules.py

# Delete all schedules
python scripts/setup_schedules.py --delete
```

### Database Commands

```bash
# Connect to Supabase
source .env
psql "postgresql://${SUPABASE_DB_USER}:${SUPABASE_DB_PASSWORD}@${SUPABASE_DB_HOST}:${SUPABASE_DB_PORT}/${SUPABASE_DB_NAME}"

# Quick row counts
psql "$DATABASE_URL" -c "
SELECT 'everflow.daily_stats' as table_name, COUNT(*) FROM everflow.daily_stats
UNION ALL
SELECT 'redtrack.daily_spend', COUNT(*) FROM redtrack.daily_spend
UNION ALL
SELECT 's3_exports.daily_exports', COUNT(*) FROM s3_exports.daily_exports;
"
```

### Report Commands

```bash
# Test report rendering (no send)
python -c "from signalroom.reports import run_report; print(run_report('daily_ccw'))"

# With specific date
python -c "from signalroom.reports import run_report; print(run_report('daily_ccw', params={'date': '2025-12-18'}))"

# Render alert
python -c "from signalroom.reports import render_alert; print(render_alert('Test', 'Message', level='warning'))"
```
