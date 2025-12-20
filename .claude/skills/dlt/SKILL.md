---
name: dlt
description: dlt (data load tool) patterns for SignalRoom ETL pipelines. Use when creating sources, debugging pipeline failures, understanding schema evolution, or implementing incremental loading.
---

# dlt Data Load Tool

## Core Concepts

**dlt** handles extract, normalize, and load. You define sources and resources; dlt handles schema inference, table creation, and loading.

## Source Structure

```
src/signalroom/sources/{source_name}/
└── __init__.py  # Contains @dlt.source and @dlt.resource
```

### Creating a New Source

```python
import dlt
from signalroom.common import settings

@dlt.source(name="my_source")
def my_source():
    """Source docstring appears in dlt metadata."""

    @dlt.resource(write_disposition="append", primary_key="id")
    def my_resource():
        yield from fetch_data()

    return [my_resource]
```

### Register in Pipeline Runner

Add to `src/signalroom/pipelines/runner.py`:

```python
SOURCES = {
    "my_source": "signalroom.sources.my_source:my_source",
}
```

## Write Dispositions

| Mode | Use Case | Behavior |
|------|----------|----------|
| `append` | Immutable events (clicks, conversions) | Always insert new rows |
| `merge` | Mutable entities (campaigns, contacts) | Upsert by primary_key |
| `replace` | Full refresh (feature flags, config) | Drop and recreate table |

## Incremental Loading

Only fetch new data since last run:

```python
@dlt.resource(write_disposition="append", primary_key="id")
def events(
    updated_at: dlt.sources.incremental[str] = dlt.sources.incremental(
        "updated_at",
        initial_value="2024-01-01"
    )
):
    # Only fetches records after last loaded timestamp
    yield from api.get_events(since=updated_at.last_value)
```

## Primary Keys

Required for `merge` disposition:

```python
# Single key
@dlt.resource(primary_key="id")

# Composite key
@dlt.resource(primary_key=["date", "affiliate_id"])
```

## Schema Evolution

dlt auto-evolves schemas. New columns added automatically. To see current schema:

```sql
SELECT * FROM {schema}._dlt_loads ORDER BY inserted_at DESC LIMIT 5;
```

## Debugging Failed Loads

### Check dlt metadata tables

```sql
-- Recent loads
SELECT load_id, schema_name, status, inserted_at
FROM {schema}._dlt_loads
ORDER BY inserted_at DESC LIMIT 10;

-- Pipeline state
SELECT * FROM {schema}._dlt_pipeline_state;
```

### Common Errors

**"Primary key violation"**
- Using `append` when you need `merge`
- Duplicate records in source data

**"Column type mismatch"**
- Schema evolved incompatibly
- Fix: Drop table or add explicit column hints

**"Connection refused"**
- Check Supabase pooler settings (port 6543, user format)

### Drop Pending Packages

If pipeline is stuck:

```bash
dlt pipeline {pipeline_name} drop-pending-packages
```

## SignalRoom Sources

| Source | Write Mode | Primary Key |
|--------|------------|-------------|
| `s3_exports` | append | `_file_name, _row_id` |
| `everflow` | merge | `date, affiliate_id, advertiser_id` |
| `redtrack` | merge | `date, source_id` |

## Testing Locally

Use DuckDB for fast local testing:

```python
pipeline = dlt.pipeline(
    pipeline_name="test",
    destination="duckdb",
    dataset_name="test"
)
```

## Resources

- [dlt Documentation](https://dlthub.com/docs)
- [Write Dispositions](https://dlthub.com/docs/general-usage/incremental-loading)
- [Schema Evolution](https://dlthub.com/docs/general-usage/schema)
- **SignalRoom API Reference**: `docs/API_REFERENCE.md` — Live docs, auth, request/response examples
