# Migration Notes — PostgreSQL to Azure SQL

**Project:** SMB Diagnostic Engine  
**Author:** Oceana O'Dean  
**Purpose:** Documents the syntax differences between PostgreSQL and Azure SQL (T-SQL) for anyone running these scripts in an Azure environment.

---

## Overview

All SQL scripts in this project were written and tested in PostgreSQL 16. Azure SQL uses T-SQL (Transact-SQL), Microsoft's SQL dialect. The two are approximately 90% compatible for the queries used in this project, but the following four differences must be addressed before running in Azure.

---

## Difference 1 — Case-insensitive matching

**PostgreSQL:**
```sql
WHERE industry ILIKE 'retail'
```

**Azure SQL (T-SQL):**
```sql
WHERE industry LIKE 'retail'
```

**Explanation:** PostgreSQL's `ILIKE` operator performs case-insensitive pattern matching. Azure SQL's `LIKE` is case-insensitive by default when using a case-insensitive collation (which is the Azure SQL default). Simply replace `ILIKE` with `LIKE` in all WHERE clauses.

---

## Difference 2 — Auto-increment columns

**PostgreSQL:**
```sql
CREATE TABLE smb_raw (
    id SERIAL PRIMARY KEY
);
```

**Azure SQL (T-SQL):**
```sql
CREATE TABLE smb_raw (
    id INT IDENTITY(1,1) PRIMARY KEY
);
```

**Explanation:** PostgreSQL uses `SERIAL` as a shorthand for an auto-incrementing integer. Azure SQL uses `IDENTITY(1,1)` where the first argument is the starting value and the second is the increment. This project does not use auto-increment columns but this is the most common difference encountered when migrating table definitions.

---

## Difference 3 — Date truncation

**PostgreSQL:**
```sql
SELECT DATE_TRUNC('month', created_at) AS month
FROM smb_raw;
```

**Azure SQL (T-SQL):**
```sql
SELECT DATETRUNC(month, created_at) AS month
FROM smb_raw;
```

**Explanation:** PostgreSQL uses `DATE_TRUNC('month', column)` with the date part as a quoted string. Azure SQL uses `DATETRUNC(month, column)` with the date part as an unquoted keyword. Note that `DATETRUNC` was introduced in Azure SQL in 2022 — older versions should use `FORMAT(created_at, 'yyyy-MM')` instead.

---

## Difference 4 — Type casting

**PostgreSQL:**
```sql
SELECT ROUND(AVG(risk_score)::NUMERIC, 2) AS avg_risk_score
FROM smb_diagnostic;
```

**Azure SQL (T-SQL):**
```sql
SELECT ROUND(AVG(CAST(risk_score AS NUMERIC)), 2) AS avg_risk_score
FROM smb_diagnostic;
```

**Explanation:** PostgreSQL uses the `::` shorthand for casting data types (e.g. `value::NUMERIC`). Azure SQL does not support this syntax — use the standard `CAST(value AS type)` function instead. The `CAST()` function works in both environments so using it consistently is the safest approach for cross-platform compatibility.

---

## Quick Reference

| Feature | PostgreSQL | Azure SQL (T-SQL) |
|---|---|---|
| Case-insensitive match | `ILIKE` | `LIKE` |
| Auto-increment | `SERIAL` | `IDENTITY(1,1)` |
| Date truncation | `DATE_TRUNC('month', col)` | `DATETRUNC(month, col)` |
| Type casting | `value::TYPE` | `CAST(value AS TYPE)` |

---

## Scripts Requiring Changes for Azure

| Script | Change Required |
|---|---|
| `01_validation.sql` | Replace `::NUMERIC` with `CAST(... AS NUMERIC)` |
| `02_clean_table.sql` | Replace `::NUMERIC` with `CAST(... AS NUMERIC)` |

All other syntax in this project is compatible with both PostgreSQL and Azure SQL without modification.

---

*SMB Diagnostic Engine · Oceana O'Dean · 2024*
