# Data Model

Entity relationships, business logic, and schema definitions for SignalRoom.

> **Related docs:**
> - `API_REFERENCE.md` — External API endpoints and authentication
> - `DATA_ORGANIZATION.md` — File conventions and dlt config patterns

---

## Entity Relationships

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│    Redtrack     │         │ affiliate_mapping │         │    Everflow     │
│  (ad spend)     │────────▶│   (join table)   │◀────────│  (conversions)  │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                           │                            │
        │ source_id                 │                            │ affiliate_id
        │                           │                            │ advertiser_id
        ▼                           ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        daily_performance (view)                          │
│  Merges spend + conversions, calculates CPA, flags internal/external    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Tables

### everflow.daily_stats

Conversion and revenue data from Everflow affiliate network.

| Column | Type | Description |
|--------|------|-------------|
| `date` | text | Report date (YYYY-MM-DD) |
| `affiliate_id` | integer | Everflow affiliate ID |
| `affiliate_label` | text | Affiliate name |
| `advertiser_id` | integer | Advertiser/brand ID |
| `advertiser_label` | text | Advertiser name |
| `clicks` | bigint | Click count |
| `conversions` | bigint | Conversion count |
| `revenue` | double | Gross revenue |
| `payout` | double | Affiliate payout |
| `profit` | double | Net profit |
| `_client_id` | text | Client identifier |
| `_loaded_at` | text | Load timestamp |

**Primary Key:** `(date, affiliate_id, advertiser_id)`

---

### redtrack.daily_spend

Ad spend data from Redtrack, grouped by traffic source.

| Column | Type | Description |
|--------|------|-------------|
| `date` | text | Report date (YYYY-MM-DD) |
| `source_id` | text | Redtrack source ID |
| `source_name` | text | Traffic source name |
| `source_alias` | text | Platform alias (facebook, google) |
| `clicks` | bigint | Click count |
| `conversions` | bigint | Redtrack-tracked conversions |
| `cost` | double | Ad spend |
| `_client_id` | text | Client identifier |
| `_loaded_at` | text | Load timestamp |

**Primary Key:** `(date, source_id)`

---

### public.affiliate_mapping

Links Redtrack traffic sources to Everflow affiliates for merged reporting.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `redtrack_source_name` | text | Redtrack source name |
| `redtrack_source_alias` | text | Platform alias |
| `redtrack_source_id` | text | Redtrack source ID |
| `everflow_affiliate_id` | integer | Everflow affiliate ID |
| `everflow_affiliate_label` | text | Everflow affiliate name |
| `everflow_advertiser_id` | integer | Everflow advertiser ID |
| `everflow_advertiser_label` | text | Advertiser name |
| `_client_id` | text | Client identifier |
| `created_at` | timestamptz | Creation timestamp |
| `updated_at` | timestamptz | Update timestamp |

---

## Affiliate Mapping Values

### Advertisers (Brands)

| ID | Label | Description |
|----|-------|-------------|
| 1 | CCW | Concealed Carry |
| 2 | EXP | Expungement |

### Internal Affiliates

These run paid ads on Meta/Google, tracked in Redtrack. Their `cost` comes from Redtrack spend.

| Redtrack Source | Source ID | Everflow Affiliate | Platform | Advertiser |
|-----------------|-----------|-------------------|----------|------------|
| Facebook CCW | `66c79f91be26fd4634569658` | G2 - Meta | Meta | CCW |
| Meta CCW AWF2 Stephanie | `6807d9120ee9ffc623c1d7e5` | SB - Meta | Meta | CCW |
| Meta CCW SB Political | `68b87e99882b48e6620a3116` | SB - Meta | Meta | CCW |
| Google Ads CCW | `62b29551c6880d00014d8c73` | G2 - Google | Google | CCW |
| Google Ads AWF2 SB | (varies) | SB - Google | Google | CCW |
| Facebook EXP | `67c097f0aee15ff71f3f99aa` | G2 - Meta | Meta | EXP |
| Facebook CCW BHS | (varies) | BHS | Meta | CCW |

### External Affiliates

These are third-party affiliates. Their `cost` is the Everflow payout.

Examples: Blue Bench Media, Venture Beyond, ProfitFuel, Adprecise, AC Email, etc.

---

## Business Logic

### Internal vs External Classification

An affiliate is **internal** if their label matches:
- `G2 - Meta` or `G2 - Meta ` (note: trailing space variant exists)
- `G2 - Google`
- `SB - Meta`
- `SB - Google`

All other affiliates are **external**.

### Cost Calculation

| Affiliate Type | Cost Source | Logic |
|----------------|-------------|-------|
| Internal | Redtrack | `cost = redtrack.daily_spend.cost` (via affiliate_mapping join) |
| External | Everflow | `cost = everflow.daily_stats.payout` |

### CPA Calculation

```
CPA = cost / conversions
```

Where `cost` depends on internal/external classification above.

---

## Views

### public.daily_performance

Merges Everflow conversions with Redtrack spend for unified reporting.

```sql
-- Simplified structure (actual view uses CTEs for aggregation)
SELECT
    e.date,
    e.advertiser_id,
    e.advertiser_label,
    e.affiliate_label,
    e.conversions,
    e.payout AS everflow_payout,
    e.revenue AS everflow_revenue,
    COALESCE(r.redtrack_cost, 0) AS redtrack_cost,

    -- Internal flag based on affiliate name
    CASE WHEN e.affiliate_label IN ('G2 - Meta', 'G2 - Meta ', 'G2 - Google', 'SB - Meta', 'SB - Google')
         THEN true ELSE false
    END AS is_internal,

    -- Cost: Redtrack for internal, Everflow payout for external
    CASE WHEN is_internal THEN redtrack_cost ELSE everflow_payout
    END AS cost,

    -- CPA calculation
    CASE WHEN conversions > 0 THEN ROUND(cost / conversions, 2) ELSE 0
    END AS cpa

FROM everflow_stats e
LEFT JOIN redtrack_by_affiliate r
    ON e.date = r.date
    AND e.affiliate_label = r.everflow_affiliate_label
    AND e.advertiser_id = r.everflow_advertiser_id;
```

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `date` | text | Report date |
| `advertiser_id` | integer | Brand ID (1=CCW, 2=EXP) |
| `advertiser_label` | text | Brand name |
| `affiliate_label` | text | Affiliate name |
| `conversions` | numeric | From Everflow |
| `everflow_payout` | numeric | Affiliate payout |
| `everflow_revenue` | numeric | Gross revenue |
| `redtrack_cost` | double | Ad spend (internal only) |
| `redtrack_clicks` | numeric | Clicks (internal only) |
| `is_internal` | boolean | True if internal affiliate |
| `cost` | double | Effective cost (see logic above) |
| `cpa` | numeric | Cost per acquisition |

---

## Query Examples

### Daily Performance by Affiliate

```sql
SELECT
    affiliate_label,
    conversions,
    cost,
    cpa,
    is_internal
FROM public.daily_performance
WHERE date = '2025-12-18'
  AND advertiser_id = 1
ORDER BY conversions DESC;
```

### Internal vs External Totals

```sql
SELECT
    is_internal,
    SUM(conversions) as conversions,
    SUM(cost) as cost,
    ROUND(SUM(cost) / NULLIF(SUM(conversions), 0), 2) as cpa
FROM public.daily_performance
WHERE date = '2025-12-18' AND advertiser_id = 1
GROUP BY is_internal;
```

### Weekly Trend

```sql
SELECT
    date,
    SUM(conversions) as conversions,
    SUM(cost) as cost,
    ROUND(SUM(cost) / NULLIF(SUM(conversions), 0), 2) as cpa
FROM public.daily_performance
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
  AND advertiser_id = 1
GROUP BY date
ORDER BY date;
```

---

## Data Flow

```
1. Temporal Schedule triggers sync
          │
          ▼
2. Everflow API ──► everflow.daily_stats
   Redtrack API ──► redtrack.daily_spend
          │
          ▼
3. daily_performance view joins data via affiliate_mapping
          │
          ▼
4. Reports query the view for Slack/Email/SMS output
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-19 | Initial creation - consolidated from INTEGRATIONS.md |
