-- Daily CCW Performance Report
-- Parameters: :date, :advertiser_id (default 1 for CCW)

WITH daily_totals AS (
    SELECT
        SUM(conversions) as total_conversions,
        SUM(cost) as total_cost,
        CASE
            WHEN SUM(conversions) > 0
            THEN SUM(cost) / SUM(conversions)
            ELSE 0
        END as overall_cpa
    FROM public.daily_performance
    WHERE date = :date
      AND advertiser_id = :advertiser_id
),
internal_totals AS (
    SELECT
        SUM(conversions) as conversions,
        SUM(cost) as cost,
        CASE
            WHEN SUM(conversions) > 0
            THEN SUM(cost) / SUM(conversions)
            ELSE 0
        END as cpa
    FROM public.daily_performance
    WHERE date = :date
      AND advertiser_id = :advertiser_id
      AND is_internal = true
),
external_totals AS (
    SELECT
        SUM(conversions) as conversions,
        SUM(cost) as cost,
        CASE
            WHEN SUM(conversions) > 0
            THEN SUM(cost) / SUM(conversions)
            ELSE 0
        END as cpa
    FROM public.daily_performance
    WHERE date = :date
      AND advertiser_id = :advertiser_id
      AND is_internal = false
),
top_affiliates AS (
    SELECT
        affiliate_label,
        conversions,
        cost,
        cpa,
        is_internal
    FROM public.daily_performance
    WHERE date = :date
      AND advertiser_id = :advertiser_id
      AND conversions > 0
    ORDER BY conversions DESC
    LIMIT 10
)
SELECT
    :date as report_date,
    dt.total_conversions,
    dt.total_cost,
    dt.overall_cpa,
    it.conversions as internal_conversions,
    it.cost as internal_cost,
    it.cpa as internal_cpa,
    et.conversions as external_conversions,
    et.cost as external_cost,
    et.cpa as external_cpa,
    (
        SELECT json_agg(row_to_json(ta))
        FROM top_affiliates ta
    ) as top_affiliates
FROM daily_totals dt
CROSS JOIN internal_totals it
CROSS JOIN external_totals et;
