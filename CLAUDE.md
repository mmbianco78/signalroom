# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ DEPLOYMENT DISCIPLINE

**STOP. Before ANY deployment or config change:**

1. **LOCAL FIRST** - Test locally before deploying
2. **ONE CHANGE** - Make one fix, verify, then proceed
3. **UNDERSTAND FIRST** - Don't conflate unrelated errors

```bash
# Pre-deploy checklist
python scripts/run_pipeline.py everflow  # Must pass before deploy
fly deploy                                # Then deploy
```

**IMPORTANT:** See `.claude/skills/deploy/` for full checklist, known working config, and recovery procedures.

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
Temporal Cloud ──► Worker ──► dlt Pipelines ──► Supabase (Postgres)
      │              │
      │              └── Activities: pipelines, reports, notifications
      │
      └── Schedules, retries, visibility, durability
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

1. Check `docs/API_REFERENCE.md` for API docs, auth, and request/response examples
2. Create `src/signalroom/sources/{source_name}/__init__.py`
3. Define `@dlt.source` with `@dlt.resource` functions
4. Register in `src/signalroom/pipelines/runner.py` SOURCES dict
5. Add credentials to `.env` and `src/signalroom/common/config.py`
6. Update `docs/API_REFERENCE.md` with any new endpoints used

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
│   ├── API_REFERENCE.md      # External API docs & examples (LIVE URLS)
│   ├── DATA_MODEL.md         # Entity relationships, business logic, schemas
│   ├── DATA_ORGANIZATION.md  # File conventions, client data patterns
│   ├── SOURCES.md            # dlt source implementation details
│   ├── ROADMAP.md            # Project phases and status
│   ├── OPERATIONS.md         # Runbooks and operational procedures
│   ├── templates/            # Documentation templates
│   └── archive/              # Historical notes and postmortems
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

## Docker & Deployment

```bash
# Local dev
docker compose up --build

# Production (Fly.io)
fly deploy              # Deploy to Fly.io
fly logs                # View logs
fly status              # Check status
```

## Skills Reference

Detailed workflows are in `.claude/skills/`:

| Skill | Use For |
|-------|---------|
| `deploy` | Pre-deployment checklist, Fly.io operations |
| `pipeline` | Running dlt pipelines, Temporal triggers |
| `dlt` | Source patterns, incremental loading, debugging |
| `temporal` | Workflows, activities, schedules |
| `supabase` | Database queries, connection config |
| `reports` | Jinja2/MJML templating |
| `troubleshoot` | Diagnostics (read-only) |
| `git` | Commit standards, PR workflow |
| `root-cause-tracing` | Systematic debugging |
| `kaizen` | Continuous improvement |
