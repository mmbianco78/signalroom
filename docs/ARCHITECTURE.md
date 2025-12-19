# Architecture

## Overview

SignalRoom is a Marketing Data Platform that ingests data from various sources into Supabase (Postgres). It uses **Temporal.io** for durable workflow orchestration and **dlt** for ELT operations.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRIGGER LAYER                                │
│  Temporal Schedules (cron) │ Manual Scripts │ External Webhooks     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TEMPORAL CLUSTER                                │
│  • Workflow scheduling and execution                                 │
│  • Retry policies with exponential backoff                          │
│  • State persistence (survives restarts)                            │
│  • Visibility (query running/completed workflows)                   │
│  • Task queues for worker routing                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────┐
                        │    API Worker     │
                        │  (api-tasks queue)│
                        ├───────────────────┤
                        │ • API calls       │
                        │ • S3 file reads   │
                        │ • CSV parsing     │
                        │ • Report rendering│
                        └─────────┬─────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DLT PIPELINE                                 │
│  • Extract: Pull from source (API, S3, browser)                     │
│  • Normalize: Flatten nested JSON, infer schema                     │
│  • Load: Insert/merge into Postgres with schema evolution           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SUPABASE (POSTGRES)                               │
│  • Schema per source (s3_exports, everflow, etc.)                   │
│  • Automatic table creation from dlt                                │
│  • _dlt_* metadata tables for lineage                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Temporal Workflows (`src/signalroom/temporal/workflows.py`)

**SyncSourceWorkflow**: Syncs a single data source.
```
Input: source_name, resources (optional), notify flags
Steps: 1. Run pipeline activity → 2. Send notification (if configured)
Output: PipelineResult with row counts
```

**ScheduledSyncWorkflow**: Syncs multiple sources sequentially.
```
Input: list of source names
Steps: For each source → run pipeline activity
Output: Dict of source → result
```

**RunReportWorkflow**: Runs and sends a templated report.
```
Input: report_name, channel, send flag
Steps: 1. Run report activity → 2. Notify on failure
Output: ReportResult with content length
```

### 2. Temporal Activities (`src/signalroom/temporal/activities.py`)

**run_pipeline_activity**: Executes a dlt pipeline. This is where actual data movement happens.

**run_report_activity**: Renders a report template and optionally sends it.

**send_notification_activity**: Sends alerts via Slack, Email, or SMS.

### 3. dlt Sources (`src/signalroom/sources/`)

Each source is a dlt `@source` that yields data:

| Source | Type | Implementation |
|--------|------|----------------|
| s3_exports | File | Reads CSVs from S3 bucket |
| everflow | API | Reporting API (stubbed) |
| redtrack | API | Reporting API (stubbed) |
| posthog | API | Events, feature flags, experiments |
| mautic | API | Contacts, campaigns, emails |
| google_sheets | API | Spreadsheet data (stubbed) |

### 4. Pipeline Runner (`src/signalroom/pipelines/runner.py`)

Registry pattern connecting source names to implementations:
```python
SOURCES = {
    "s3_exports": "signalroom.sources.s3_exports:s3_exports",
    # ...
}
```

### 5. Workers (`src/signalroom/workers/main.py`)

Long-running processes that poll Temporal for work:
- Register workflows and activities
- Connect to Temporal cluster
- Handle graceful shutdown

## Data Flow Example

```
1. Temporal schedule triggers ScheduledSyncWorkflow
   └── workflow_id: "daily-sync-2024-01-15"

2. Workflow calls run_pipeline_activity("s3_exports")
   └── activity_id: "run_pipeline_s3_exports_1"

3. Activity calls run_pipeline() from runner.py
   └── Creates dlt.pipeline(destination="postgres")

4. dlt source s3_exports() yields rows
   └── Reads from s3://sticky-713-data-repo/orders-create/*.csv

5. dlt normalizes and loads to Postgres
   └── Table: s3_exports.daily_exports
   └── Columns inferred from CSV headers

6. Activity returns PipelineResult
   └── {load_id: "1705312345", row_counts: {"daily_exports": 1523}}

7. Workflow sends Slack notification (if enabled)
   └── "Pipeline completed: s3_exports - 1523 rows"
```

## Retry & Durability

### Temporal Retry Policy
```python
RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(minutes=5),
    backoff_coefficient=2.0,
    maximum_attempts=5,
    non_retryable_error_types=["ValueError", "KeyError"],
)
```

### Failure Modes

| Failure | Handled By | Behavior |
|---------|------------|----------|
| Network timeout | Temporal retry | Exponential backoff, up to 5 attempts |
| API rate limit | Temporal retry | Backoff allows rate limit to reset |
| Invalid credentials | Non-retryable | Fails immediately (ValueError) |
| Postgres down | Temporal retry | Retries until Postgres recovers |
| Worker crash | Temporal | Activity times out, rescheduled to another worker |
| Partial load | **NOT HANDLED** | See ROADMAP.md - needs checkpointing |

## Directory Structure

```
src/signalroom/
├── common/           # Shared utilities
│   ├── config.py     # Environment-based settings (pydantic)
│   ├── logging.py    # Structured logging (structlog)
│   └── clients.py    # Client registry (713, CTI)
├── sources/          # dlt sources (one per data platform)
│   ├── s3_exports/   # CSV files from S3
│   ├── everflow/     # Affiliate tracking
│   ├── posthog/      # Product analytics
│   └── ...
├── pipelines/        # dlt pipeline orchestration
│   └── runner.py     # Source registry, run_pipeline()
├── temporal/         # Temporal workflows & activities
│   ├── workflows.py  # Orchestration logic
│   ├── activities.py # Units of work
│   └── config.py     # Retry policies, client setup
├── workers/          # Worker entry points
│   └── main.py       # Temporal worker process
├── reports/          # Templated reports
│   ├── registry.py   # Report definitions
│   ├── renderer.py   # Jinja2 + MJML rendering
│   ├── runner.py     # Execute reports
│   ├── templates/    # .j2 and .mjml templates
│   └── queries/      # SQL for report data
└── notifications/    # Alert channels
    └── channels.py   # Slack, Email, SMS
```

## Configuration

All configuration via environment variables. See `.env.example`.

Key settings:
- `TEMPORAL_ADDRESS`: Temporal server (default: localhost:7233)
- `SUPABASE_DB_*`: Postgres connection for dlt destination
- `AWS_*`: S3 credentials for s3_exports source
- `SLACK_*`: Notification channel

## Task Queues

| Queue | Worker | Use Case |
|-------|--------|----------|
| api-tasks | worker | API calls, file processing, reports |

## Deployment Topology

### Local Development (Docker Compose)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Compose                               │
├─────────────────────────────────────────────────────────────────┤
│  temporal        │ Temporal server (scheduling, state)          │
│  temporal-ui     │ Web UI for visibility (port 8080)            │
│  temporal-db     │ Postgres for Temporal's internal state       │
│  worker          │ API worker (polls api-tasks queue)           │
└─────────────────────────────────────────────────────────────────┘
```

### Production (Fly.io + Temporal Cloud)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Fly.io                                       │
├─────────────────────────────────────────────────────────────────┤
│  signalroom-worker  │ API worker container (247MB)              │
│  Region: iad        │ US East (closest to Supabase/Temporal)    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  External Services                               │
├─────────────────────────────────────────────────────────────────┤
│  Temporal Cloud  │ signalroom-713.nzg5u (ap-northeast-1)        │
│  Supabase        │ foieoinshqlescyocbld (us-east-1 pooler)      │
│  S3              │ sticky-713-data-repo                         │
│  Slack           │ #reporting channel                           │
└─────────────────────────────────────────────────────────────────┘
```
