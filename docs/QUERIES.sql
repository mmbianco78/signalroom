-- SignalRoom SQL Query Reference
-- Schema: s3_exports
-- Tables: orders_create, orders_update
-- Data: December 2025 (304,951 orders_create, 346,044 orders_update)

-- =============================================================================
-- BASIC OVERVIEW QUERIES
-- =============================================================================

-- Daily Orders & Revenue Trend
SELECT
  _file_date as date,
  COUNT(*) FILTER (WHERE order_status = 'NEW') as approved,
  COUNT(*) FILTER (WHERE order_status = 'DECLINED') as declined,
  ROUND(SUM(total_amount::numeric) FILTER (WHERE order_status = 'NEW'), 0) as revenue
FROM s3_exports.orders_create
GROUP BY _file_date
ORDER BY _file_date;

-- Order Status Breakdown (for pie/donut chart)
SELECT
  order_status,
  COUNT(*) as orders,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM s3_exports.orders_create
GROUP BY order_status
ORDER BY orders DESC;

-- Price Tier Distribution (for histogram)
SELECT
  CASE
    WHEN total_amount::numeric < 25 THEN '$0-24'
    WHEN total_amount::numeric < 50 THEN '$25-49'
    WHEN total_amount::numeric < 100 THEN '$50-99'
    ELSE '$100+'
  END as price_tier,
  COUNT(*) as orders,
  ROUND(SUM(total_amount::numeric), 0) as revenue
FROM s3_exports.orders_create
WHERE order_status = 'NEW'
GROUP BY 1
ORDER BY MIN(total_amount::numeric);

-- =============================================================================
-- GEOGRAPHIC ANALYSIS
-- =============================================================================

-- Orders & Revenue by State
SELECT
  billing_state as state,
  COUNT(DISTINCT orders_id) as orders,
  COUNT(DISTINCT billing_email) as customers,
  ROUND(SUM(total_amount::numeric), 2) as revenue,
  ROUND(AVG(total_amount::numeric), 2) as avg_order
FROM s3_exports.orders_create
WHERE order_status = 'NEW'
  AND total_amount::numeric > 85
GROUP BY billing_state
ORDER BY revenue DESC;

-- Decline Rate by State (for heatmap)
SELECT
  billing_state as state,
  COUNT(*) as total_orders,
  COUNT(*) FILTER (WHERE order_status = 'DECLINED') as declined,
  ROUND(100.0 * COUNT(*) FILTER (WHERE order_status = 'DECLINED') / COUNT(*), 1) as decline_rate
FROM s3_exports.orders_create
WHERE billing_state IS NOT NULL AND billing_state != ''
GROUP BY billing_state
HAVING COUNT(*) > 50
ORDER BY decline_rate DESC;

-- =============================================================================
-- CAMPAIGN & ATTRIBUTION ANALYSIS
-- =============================================================================

-- Campaign Performance
SELECT
  COALESCE(NULLIF(campaign_id, ''), 'direct') as campaign,
  COUNT(*) as total_orders,
  COUNT(*) FILTER (WHERE order_status = 'NEW') as approved,
  ROUND(100.0 * COUNT(*) FILTER (WHERE order_status = 'NEW') / COUNT(*), 1) as approval_rate,
  ROUND(SUM(total_amount::numeric) FILTER (WHERE order_status = 'NEW'), 0) as revenue
FROM s3_exports.orders_create
GROUP BY campaign_id
ORDER BY revenue DESC
LIMIT 15;

-- Campaign Approval Rates Only (for bar chart)
SELECT
  COALESCE(NULLIF(campaign_id, ''), 'direct') as campaign,
  ROUND(100.0 * COUNT(*) FILTER (WHERE order_status = 'NEW') / COUNT(*), 1) as approval_rate
FROM s3_exports.orders_create
GROUP BY campaign_id
HAVING COUNT(*) > 100
ORDER BY approval_rate DESC
LIMIT 15;

-- Affiliate Approval Rates (for leaderboard)
SELECT
  COALESCE(NULLIF(affid, ''), 'direct') as affiliate,
  COUNT(*) as total_orders,
  ROUND(100.0 * COUNT(*) FILTER (WHERE order_status = 'NEW') / COUNT(*), 1) as approval_rate
FROM s3_exports.orders_create
GROUP BY affid
HAVING COUNT(*) > 100
ORDER BY approval_rate DESC
LIMIT 20;

-- =============================================================================
-- PAYMENT & RISK ANALYSIS
-- =============================================================================

-- Payment Gateway Performance
SELECT
  COALESCE(NULLIF(gateway_alias, ''), 'unknown') as gateway,
  COUNT(*) as attempts,
  COUNT(*) FILTER (WHERE order_status = 'NEW') as approved,
  COUNT(*) FILTER (WHERE order_status = 'DECLINED') as declined,
  ROUND(100.0 * COUNT(*) FILTER (WHERE order_status = 'DECLINED') / COUNT(*), 1) as decline_rate
FROM s3_exports.orders_create
GROUP BY gateway_alias
HAVING COUNT(*) > 100
ORDER BY decline_rate DESC;

-- Chargeback & Refund Risk by Date
SELECT
  _file_date as date,
  COUNT(*) as total_orders,
  SUM(CASE WHEN chargeback_flag = '1' THEN 1 ELSE 0 END) as chargebacks,
  SUM(CASE WHEN refund_flag = '1' THEN 1 ELSE 0 END) as refunds,
  ROUND(100.0 * SUM(CASE WHEN chargeback_flag = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as chargeback_pct,
  ROUND(100.0 * SUM(CASE WHEN refund_flag = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as refund_pct
FROM s3_exports.orders_update
GROUP BY _file_date
ORDER BY _file_date;

-- =============================================================================
-- ADVANCED / VISUALIZATION QUERIES
-- =============================================================================

-- Cumulative Revenue Waterfall
SELECT
  _file_date as date,
  ROUND(SUM(total_amount::numeric) FILTER (WHERE order_status = 'NEW'), 0) as daily_revenue,
  ROUND(SUM(SUM(total_amount::numeric) FILTER (WHERE order_status = 'NEW')) OVER (ORDER BY _file_date), 0) as cumulative_revenue
FROM s3_exports.orders_create
GROUP BY _file_date
ORDER BY _file_date;

-- Approval vs Decline Scatter by State (bubble size = volume)
SELECT
  billing_state as state,
  COUNT(*) FILTER (WHERE order_status = 'NEW') as approved,
  COUNT(*) FILTER (WHERE order_status = 'DECLINED') as declined,
  COUNT(*) as total_volume,
  ROUND(SUM(total_amount::numeric) FILTER (WHERE order_status = 'NEW'), 0) as revenue
FROM s3_exports.orders_create
WHERE billing_state IS NOT NULL AND billing_state != ''
GROUP BY billing_state
HAVING COUNT(*) > 100
ORDER BY total_volume DESC;

-- Key Column Reference:
-- orders_id: Unique order ID
-- order_status: NEW, DECLINED, VOID/REFUNDED (no "approved" status)
-- total_amount: Stored as text, cast to numeric
-- billing_state: Customer state
-- product_category: Project identifier (CCW, etc.)
-- campaign_id: Campaign attribution
-- affid: Affiliate ID
-- gateway_alias: Payment processor
-- chargeback_flag: "1" if chargedback
-- refund_flag: "1" if refunded
-- _client_id: Multi-client tag (713, CTI)
-- _file_date: Date extracted from filename
