-- Test sync report: Just basic totals for today
-- No sensitive affiliate breakdown data

SELECT
    :date AS report_date,
    COALESCE(
        (SELECT SUM(conversions)
         FROM everflow.daily_stats
         WHERE date = :date),
        0
    ) AS everflow_conversions,
    COALESCE(
        (SELECT SUM(cost)
         FROM redtrack.daily_spend
         WHERE date = :date),
        0
    ) AS redtrack_spend
