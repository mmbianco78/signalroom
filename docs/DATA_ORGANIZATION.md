# Data Organization Guide

This document defines the standard patterns for organizing client-specific data, configuration, and reference files in SignalRoom. **All contributors (human and AI) must follow these patterns.**

---

## Core Principles

1. **Client isolation**: All client-specific data lives under `data/clients/{client_id}/`
2. **Convention over configuration**: Use consistent naming, not custom paths
3. **Source of truth in repo**: Reference data (CSVs) committed to git, synced to Supabase
4. **dlt alignment**: Follow dlt's config patterns for pipeline settings

---

## Directory Structure

```
signalroom/
├── .dlt/
│   ├── config.toml              # Pipeline config (non-sensitive, committed)
│   └── secrets.toml             # API keys (gitignored)
│
├── data/
│   └── clients/
│       ├── 713/                 # Client: 713
│       │   └── mappings/
│       │       └── internal-affiliates.csv
│       └── cti/                 # Client: CTI (future)
│           └── mappings/
│               └── (future files)
│
├── src/signalroom/
│   ├── sources/                 # dlt sources (platform-specific, not client-specific)
│   ├── pipelines/               # Pipeline runner
│   └── common/
│       └── config.py            # Settings from env vars
│
└── scripts/
    └── load_mappings.py         # Sync CSVs to Supabase
```

---

## Client Data Patterns

### File Location Convention

```
data/clients/{client_id}/{category}/{filename}
```

| Component | Description | Examples |
|-----------|-------------|----------|
| `client_id` | Client identifier (lowercase) | `713`, `cti` |
| `category` | Data category | `mappings`, `seeds`, `overrides` |
| `filename` | Descriptive name | `internal-affiliates.csv` |

### Current Client IDs

| ID | Name | Status |
|----|------|--------|
| `713` | 713 | Active |
| `cti` | ClayTargetInstruction | Planned |

### Adding a New Client

1. Create directory: `data/clients/{new_client_id}/mappings/`
2. Add mapping files as needed
3. Update `src/signalroom/common/clients.py` (if exists)
4. Run sync script: `python scripts/load_mappings.py --client {new_client_id}`

---

## Reference Data (Mappings)

### Purpose

Reference data maps identifiers between systems (e.g., Redtrack source IDs → Everflow affiliate IDs). These are:
- **Versioned** in git (source of truth)
- **Loaded** to Supabase for SQL joins
- **Client-specific** (each client has their own mappings)

### File Format

CSV with headers. Example (`internal-affiliates.csv`):

```csv
redtrack.source,redtrack.source_id,everflow.affiliate_id,everflow.affiliate_label,everflow.advertiser_id
Facebook CCW,66c79f91be26fd4634569658,1,G2 - Meta,1
Google Ads CCW,62b29551c6880d00014d8c73,1,G2 - Google,1
```

### Supabase Table Convention

Reference data loads to `public.{table_name}` with a `client_id` column:

```sql
CREATE TABLE public.affiliate_mapping (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,              -- '713', 'cti', etc.
    redtrack_source TEXT,
    redtrack_source_id TEXT NOT NULL,
    everflow_affiliate_id INTEGER,
    everflow_affiliate_label TEXT,
    everflow_advertiser_id INTEGER,
    everflow_advertiser_label TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, redtrack_source_id)
);
```

### Sync Script Usage

```bash
# Sync specific client
python scripts/load_mappings.py --client 713

# Sync all clients
python scripts/load_mappings.py --all

# Dry run (preview without loading)
python scripts/load_mappings.py --client 713 --dry-run
```

---

## dlt Configuration

### .dlt/config.toml

Non-sensitive pipeline configuration. Use client prefixes for client-specific settings:

```toml
# Global settings
[runtime]
log_level = "INFO"

# Source defaults
[sources.everflow]
base_url = "https://api.eflow.team"

[sources.redtrack]
base_url = "https://api.redtrack.io"

# Client-specific overrides (if needed)
[sources.affiliate_mapping.clients.713]
csv_path = "data/clients/713/mappings/internal-affiliates.csv"

[sources.affiliate_mapping.clients.cti]
csv_path = "data/clients/cti/mappings/internal-affiliates.csv"
```

### .dlt/secrets.toml (gitignored)

Sensitive credentials only:

```toml
[sources.everflow]
api_key = "your-api-key"

[sources.redtrack]
api_key = "your-api-key"

[destination.postgres]
credentials = "postgresql://..."
```

---

## Supabase Data Tagging

All data loaded to Supabase includes a `_client_id` column for filtering:

```sql
-- Query specific client
SELECT * FROM everflow.daily_stats WHERE _client_id = '713';

-- Query with client join
SELECT e.*, m.everflow_affiliate_label
FROM everflow.daily_stats e
JOIN public.affiliate_mapping m
  ON e.affiliate_id = m.everflow_affiliate_id
  AND e._client_id = m.client_id
WHERE e._client_id = '713';
```

---

## Adding New Reference Data

### Step-by-Step

1. **Create the CSV file**:
   ```
   data/clients/{client_id}/mappings/{descriptive-name}.csv
   ```

2. **Define headers** matching the target schema

3. **Create Supabase migration** (if new table):
   ```sql
   -- migrations/YYYYMMDD_create_{table_name}.sql
   CREATE TABLE public.{table_name} (
       id SERIAL PRIMARY KEY,
       client_id TEXT NOT NULL,
       -- ... columns matching CSV ...
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

4. **Add to sync script** (if not auto-discovered)

5. **Document** in this file under "Reference Data Types"

---

## Reference Data Types

### internal-affiliates.csv

**Purpose**: Maps Redtrack traffic sources to Everflow affiliates for cost/revenue merge.

**Location**: `data/clients/{client_id}/mappings/internal-affiliates.csv`

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| redtrack.source | text | Redtrack source name |
| redtrack.source_id | text | Redtrack source ID (primary key) |
| everflow.affiliate_id | int | Everflow affiliate ID |
| everflow.affiliate_label | text | Everflow affiliate name |
| everflow.advertiser_id | int | Everflow advertiser ID (1=CCW, 2=EXP) |
| everflow.advertiser_label | text | Advertiser name |

**Used by**: Phase 3 merge logic, daily reports

---

## Anti-Patterns (Do NOT Do)

| Anti-Pattern | Why It's Bad | Correct Pattern |
|--------------|--------------|-----------------|
| `data/713-affiliates.csv` | Client ID buried in filename | `data/clients/713/mappings/affiliates.csv` |
| `src/signalroom/data/mappings.csv` | Mixing code and data | `data/clients/{id}/mappings/` |
| Hardcoding paths in source code | Not configurable | Use `config.toml` or conventions |
| Client-specific logic in sources | Sources should be generic | Pass `client_id` as parameter |
| Storing secrets in `config.toml` | Security risk | Use `secrets.toml` (gitignored) |

---

## For AI/LLM Agents

When implementing new features that involve client-specific data:

1. **Always ask**: "Is this data client-specific or universal?"
2. **If client-specific**: Place in `data/clients/{client_id}/`
3. **If universal**: Place in `data/shared/` or configure in `.dlt/config.toml`
4. **Tag all Supabase data** with `_client_id` column
5. **Follow existing patterns** - check this doc and existing implementations
6. **Update this doc** when adding new data types

### Checklist for New Data Types

- [ ] File placed in `data/clients/{client_id}/{category}/`
- [ ] CSV has clear, consistent headers
- [ ] Supabase table includes `client_id` column
- [ ] Sync script updated (if needed)
- [ ] This doc updated with new data type section
- [ ] CLAUDE.md updated (if pattern changes)
