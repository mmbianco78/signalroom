# SignalRoom Constitution

Immutable principles governing all development in this project. AI agents and human developers must adhere to these articles when making technical decisions.

---

## Preamble

SignalRoom is a Marketing Data Platform. Its purpose is to ingest data from external marketing sources, normalize it, and load it into Supabase/Postgres for reporting and analysis. All development serves this mission.

---

## Article I: dlt-First Data Ingestion

**Every data source MUST be implemented as a dlt source.**

- Use `@dlt.source` and `@dlt.resource` decorators
- Let dlt handle schema inference, normalization, and loading
- Never write raw SQL INSERT statements for data ingestion
- Never build custom ETL logic that dlt already provides

**Rationale**: dlt provides schema evolution, state management, and destination abstraction. Reinventing these creates maintenance burden and inconsistency.

---

## Article II: Temporal Workflow Orchestration

**All scheduled and long-running operations MUST use Temporal workflows.**

- Pipelines are triggered via Temporal, not cron or launchd
- Activities contain the actual work; workflows orchestrate
- Use `UnsandboxedWorkflowRunner` for dlt compatibility
- Never call external APIs directly from workflows—use activities

**Rationale**: Temporal provides durability, retries, visibility, and scheduling. Direct execution loses these guarantees.

---

## Article III: Client Tagging Mandate

**Every row of data MUST include `_client_id`.**

- All dlt resources must yield records with `_client_id` field
- All Supabase tables must have `_client_id` column
- Queries filtering by client must use this column
- Never assume single-client context in data logic

**Rationale**: Multi-client support without multi-tenancy. Data isolation through tagging, not schema separation.

---

## Article IV: Configuration via Environment

**All configuration MUST come from environment variables.**

- Secrets in `.env` (gitignored) or Fly.io secrets
- Non-sensitive config in `.env` or `.dlt/config.toml`
- Never hardcode API keys, URLs, or credentials
- Never commit secrets to the repository

**Rationale**: Enables environment parity (local, staging, production) and secure secret management.

---

## Article V: Skills as Workflow Guardrails

**Complex workflows MUST have corresponding skills.**

- Skills live in `.claude/skills/{name}/SKILL.md`
- Skills encode the workflow, not just commands
- Skills may restrict tool access for safety (e.g., read-only diagnostics)
- Update skills when workflows change

**Rationale**: Skills prevent AI agents from taking incorrect paths and encode institutional knowledge.

---

## Article VI: Documentation Separation

**Documentation MUST maintain clear separation of concerns.**

| Document | Contains | Does NOT Contain |
|----------|----------|------------------|
| `API_REFERENCE.md` | External API docs, auth, examples | Business logic |
| `DATA_MODEL.md` | Entity relationships, business rules | API documentation |
| `DATA_ORGANIZATION.md` | File paths, naming conventions | Data semantics |
| `SOURCES.md` | Implementation details per source | API reference |
| `OPERATIONS.md` | Runbooks, recovery procedures | Development guides |

**Rationale**: Prevents information duplication and staleness. Single source of truth per concept.

---

## Article VII: Test Before Deploy

**No deployment without local verification.**

1. Run the pipeline locally: `python scripts/run_pipeline.py {source}`
2. Verify data in Supabase
3. Only then deploy: `fly deploy`

**Rationale**: Production stability. Catching errors before they reach production.

---

## Article VIII: Merge Over Replace

**Prefer merge write disposition for mutable entities.**

| Data Type | Disposition | Rationale |
|-----------|-------------|-----------|
| Immutable events (clicks, logs) | `append` | Events don't change |
| Mutable entities (contacts, stats) | `merge` | Updates overwrite |
| Reference data (config, flags) | `replace` | Full refresh |

**Rationale**: Merge allows re-running pipelines for date ranges without duplicates. Append requires deduplication logic.

---

## Article IX: Observability Over Opacity

**All operations MUST be observable.**

- Structured logging with `structlog`
- Temporal UI for workflow visibility
- dlt load info returned from pipelines
- Slack notifications for failures

**Rationale**: Debugging requires visibility. Silent failures are unacceptable.

---

## Article X: Simplicity Over Abstraction

**Prefer direct implementation over premature abstraction.**

- Don't wrap frameworks unnecessarily
- Don't create helpers for one-time operations
- Don't add configurability before it's needed
- Three similar lines are better than a clever abstraction

**Rationale**: Abstractions have maintenance cost. Add them when patterns prove stable.

---

## Article XI: Primary Keys Are Sacred

**Every dlt resource MUST define explicit primary keys.**

| Source | Primary Key | Write Mode |
|--------|-------------|------------|
| `s3_exports` | `_file_name, _row_id` | append |
| `everflow` | `date, affiliate_id, advertiser_id` | merge |
| `redtrack` | `date, source_id` | merge |

**Rationale**: Primary keys enable merge disposition and prevent duplicates. Missing or wrong keys cause data corruption.

---

## Article XII: Live Docs Front and Center

**External API documentation URLs MUST be prominently documented.**

- Live URLs at top of `API_REFERENCE.md`
- Labeled clearly for agentic search: "LIVE DOCS:"
- Verified working before commit
- Updated when APIs change

**Rationale**: AI agents need quick access to authoritative API documentation. Stale or hidden URLs waste time.

---

## Enforcement

These articles are referenced by:
- AI agents via CLAUDE.md and skills
- Code review checklist
- Pre-deployment verification

Violations require documented justification in commit messages or PR descriptions.

---

## Amendments

To propose changes to this constitution:
1. Open a discussion with rationale
2. Demonstrate the limitation of current article
3. Propose specific amendment language
4. Update all affected documentation

The constitution evolves through deliberate, documented changes—not ad-hoc exceptions.
