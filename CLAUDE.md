# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ DEPLOYMENT DISCIPLINE (READ THIS FIRST)

**STOP. Before making ANY infrastructure or config changes, follow this protocol.**

### The Golden Rules

1. **LOCAL FIRST, ALWAYS** - Never deploy until local tests pass
2. **ONE CHANGE AT A TIME** - Make one fix, test it, verify it works, then proceed
3. **UNDERSTAND BEFORE FIXING** - Don't conflate unrelated errors. A Temporal sandbox error is NOT an env file loading issue.
4. **NOTIFICATIONS ARE PRODUCTION** - Failed deployments spam Slack. This is unacceptable.

### Before ANY Fly.io Deployment

```bash
# Step 1: Verify database connection locally
python -c "from signalroom.common import settings; print(settings.postgres_connection_string[:50])"

# Step 2: Test a simple pipeline locally
python scripts/run_pipeline.py everflow

# Step 3: Only if above passes, proceed to deployment
```

### When Troubleshooting Errors

1. **STOP** - Don't make rapid changes
2. **READ** - Understand the actual error message
3. **ISOLATE** - Is this a code issue, config issue, or secrets issue?
4. **TEST LOCALLY** - Reproduce and fix locally first
5. **DEPLOY ONCE** - With confidence, not hope

### Fly.io Secrets with Special Characters

Passwords with `$`, `!`, `@` characters get mangled by shell interpolation.

**WRONG:** `fly secrets set PASSWORD='$foo@bar!'` ($ gets interpreted)

**RIGHT:** Use the Fly.io dashboard, or:
```bash
# Write to file, set from file
echo -n 'actual-password' > /tmp/pw.txt
fly secrets set PASSWORD=- < /tmp/pw.txt
rm /tmp/pw.txt
```

### Known Working Configuration

**Database (Supabase Pooler):**
- Host: `aws-1-us-east-1.pooler.supabase.com`
- Port: `6543`
- User: `postgres.foieoinshqlescyocbld` (NOT just `postgres`)
- Database: `postgres`

**Settings config MUST have:**
```python
model_config = SettingsConfigDict(
    env_file=".env",  # DO NOT REMOVE THIS
    env_file_encoding="utf-8",
    extra="ignore",
)
```

**Temporal worker MUST use:**
```python
workflow_runner=UnsandboxedWorkflowRunner()  # Avoids sandbox issues with structlog/rich
```

### Recovery Checklist (If Things Break)

1. [ ] Stop Fly.io worker: `fly machine stop <id> --app signalroom-worker`
2. [ ] Verify local .env has correct credentials
3. [ ] Test locally: `python scripts/run_pipeline.py everflow`
4. [ ] Fix Fly.io secrets via dashboard (not CLI for special char passwords)
5. [ ] Deploy and verify logs before enabling schedules

---

## Project Overview

**SignalRoom** is a Marketing Data Platform built by Critical Ads. It handles data ingestion, normalization, and loading into Supabase (Postgres) from various marketing data sources.

**Core Technologies:**
- **dlt** (data load tool): ETL/ELT library for data ingestion and schema handling
- **Temporal.io**: Durable workflow orchestration, retries, and scheduling
- **Supabase/Postgres**: Data destination

**Clients:** 713, CTI (ClayTargetInstruction) - use `client_id` tagging for grouping, no multi-tenancy.

## Build & Development Commands

```bash
# Setup (requires uv: https://docs.astral.sh/uv/)
make install-dev          # Install with dev dependencies

# Development
make dev                  # Start Temporal + worker with docker-compose (foreground)
make up                   # Start all services in background
make down                 # Stop all services
make logs                 # Tail all logs
make logs-worker          # Tail worker logs only
make restart-worker       # Restart worker after code changes

# Code Quality
make lint                 # Run ruff linter
make format               # Format code with ruff
make typecheck            # Run pyright
make test                 # Run pytest
make ci                   # Run all checks (lint + typecheck + test)

# Running Pipelines
python scripts/run_pipeline.py s3_exports          # Run a pipeline directly
python scripts/trigger_workflow.py s3_exports -w   # Trigger via Temporal (--wait)

# Reports
python -c "from signalroom.reports import run_report; print(run_report('daily_ccw'))"

# Temporal Cloud
python scripts/test_temporal_connection.py         # Verify connection
python scripts/setup_schedules.py                  # Create/update schedules
python scripts/setup_schedules.py --delete         # Delete all schedules

# Temporal UI
make temporal-ui          # Open http://localhost:8080
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Temporal Cluster                    │
│   (scheduling, retries, durability, visibility)  │
└─────────────────────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
    ┌───────────────┐      ┌───────────────┐
    │  API Worker   │      │Browser Worker │
    │ (fast tasks)  │      │ (slow tasks)  │
    └───────┬───────┘      └───────┬───────┘
            │                      │
            └──────────┬───────────┘
                       ▼
            ┌─────────────────────┐
            │    dlt Pipelines    │
            │ (extract, normalize,│
            │  schema, load)      │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │ Supabase (Postgres) │
            └─────────────────────┘
```

### Key Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Sources** | `src/signalroom/sources/` | dlt sources - one per platform (S3, Everflow, PostHog, etc.) |
| **Pipelines** | `src/signalroom/pipelines/` | dlt pipeline runner, source registry |
| **Temporal** | `src/signalroom/temporal/` | Workflows (orchestration) and Activities (units of work) |
| **Workers** | `src/signalroom/workers/` | Temporal worker entry points |
| **Reports** | `src/signalroom/reports/` | Jinja2/MJML templated reports (Slack, Email, SMS) |
| **Notifications** | `src/signalroom/notifications/` | Slack, Email (Resend), SMS (Twilio) |
| **Common** | `src/signalroom/common/` | Config, logging, client definitions |

### Data Flow

1. **Temporal Workflow** started (scheduled or manual)
2. **Activity** calls `run_pipeline()` with source name
3. **dlt Pipeline** extracts from source, normalizes, loads to Postgres
4. **Activity** returns result (row counts, load ID)
5. **Workflow** sends notifications on success/failure

### Adding a New Source

1. Create `src/signalroom/sources/{source_name}/__init__.py`
2. Define `@dlt.source` with `@dlt.resource` functions
3. Register in `src/signalroom/pipelines/runner.py` SOURCES dict
4. Add credentials to `.env` and `src/signalroom/common/config.py`

## Project Structure

```
signalroom/
├── .dlt/
│   ├── config.toml        # Pipeline config (non-sensitive, committed)
│   └── secrets.toml       # API keys (gitignored)
├── data/
│   └── clients/           # Client-specific reference data
│       ├── 713/
│       │   └── mappings/
│       │       └── internal-affiliates.csv
│       └── cti/           # Future clients
├── src/signalroom/
│   ├── sources/           # dlt sources (one per platform)
│   │   ├── s3_exports/    # CSV files from S3
│   │   ├── everflow/      # Everflow reporting API
│   │   ├── redtrack/      # Redtrack reporting API
│   │   ├── posthog/       # PostHog analytics
│   │   ├── mautic/        # Mautic (self-hosted)
│   │   └── google_sheets/ # Google Sheets
│   ├── pipelines/         # dlt pipeline runner
│   ├── temporal/          # Workflows and Activities
│   ├── workers/           # Worker entry points
│   ├── reports/           # Jinja2/MJML templated reports
│   │   ├── templates/     # .j2 and .mjml templates
│   │   └── queries/       # SQL for report data
│   ├── notifications/     # Slack, Email, SMS
│   └── common/            # Config, logging, clients
├── scripts/               # CLI tools for manual runs
├── tests/
├── docs/
│   ├── templates/         # Documentation templates
│   └── DATA_ORGANIZATION.md  # Client data patterns (READ THIS)
├── docker-compose.yml     # Temporal + Postgres + Worker
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Client Data Organization (IMPORTANT)

**Full documentation:** `docs/DATA_ORGANIZATION.md`

### Critical Rules

1. **Client-specific data path**: `data/clients/{client_id}/{category}/{filename}`
   - Example: `data/clients/713/mappings/internal-affiliates.csv`
   - NEVER: `data/713-file.csv` or `src/signalroom/data/`

2. **All Supabase data tagged**: Every table must include `_client_id` column
   ```python
   yield {"data": value, "_client_id": client_id}
   ```

3. **Reference data flow**: CSV in repo → Load script → Supabase table
   - CSV is source of truth (version controlled)
   - Table has `client_id` column for filtering

4. **dlt config hierarchy**: Use `.dlt/config.toml` for settings, not hardcoded paths
   ```toml
   [sources.affiliate_mapping.clients.713]
   csv_path = "data/clients/713/mappings/internal-affiliates.csv"
   ```

### Current Clients

| ID | Name | Status |
|----|------|--------|
| `713` | 713 | Active |
| `cti` | ClayTargetInstruction | Planned |

### When Adding New Client Data

1. Create: `data/clients/{client_id}/{category}/`
2. Add files following existing naming conventions
3. Ensure Supabase tables have `client_id` column
4. Update `docs/DATA_ORGANIZATION.md` if new patterns

## Configuration

All config via environment variables. See `.env.example` for full list.

Key settings in `src/signalroom/common/config.py`:
- `settings.postgres_connection_string` - dlt destination
- `settings.temporal_address` - Temporal server
- Source API keys loaded from env

## Temporal Patterns

**Workflows** (pure orchestration, no I/O):
- `SyncSourceWorkflow` - sync one source, optionally notify
- `ScheduledSyncWorkflow` - sync multiple sources sequentially
- `RunReportWorkflow` - run and send a templated report

**Activities** (retryable work):
- `run_pipeline_activity` - runs dlt pipeline
- `run_report_activity` - renders and sends a report
- `send_notification_activity` - sends Slack/email/SMS

**Active Schedules** (Temporal Cloud - signalroom-713.nzg5u):
- `hourly-sync-everflow-redtrack` - Hourly 7am-11pm ET
- `daily-sync-s3` - Daily 6am ET
- `daily-report-ccw` - Daily 7am ET

**Retry Policy** (defined in `temporal/config.py`):
- 5 attempts, exponential backoff (1s → 5min)
- Non-retryable: ValueError, KeyError

## dlt Patterns

**Write dispositions:**
- `append` - immutable events (conversions, clicks)
- `merge` - mutable entities with primary key (campaigns, contacts)
- `replace` - full refresh (feature flags)

**Incremental loading:**
```python
@dlt.resource(write_disposition="append", primary_key="id")
def events(after: dlt.sources.incremental[str] = dlt.sources.incremental("timestamp")):
    # Only fetches records after last loaded timestamp
    yield from fetch_events(since=after.last_value)
```

## Testing

```bash
make test                           # Run all tests
make test-quick                     # Stop on first failure
make test-file FILE=tests/test_x.py # Run single file
```

Use DuckDB destination for local testing (no Postgres needed):
```python
pipeline = dlt.pipeline(destination="duckdb", dataset_name="test")
```

## Docker

```bash
# Local dev (same as production)
docker compose up --build

# Build specific targets
docker build --target dev -t signalroom:dev .
docker build --target prod -t signalroom:prod .
docker build --target prod-browser -t signalroom:browser .
```
