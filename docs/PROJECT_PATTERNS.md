# Project Patterns

How to set up a new project following the SignalRoom pattern. This is the meta-document that explains the philosophy and structure.

---

## Philosophy

1. **AI-first documentation** - Structure docs for both humans AND agentic AI tools
2. **Single source of truth** - One authoritative location per concept
3. **Separation of concerns** - External APIs vs internal data models vs operational guides
4. **Skills as guardrails** - Encode workflows, not just commands
5. **Client-tagged data** - All data includes `_client_id` for multi-client without multi-tenancy

---

## Documentation Structure

```
project/
├── CLAUDE.md              # AI/developer entry point (REQUIRED)
├── README.md              # Human entry point, quick start
└── docs/
    ├── API_REFERENCE.md   # External API docs, live URLs front and center
    ├── DATA_MODEL.md      # Entity relationships, business logic, schemas
    ├── DATA_ORGANIZATION.md  # File conventions, where things go
    ├── SOURCES.md         # Data source implementation details
    ├── OPERATIONS.md      # Runbooks, incident response
    ├── ROADMAP.md         # Project phases, status tracking
    ├── templates/         # Reusable doc templates
    └── archive/           # Historical notes, postmortems
```

### What Goes Where

| Document | Contains | Does NOT Contain |
|----------|----------|------------------|
| `CLAUDE.md` | Commands, project structure, quick reference | Detailed implementation |
| `README.md` | Quick start, architecture overview | AI-specific instructions |
| `API_REFERENCE.md` | Live doc URLs, auth, request/response examples | Business logic |
| `DATA_MODEL.md` | Entity relationships, views, business rules | API endpoints |
| `DATA_ORGANIZATION.md` | File paths, naming conventions | Data meanings |
| `SOURCES.md` | Implementation details per source | API documentation |
| `OPERATIONS.md` | Runbooks, recovery procedures | Development guides |

---

## CLAUDE.md Pattern

The AI entry point. Must include:

```markdown
# CLAUDE.md

## Project Overview
One paragraph: what it does, core technologies, clients.

## Build & Development Commands
Table of common commands with examples.

## Architecture
ASCII diagram + layer table (Sources, Pipelines, Workers, etc.)

## Project Structure
Directory tree with annotations.

## Configuration
Environment variables, where settings live.

## Skills Reference
Table pointing to .claude/skills/*/SKILL.md files.
```

### Key Principles

1. **Commands up top** - Most frequently needed
2. **Structure visible** - Directory tree with purpose annotations
3. **Cross-references** - Point to detailed docs, don't duplicate
4. **Deployment discipline** - Warnings for destructive operations

---

## Skills System

Skills are workflow guides in `.claude/skills/{skill-name}/SKILL.md`.

### Skill File Format

```markdown
---
name: skill-name
description: One sentence. Use when [trigger conditions].
allowed-tools: Read, Grep, Glob, Bash, Edit  # Restrict tools if needed
---

# Skill Title

## Quick Reference
Most common commands/patterns.

## Detailed Workflow
Step-by-step with code blocks.

## Common Issues
Error patterns and fixes.

## References
Links to related docs.
```

### Skill Categories

| Type | Purpose | Example |
|------|---------|---------|
| **Workflow** | Multi-step processes | `deploy`, `pipeline`, `git` |
| **Technology** | Tool-specific guidance | `dlt`, `temporal`, `supabase` |
| **Diagnostic** | Read-only investigation | `troubleshoot`, `root-cause-tracing` |
| **Process** | Methodologies | `kaizen` (continuous improvement) |

### When to Create a Skill

Create a skill when:
- A workflow has 3+ steps that must be done in order
- Common mistakes should be prevented
- Tool restrictions are needed (e.g., read-only diagnostics)
- External tool usage patterns need encoding

### Skill Naming

- Use lowercase, hyphenated names: `root-cause-tracing`
- Name describes the activity: `deploy`, `troubleshoot`, `pipeline`
- NOT the technology (prefer `pipeline` over `dlt-runner`)

---

## API Reference Pattern

External API documentation lives in `docs/API_REFERENCE.md`.

### Structure

```markdown
# API Reference

## Quick Links (Live Documentation)

| Service | Live Docs URL | Status |
|---------|---------------|--------|
| **ServiceName** | https://docs.service.com/ | Active |

---

## ServiceName

### LIVE DOCS: https://docs.service.com/

**API Base URL**: `https://api.service.com`
**Authentication**: Header `X-API-Key: {key}`

### Endpoints Used

#### Endpoint Name
- **Method**: POST
- **Path**: `/v1/endpoint`
- **Purpose**: What it does

**Request:**
```json
{...}
```

**Response:**
```json
{...}
```
```

### Key Principles

1. **Live URL front and center** - Labeled clearly, first thing visible
2. **Authentication details** - How to auth, header names
3. **Actual request/response** - Real examples, not just schema
4. **Status per service** - Active, Planned, Deprecated

---

## Data Model Pattern

Entity relationships and business logic in `docs/DATA_MODEL.md`.

### Structure

```markdown
# Data Model

## Entity Relationships
ASCII diagram showing how tables connect.

## Core Tables
Schema for each table with column descriptions.

## Business Logic
Rules: internal vs external, cost calculation, etc.

## Views
SQL view definitions with explanations.

## Query Examples
Common queries with explanations.
```

### Key Principles

1. **Diagram first** - Visual before details
2. **Primary keys explicit** - Critical for merge operations
3. **Business rules codified** - Not buried in code
4. **Query examples** - Show how to use the data

---

## Data Organization Pattern

File conventions in `docs/DATA_ORGANIZATION.md`.

### Client Data Path

```
data/clients/{client_id}/{category}/{filename}
```

Examples:
```
data/clients/713/mappings/internal-affiliates.csv
data/clients/713/exports/daily-summary.csv
data/clients/cti/mappings/campaigns.csv
```

### Rules

1. **All client data under `data/clients/`** - Never scattered
2. **Supabase tables tagged with `_client_id`** - Always
3. **Reference data flow**: CSV (repo) → Load script → Supabase
4. **dlt config hierarchy**: Use `.dlt/config.toml` for paths

---

## New Project Checklist

### 1. Core Structure

```bash
mkdir -p project/{src,docs,scripts,tests,.claude/skills}
touch project/{CLAUDE.md,README.md,Makefile,pyproject.toml}
touch project/docs/{API_REFERENCE.md,DATA_MODEL.md,DATA_ORGANIZATION.md}
touch project/docs/{SOURCES.md,OPERATIONS.md,ROADMAP.md}
mkdir -p project/docs/{templates,archive}
```

### 2. Essential Skills

Create these skills first:

| Skill | Purpose |
|-------|---------|
| `deploy` | Deployment checklist, recovery |
| `troubleshoot` | Read-only diagnostics |
| `git` | Commit standards, PR workflow |

### 3. Documentation Order

Write in this order:

1. **README.md** - Quick start, architecture overview
2. **CLAUDE.md** - Commands, structure, AI guidance
3. **API_REFERENCE.md** - External APIs (live URLs!)
4. **DATA_MODEL.md** - Entity relationships
5. **SOURCES.md** - Implementation details
6. **OPERATIONS.md** - Runbooks (as you learn them)

### 4. Skill Creation Order

Create skills as workflows emerge:

1. Start with 3 essential skills above
2. Add technology skills as integrations develop
3. Add diagnostic skills after first incident
4. Add process skills for repeated patterns

### 5. Verification

Before going live:

- [ ] All external API URLs verified working
- [ ] Skills cross-referenced against implementation
- [ ] Primary keys documented and match code
- [ ] `_client_id` tagging in place
- [ ] Commands in CLAUDE.md tested

---

## Anti-Patterns

### Documentation

- **Duplicated content** - Single source of truth, cross-reference instead
- **Stale examples** - Test examples, keep them working
- **API keys in docs** - Never, use `.env.example` patterns
- **Undated decisions** - Include dates on time-sensitive content

### Skills

- **Too many tools** - Restrict tools when workflow allows
- **No references** - Always link to related docs
- **Command-only** - Include context and common issues
- **Outdated primary keys** - Cross-reference with implementation

### Structure

- **Scattered client data** - Always under `data/clients/{id}/`
- **Missing `_client_id`** - All Supabase tables must have it
- **Hardcoded paths** - Use config files

---

## Maintenance

### Monthly

- [ ] Verify all API reference URLs still work
- [ ] Check skills against current implementation
- [ ] Archive any stale docs

### After Each Feature

- [ ] Update relevant source docs
- [ ] Add/update skills if workflow changed
- [ ] Update DATA_MODEL.md if schema changed

### After Incidents

- [ ] Create postmortem in `docs/archive/`
- [ ] Update OPERATIONS.md with new runbook
- [ ] Update troubleshoot skill if applicable

---

## References

- **This Project**: Look at SignalRoom as the reference implementation
- **dlt**: https://dlthub.com/docs
- **Temporal**: https://docs.temporal.io
- **Claude Code Skills**: See `.claude/skills/*/SKILL.md` for examples
