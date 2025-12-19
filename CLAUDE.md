# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**Activities** (retryable work):
- `run_pipeline_activity` - runs dlt pipeline
- `send_notification_activity` - sends Slack/email/SMS

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
