-- ============================================================
-- SMB Diagnostic Engine
-- Script : 02_clean_table.sql
-- Purpose: Build smb_diagnostic — a clean, validated, analysis-ready
--          table from smb_raw. Preserves smb_raw untouched.
-- Author : Oceana O'Dean
-- ============================================================


-- ------------------------------------------------------------
-- STEP 1: Drop existing clean table if rebuilding
-- ------------------------------------------------------------
DROP TABLE IF EXISTS smb_diagnostic;


-- ------------------------------------------------------------
-- STEP 2: Create clean table
-- Cleaning operations applied:
--   - DISTINCT ON (business_id, month) removes duplicates
--   - TRIM() removes leading/trailing whitespace
--   - INITCAP() standardises casing in categorical columns
--   - CASE statement repairs all 5 malformed date formats
--   - WHERE conditions remove all invalid values
-- ------------------------------------------------------------
CREATE TABLE smb_diagnostic AS
SELECT DISTINCT ON (business_id, month)
    TRIM(business_id)                               AS business_id,
    INITCAP(TRIM(industry))                         AS industry,
    INITCAP(TRIM(region))                           AS region,
    CASE
        WHEN month LIKE '____-__'  THEN month
        WHEN month LIKE '__/____'  THEN SUBSTRING(month, 4, 4) || '-' || SUBSTRING(month, 1, 2)
        WHEN month LIKE '____/__'  THEN SUBSTRING(month, 1, 4) || '-' || SUBSTRING(month, 6, 2)
        WHEN month LIKE 'Jan-%'    THEN REPLACE(month, 'Jan-', '2023-01')
        WHEN month LIKE 'January%' THEN '2023-01'
        WHEN month LIKE '__-__'    THEN '20' || SUBSTRING(month, 1, 2) || '-' || SUBSTRING(month, 4, 2)
        ELSE NULL
    END                                             AS month,
    monthly_revenue,
    cash_outflow,
    burn_rate,
    churn_rate,
    lead_time_days,
    headcount,
    cash_flow_flag,
    churn_flag,
    lead_time_flag,
    risk_score
FROM smb_raw
WHERE
    monthly_revenue  > 0
    AND monthly_revenue  < 1000000
    AND (churn_rate     IS NULL OR churn_rate    <= 1)
    AND (lead_time_days IS NULL OR lead_time_days > 0)
    AND (headcount      IS NULL OR headcount      > 0)
    AND (burn_rate      IS NULL OR burn_rate      <= 2)
ORDER BY business_id, month;


-- ------------------------------------------------------------
-- STEP 3: Post-clean validation
-- All invalid value checks should return zero
-- ------------------------------------------------------------
SELECT
    COUNT(*) FILTER (WHERE lead_time_days < 0)        AS negative_lead_times,
    COUNT(*) FILTER (WHERE churn_rate > 1)             AS invalid_churn,
    COUNT(*) FILTER (WHERE headcount <= 0)             AS invalid_headcount,
    COUNT(*) FILTER (WHERE burn_rate > 2)              AS extreme_burn_rate,
    COUNT(*) FILTER (WHERE monthly_revenue > 1000000)  AS extreme_revenue
FROM smb_diagnostic;


-- ------------------------------------------------------------
-- STEP 4: Confirm casing is standardised
-- Each industry and region should appear exactly once
-- ------------------------------------------------------------
SELECT industry, COUNT(*) AS occurrences
FROM smb_diagnostic
GROUP BY industry
ORDER BY industry;

SELECT region, COUNT(*) AS occurrences
FROM smb_diagnostic
GROUP BY region
ORDER BY region;


-- ------------------------------------------------------------
-- STEP 5: Confirm all dates are in YYYY-MM format
-- Should return zero rows
-- ------------------------------------------------------------
SELECT month, COUNT(*) AS occurrences
FROM smb_diagnostic
WHERE month NOT LIKE '____-__'
GROUP BY month
ORDER BY occurrences DESC;


-- ------------------------------------------------------------
-- STEP 6: Final dataset summary
-- ------------------------------------------------------------
SELECT
    COUNT(*)                           AS total_rows,
    COUNT(DISTINCT business_id)        AS unique_businesses,
    COUNT(DISTINCT industry)           AS unique_industries,
    COUNT(DISTINCT region)             AS unique_regions,
    MIN(month)                         AS earliest_month,
    MAX(month)                         AS latest_month,
    ROUND(AVG(risk_score)::NUMERIC, 2) AS avg_risk_score
FROM smb_diagnostic;


-- ------------------------------------------------------------
-- CLEAN TABLE SUMMARY
-- Results from smb_diagnostic:
--   Total rows:          232,941
--   Unique businesses:    10,000
--   Unique industries:        11
--   Unique regions:            5
--   Date range:      2023-01 to 2024-12
--   Avg risk score:         8.38
-- ============================================================
