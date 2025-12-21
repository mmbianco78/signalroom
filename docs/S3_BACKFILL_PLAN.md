# S3 Backfill Plan

> **Status**: Deferred - Pending incremental loading implementation first
> **Created**: 2025-12-21
> **Priority**: Medium (not blocking daily operations once incremental is fixed)

## Context

The S3 exports source (`s3_exports`) loads CSV files from S3 that are pushed daily by Sticky.io. Before implementing incremental loading, we identified a need to potentially backfill historical data.

## Current State

### S3 Bucket (Available Data)
| Prefix | Files | Date Range |
|--------|-------|------------|
| `orders-create` | 91 | Sep 22, 2025 → Dec 21, 2025 |
| `orders-update` | 91 | Sep 22, 2025 → Dec 21, 2025 |
| `prospects-create` | 0 | (empty) |

### Supabase (Currently Loaded)
| Table | Files | Date Range |
|-------|-------|------------|
| `orders_create` | 18 | Dec 1 → Dec 18, 2025 |
| `orders_update` | 18 | Dec 1 → Dec 18, 2025 |

### Gap Analysis
| Gap Type | Range | Days | Notes |
|----------|-------|------|-------|
| **Forward** | Dec 19-21 | 3 | Will be handled by incremental loading |
| **Historical** | Sep 22 → Nov 30 | 70 | Optional backfill |

## Backfill Options

### Option 1: Full Historical Backfill
- Load all data from Sep 22, 2025
- ~182 files total (91 per prefix)
- Estimated time: 2-3 hours
- Pros: Complete historical record
- Cons: Time-consuming, may not be needed

### Option 2: Partial Backfill (Recommended to Evaluate)
- Choose a business-relevant start date (e.g., Nov 1)
- Load ~50 days instead of 91
- Estimated time: ~1 hour
- Pros: Faster, covers recent history
- Cons: Incomplete historical record

### Option 3: No Backfill
- Accept Dec 1 as the start of SignalRoom data
- Historical analysis uses legacy system
- Pros: Zero effort
- Cons: Limited historical visibility

## Implementation Approach

Once incremental loading is in place, backfill can be done using dlt's `end_value` parameter:

```python
# Partitioned backfill - does NOT modify incremental state
from signalroom.sources.s3_exports import s3_exports

# Run specific date ranges
november_data = s3_exports(
    from_date="2025-11-01",
    to_date="2025-11-30"
)

# Or use dlt's built-in range support
pipeline.run(
    s3_exports().with_resources("orders_create")(
        file_date=dlt.sources.incremental(
            "_file_date",
            initial_value="2025-11-01",
            end_value="2025-12-01"  # Exclusive
        )
    )
)
```

### Backfill Script Design

Create `scripts/backfill_s3.py`:
```bash
# Usage examples
python scripts/backfill_s3.py --start 2025-11-01 --end 2025-11-30
python scripts/backfill_s3.py --start 2025-09-22 --end 2025-12-01 --batch-size 7
python scripts/backfill_s3.py --dry-run  # Show what would be loaded
```

Features:
- `--start` / `--end`: Explicit date bounds (required)
- `--batch-size`: Process N days at a time (avoid memory/timeout issues)
- `--dry-run`: List files without loading
- `--prefix`: Specific prefix only (orders-create, orders-update)
- Progress tracking with resume capability

## Questions to Answer Before Backfilling

1. **Business need**: Is historical data (Sep-Nov) actually needed for reports?
2. **Data quality**: Are older files in the same format as recent ones?
3. **Storage cost**: How much Supabase storage will 70 extra days consume?
4. **Report dependencies**: Do any reports require data before Dec 1?

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-21 | Defer backfill | Focus on incremental loading first; backfill is optional |

## Next Steps

1. Complete incremental loading implementation
2. Verify forward processing works correctly
3. Revisit this document to decide on backfill scope
4. If backfilling: create `scripts/backfill_s3.py`
