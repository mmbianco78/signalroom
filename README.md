# SignalRoom

Marketing Data Platform for Critical Ads. Ingests data from marketing sources into Supabase/Postgres using dlt pipelines orchestrated by Temporal.

## Quick Start

```bash
# Prerequisites: uv (https://docs.astral.sh/uv/)

# 1. Install
uv venv && uv pip install -e ".[dev]"
source .venv/bin/activate

# 2. Configure
cp .env.example .env
# Edit .env with your credentials

# 3. Run (Docker required)
make dev
```

Temporal UI: http://localhost:8080

---

## Architecture

```
Temporal Cluster ──> Worker ──> dlt Pipelines ──> Supabase (Postgres)
     │                  │
     │                  └── API Worker (API calls, file processing, reports)
     │
     └── Schedules, retries, visibility, durability
```

| Layer | Path | Purpose |
|-------|------|---------|
| Sources | `src/signalroom/sources/` | dlt sources (one per platform) |
| Pipelines | `src/signalroom/pipelines/` | Pipeline runner, source registry |
| Temporal | `src/signalroom/temporal/` | Workflows and Activities |
| Workers | `src/signalroom/workers/` | Worker entry points |
| Notifications | `src/signalroom/notifications/` | Slack, Email, SMS |
| Common | `src/signalroom/common/` | Config, logging, clients |

---

## Sources

| Source | Description | Write Mode | Status |
|--------|-------------|------------|--------|
| `s3_exports` | CSV files from S3 (Sticky.io) | append | ✅ Active (650k rows) |
| `everflow` | Affiliate conversions/revenue | merge | ✅ Active |
| `redtrack` | Ad spend tracking | merge | ✅ Active |
| `posthog` | PostHog analytics | append | Stubbed |
| `mautic` | Mautic contacts/campaigns | merge | Stubbed |
| `google_sheets` | Google Sheets data | replace | Stubbed |

See `docs/SOURCES.md` for detailed schema and usage.

---

## Configuration

All configuration via environment variables. See `.env.example` for full list.

### Required

| Variable | Description |
|----------|-------------|
| `SUPABASE_DB_HOST` | Postgres host (e.g., `db.xxx.supabase.co`) |
| `SUPABASE_DB_PASSWORD` | Database password |

### S3 (for s3_exports source)

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region (default: `us-east-1`) |
| `S3_BUCKET_NAME` | Bucket name |
| `S3_PREFIXES` | Comma-separated prefixes to scan |

### Temporal

| Variable | Description | Default |
|----------|-------------|---------|
| `TEMPORAL_ADDRESS` | Temporal server address | `localhost:7233` |
| `TEMPORAL_NAMESPACE` | Namespace | `default` |
| `TEMPORAL_TASK_QUEUE` | Task queue name | `api-tasks` |

### Everflow

| Variable | Description |
|----------|-------------|
| `EVERFLOW_API_KEY` | Everflow API key |
| `EVERFLOW_BASE_URL` | Base URL (default: `https://api.eflow.team`) |

### Redtrack

| Variable | Description |
|----------|-------------|
| `REDTRACK_API_KEY` | Redtrack API key |
| `REDTRACK_BASE_URL` | Base URL (default: `https://api.redtrack.io`) |

### Notifications (optional)

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN` | Slack bot token |
| `SLACK_CHANNEL_ID` | Channel for alerts |
| `RESEND_API_KEY` | Resend email API key |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |

---

## Commands

### Development

| Command | Description |
|---------|-------------|
| `make dev` | Start Temporal + worker (foreground) |
| `make up` | Start all services (background) |
| `make down` | Stop all services |
| `make logs` | Tail all logs |
| `make logs-worker` | Tail worker logs |
| `make restart-worker` | Restart worker after code changes |

### Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff linter |
| `make format` | Format with ruff |
| `make typecheck` | Run pyright |
| `make test` | Run pytest |
| `make ci` | Run all checks |

### Pipelines

```bash
# Run directly (bypasses Temporal, for testing)
python scripts/run_pipeline.py s3_exports

# Trigger via Temporal workflow
python scripts/trigger_workflow.py s3_exports -w  # -w waits for completion
```

---

## Adding a New Source

1. Create source module:
   ```
   src/signalroom/sources/{source_name}/__init__.py
   ```

2. Define dlt source:
   ```python
   import dlt
   from signalroom.common import settings

   @dlt.source(name="my_source")
   def my_source():
       @dlt.resource(write_disposition="append", primary_key="id")
       def my_resource():
           yield from fetch_data()
       return [my_resource]
   ```

3. Register in `src/signalroom/pipelines/runner.py`:
   ```python
   SOURCES = {
       ...
       "my_source": "signalroom.sources.my_source:my_source",
   }
   ```

4. Add credentials to `.env` and `src/signalroom/common/config.py`

---

## Clients

Data is tagged with `client_id` for grouping. No multi-tenancy.

| Client ID | Name |
|-----------|------|
| `713` | 713 |
| `cti` | ClayTargetInstruction |

---

## Docker

```bash
# Local dev
docker compose up --build

# Production build
docker build --target prod -t signalroom:prod .
```

## Production (Fly.io)

Worker runs on Fly.io, connected to Temporal Cloud.

```bash
# Deploy
fly deploy

# View logs
fly logs

# Check status
fly status
```

---

## Project Structure

```
signalroom/
├── src/signalroom/
│   ├── sources/           # dlt sources (one per platform)
│   ├── pipelines/         # Pipeline runner
│   ├── temporal/          # Workflows and Activities
│   ├── workers/           # Worker entry points
│   ├── reports/           # Jinja2/MJML templated reports
│   ├── notifications/     # Slack, Email, SMS
│   └── common/            # Config, logging
├── scripts/               # CLI tools
├── tests/
├── docs/                  # Documentation (see below)
├── .claude/skills/        # Claude Code skill definitions
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Documentation

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | AI/developer guidance, commands, patterns |
| `docs/API_REFERENCE.md` | External API endpoints, auth, examples |
| `docs/DATA_MODEL.md` | Entity relationships, business logic, schemas |
| `docs/DATA_ORGANIZATION.md` | File conventions, client data patterns |
| `docs/SOURCES.md` | dlt source implementation details |
| `docs/ROADMAP.md` | Project phases and current status |
| `docs/OPERATIONS.md` | Runbooks and operational procedures |
