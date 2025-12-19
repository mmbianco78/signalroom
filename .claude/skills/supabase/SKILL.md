---
name: supabase
description: Supabase and Postgres database operations for SignalRoom. Use for database queries, schema inspection, connection troubleshooting, or checking loaded data.
---

# Supabase Operations

## Connection Details

**Project:** 713 Main DB
**Project Ref:** `foieoinshqlescyocbld`

### Direct Connection (local dev)
```
Host: db.foieoinshqlescyocbld.supabase.co
Port: 5432
User: postgres
```

### Pooler Connection (Fly.io, serverless)
```
Host: aws-0-us-east-1.pooler.supabase.com
Port: 6543
User: postgres.foieoinshqlescyocbld
```

## Quick Queries via MCP

```
# List tables
mcp__supabase-713__list_tables

# Execute SQL
mcp__supabase-713__execute_sql with query

# Check security advisors
mcp__supabase-713__get_advisors type="security"
```

## Common SQL Queries

### Check loaded data
```sql
-- Row counts by table
SELECT schemaname, tablename, n_tup_ins as rows
FROM pg_stat_user_tables
WHERE schemaname NOT LIKE '_dlt%'
ORDER BY n_tup_ins DESC;

-- Recent dlt loads
SELECT * FROM s3_exports._dlt_loads
ORDER BY inserted_at DESC LIMIT 5;

-- Everflow daily stats
SELECT date, SUM(conversions), SUM(payout)
FROM everflow.daily_stats
GROUP BY date ORDER BY date DESC LIMIT 7;

-- Redtrack daily spend
SELECT date, SUM(cost)
FROM redtrack.daily_spend
GROUP BY date ORDER BY date DESC LIMIT 7;
```

### Schema inspection
```sql
-- List all schemas
SELECT schema_name FROM information_schema.schemata
WHERE schema_name NOT IN ('pg_catalog', 'information_schema');

-- Tables in a schema
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'everflow';

-- Column details
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'everflow' AND table_name = 'daily_stats';
```

## Troubleshooting

**"password authentication failed"**
- Check user format: must be `postgres.{project_ref}` for pooler
- Port must be 6543 for pooler, 5432 for direct
- Password may have special chars - verify in Supabase dashboard

**"connection refused"**
- Project may be paused - check Supabase dashboard
- Wrong host - pooler vs direct connection

**"too many connections"**
- Use pooler connection (port 6543)
- Check for connection leaks in code

## Dashboard Links

- **Supabase Dashboard:** https://supabase.com/dashboard/project/foieoinshqlescyocbld
- **Table Editor:** https://supabase.com/dashboard/project/foieoinshqlescyocbld/editor
- **SQL Editor:** https://supabase.com/dashboard/project/foieoinshqlescyocbld/sql
