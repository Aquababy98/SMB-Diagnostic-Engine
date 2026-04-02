-- ============================================================
-- SMB Diagnostic Engine
-- Script : 01_validation.sql
-- Purpose: Audit smb_raw for data quality issues before cleaning
-- Author : Oceana O'Dean
-- ============================================================


-- ------------------------------------------------------------
-- STEP 1: Baseline row count
-- Expected: 241,200
-- ------------------------------------------------------------
SELECT COUNT(*) AS total_rows
FROM smb_raw;


-- ------------------------------------------------------------
-- STEP 2: Duplicate detection
-- Identifies business/month combinations appearing more than once
-- Root cause: double-entry from multiple source systems
-- ------------------------------------------------------------
SELECT
    business_id,
    month,
    COUNT(*) AS occurrences
FROM smb_raw
GROUP BY business_id, month
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;


-- ------------------------------------------------------------
-- STEP 3: Null audit across all columns
-- Formula: COUNT(*) counts nulls, COUNT(col) skips them
-- The difference = null count per column
-- ------------------------------------------------------------
SELECT
    COUNT(*) - COUNT(business_id)       AS null_business_id,
    COUNT(*) - COUNT(industry)          AS null_industry,
    COUNT(*) - COUNT(region)            AS null_region,
    COUNT(*) - COUNT(month)             AS null_month,
    COUNT(*) - COUNT(monthly_revenue)   AS null_monthly_revenue,
    COUNT(*) - COUNT(cash_outflow)      AS null_cash_outflow,
    COUNT(*) - COUNT(burn_rate)         AS null_burn_rate,
    COUNT(*) - COUNT(churn_rate)        AS null_churn_rate,
    COUNT(*) - COUNT(lead_time_days)    AS null_lead_time_days,
    COUNT(*) - COUNT(headcount)         AS null_headcount,
    COUNT(*) - COUNT(cash_flow_flag)    AS null_cash_flow_flag,
    COUNT(*) - COUNT(churn_flag)        AS null_churn_flag,
    COUNT(*) - COUNT(lead_time_flag)    AS null_lead_time_flag,
    COUNT(*) - COUNT(risk_score)        AS null_risk_score
FROM smb_raw;


-- ------------------------------------------------------------
-- STEP 4: Invalid value detection
-- Checks business rules defined in DATA_DICTIONARY.md
-- ------------------------------------------------------------
SELECT
    COUNT(*) FILTER (WHERE lead_time_days < 0)        AS negative_lead_times,
    COUNT(*) FILTER (WHERE churn_rate > 1)             AS invalid_churn,
    COUNT(*) FILTER (WHERE headcount <= 0)             AS invalid_headcount,
    COUNT(*) FILTER (WHERE burn_rate > 2)              AS extreme_burn_rate,
    COUNT(*) FILTER (WHERE monthly_revenue > 1000000)  AS extreme_revenue
FROM smb_raw;


-- ------------------------------------------------------------
-- STEP 5: Casing inconsistencies in categorical columns
-- Expected: each industry/region should appear once per clean name
-- Root cause: data sourced from multiple systems with no casing standard
-- ------------------------------------------------------------
SELECT
    industry,
    COUNT(*) AS occurrences
FROM smb_raw
GROUP BY industry
ORDER BY industry;

SELECT
    region,
    COUNT(*) AS occurrences
FROM smb_raw
GROUP BY region
ORDER BY region;


-- ------------------------------------------------------------
-- STEP 6: Date format errors
-- Valid format is YYYY-MM (e.g. 2023-01)
-- Root cause: data exported from mixed regional systems
-- ------------------------------------------------------------
SELECT
    month,
    COUNT(*) AS occurrences
FROM smb_raw
WHERE month NOT LIKE '____-__'
GROUP BY month
ORDER BY occurrences DESC;


-- ------------------------------------------------------------
-- VALIDATION SUMMARY
-- Results from smb_raw audit:
--   Total rows:             241,200
--   Duplicate records:        1,179 business/month combinations
--   Null cells:              16,594 across 5 columns
--   Negative lead times:        960 rows
--   Invalid churn (>1):         720 rows
--   Invalid headcount (<=0):    480 rows
--   Extreme burn rate (>2):     480 rows
--   Extreme revenue (>1M):      720 rows
--   Date format errors:       1,200 rows
--   Casing inconsistencies: ~8% industry, ~6% region
-- All issues resolved in 02_clean_table.sql
-- ============================================================
