"""
SMB Diagnostic Engine — Synthetic Dataset Generator
=====================================================
Generates 10,000 SMB businesses x 24 monthly snapshots = 240,000 rows,
then injects realistic data quality issues to simulate a real-world
messy dataset ready for SQL cleaning and validation.

Pipeline:
  Step 1 — Generate clean synthetic data
  Step 2 — Inject data quality imperfections
  Step 3 — Save final messy dataset as smb_raw_messy.csv

Data quality issues injected:
  1. Nulls                — missing values across 5 key columns
  2. Duplicates           — repeated records from multiple source systems
  3. Outliers             — extreme revenue and burn rate values
  4. Formatting           — inconsistent casing in industry & region
  5. Invalid values       — negative lead times, churn > 1, bad headcount
  6. Date format errors   — malformed month strings from mixed systems
  7. Whitespace           — leading/trailing spaces in string columns

Author : Oceana O'Dean
Project: SMB Diagnostic Engine
Tech   : Python 3 · pandas · numpy
"""

import numpy as np
import pandas as pd
from datetime import date

# ── Seeds ─────────────────────────────────────────────────────────────────────
GEN_SEED  = 42
DIRT_SEED = 99
rng_gen   = np.random.default_rng(GEN_SEED)
rng_dirt  = np.random.default_rng(DIRT_SEED)

# ── Constants ─────────────────────────────────────────────────────────────────
N_BUSINESSES = 10_000
N_MONTHS     = 24
START_DATE   = date(2023, 1, 1)
OUTPUT_FILE  = "smb_raw_messy.csv"

# Realistic US SMB industry distribution
INDUSTRIES = {
    "Retail":                0.18,
    "Food & Beverage":       0.15,
    "Professional Services": 0.13,
    "Healthcare":            0.10,
    "Construction":          0.09,
    "Technology":            0.08,
    "Manufacturing":         0.07,
    "Real Estate":           0.06,
    "Transportation":        0.06,
    "Education":             0.05,
    "Entertainment":         0.03,
}

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]

# Industry-level monthly revenue baselines (USD)
REVENUE_BASE = {
    "Retail":                55_000,
    "Food & Beverage":       42_000,
    "Professional Services": 80_000,
    "Healthcare":           110_000,
    "Construction":          95_000,
    "Technology":           120_000,
    "Manufacturing":         88_000,
    "Real Estate":           70_000,
    "Transportation":        60_000,
    "Education":             45_000,
    "Entertainment":         35_000,
}

# Seasonality multipliers by month (0=Jan … 11=Dec)
SEASONALITY = np.array([0.88, 0.85, 0.92, 0.95, 1.00, 1.03,
                        1.05, 1.04, 1.02, 1.06, 1.15, 1.25])


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — GENERATE CLEAN SYNTHETIC DATA
# ══════════════════════════════════════════════════════════════════════════════

def make_business(biz_id):
    """Generate a stable profile for one SMB."""
    industry    = rng_gen.choice(list(INDUSTRIES.keys()),
                                 p=list(INDUSTRIES.values()))
    region      = rng_gen.choice(REGIONS)
    base_rev    = REVENUE_BASE[industry]
    firm_factor = rng_gen.lognormal(mean=0, sigma=0.35)
    health_drift = rng_gen.choice(
        [-0.008, -0.003, 0.002, 0.005, 0.010],
        p=[0.08, 0.12, 0.35, 0.30, 0.15]
    )
    base_headcount = max(2, int(base_rev / 12_000 * firm_factor))
    return {
        "business_id":    f"SMB-{biz_id:05d}",
        "industry":       industry,
        "region":         region,
        "base_rev":       base_rev * firm_factor,
        "health_drift":   health_drift,
        "base_headcount": base_headcount,
    }


def make_monthly_row(profile, month_idx):
    """Generate one monthly snapshot for a business."""
    mo     = START_DATE.month - 1 + month_idx
    season = SEASONALITY[mo % 12]
    drift  = (1 + profile["health_drift"]) ** month_idx

    revenue      = max(500, profile["base_rev"] * season * drift
                       * rng_gen.lognormal(mean=0, sigma=0.08))
    outflow_ratio = rng_gen.uniform(0.75, 1.15)
    cash_outflow  = revenue * outflow_ratio
    burn_rate     = (cash_outflow - revenue) / revenue

    base_churn  = rng_gen.uniform(0.02, 0.12)
    churn_bump  = max(0, burn_rate * 0.3)
    churn_rate  = min(0.60, base_churn + churn_bump + rng_gen.normal(0, 0.01))

    base_lead   = rng_gen.uniform(3, 45)
    lead_shock  = rng_gen.choice([0, 10, 25], p=[0.80, 0.14, 0.06])
    lead_time   = max(1, base_lead + lead_shock * max(0, burn_rate))

    headcount   = max(1, int(profile["base_headcount"]
                             * (1 + profile["health_drift"] * month_idx / 2)
                             + rng_gen.normal(0, 0.5)))

    cash_flow_flag = int(burn_rate  >  0.10)
    churn_flag     = int(churn_rate >  0.15)
    lead_time_flag = int(lead_time  > 30)

    risk_score = round(
        (burn_rate  * 0.50 +
         churn_rate * 0.30 +
         (lead_time / 60) * 0.20) * 100, 2
    )
    risk_score = max(0, min(100, risk_score))

    yr  = START_DATE.year  + (START_DATE.month - 1 + month_idx) // 12
    mon = (START_DATE.month - 1 + month_idx) % 12 + 1
    month_label = f"{yr}-{mon:02d}"

    return {
        "business_id":    profile["business_id"],
        "industry":       profile["industry"],
        "region":         profile["region"],
        "month":          month_label,
        "monthly_revenue":round(revenue, 2),
        "cash_outflow":   round(cash_outflow, 2),
        "burn_rate":      round(burn_rate, 4),
        "churn_rate":     round(churn_rate, 4),
        "lead_time_days": round(lead_time, 1),
        "headcount":      headcount,
        "cash_flow_flag": cash_flow_flag,
        "churn_flag":     churn_flag,
        "lead_time_flag": lead_time_flag,
        "risk_score":     risk_score,
    }


print("=" * 60)
print("SMB Diagnostic Engine — Dataset Generator")
print("=" * 60)
print(f"\nStep 1: Generating {N_BUSINESSES:,} businesses x "
      f"{N_MONTHS} months = {N_BUSINESSES * N_MONTHS:,} rows...")

profiles = [make_business(i) for i in range(1, N_BUSINESSES + 1)]
rows     = [make_monthly_row(p, m)
            for p in profiles for m in range(N_MONTHS)]
df       = pd.DataFrame(rows)

print(f"Clean dataset shape: {df.shape[0]:,} rows x {df.shape[1]} columns")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — INJECT DATA QUALITY IMPERFECTIONS
# ══════════════════════════════════════════════════════════════════════════════

print("\nStep 2: Injecting data quality issues...")
total_rows = len(df)

# ── 1. Nulls ──────────────────────────────────────────────────────────────────
print("\n  [1] Nulls")
null_targets = {
    "monthly_revenue": 0.012,
    "churn_rate":      0.018,
    "lead_time_days":  0.022,
    "headcount":       0.009,
    "cash_outflow":    0.008,
}
total_nulls = 0
for col, rate in null_targets.items():
    n   = int(total_rows * rate)
    idx = rng_dirt.choice(total_rows, size=n, replace=False)
    df.loc[idx, col] = np.nan
    total_nulls += n
    print(f"      {col}: {n:,} nulls ({rate*100:.1f}%)")

# ── 2. Duplicates ─────────────────────────────────────────────────────────────
print("\n  [2] Duplicates")
n_dupes  = int(total_rows * 0.005)
dupe_idx = rng_dirt.choice(total_rows, size=n_dupes, replace=False)
dupes    = df.iloc[dupe_idx].copy()
df       = pd.concat([df, dupes], ignore_index=True)
print(f"      {n_dupes:,} duplicate rows injected")

# ── 3. Outliers ───────────────────────────────────────────────────────────────
print("\n  [3] Outliers")
n_rev_out  = int(total_rows * 0.003)
rev_idx    = rng_dirt.choice(total_rows, size=n_rev_out, replace=False)
df.loc[rev_idx, "monthly_revenue"] = rng_dirt.uniform(
    2_000_000, 9_500_000, size=n_rev_out)
print(f"      monthly_revenue: {n_rev_out:,} extreme values (2M–9.5M)")

n_burn_out = int(total_rows * 0.002)
burn_idx   = rng_dirt.choice(total_rows, size=n_burn_out, replace=False)
df.loc[burn_idx, "burn_rate"] = rng_dirt.uniform(2.5, 8.0, size=n_burn_out)
print(f"      burn_rate: {n_burn_out:,} extreme values (2.5–8.0)")

# ── 4. Formatting inconsistencies ─────────────────────────────────────────────
print("\n  [4] Casing inconsistencies")

def corrupt_case(series, rate, rng):
    idx       = rng.choice(len(series), size=int(len(series) * rate),
                            replace=False)
    corrupted = series.copy()
    for i in idx:
        choice = rng.integers(0, 3)
        val    = str(corrupted.iloc[i])
        corrupted.iloc[i] = (val.upper() if choice == 0
                             else val.lower() if choice == 1
                             else val.swapcase())
    return corrupted

df["industry"] = corrupt_case(df["industry"], 0.08, rng_dirt)
df["region"]   = corrupt_case(df["region"],   0.06, rng_dirt)
print(f"      industry: ~8% inconsistent casing")
print(f"      region:   ~6% inconsistent casing")

# ── 5. Invalid values ─────────────────────────────────────────────────────────
print("\n  [5] Invalid values")

n_neg_lead = int(total_rows * 0.004)
neg_idx    = rng_dirt.choice(total_rows, size=n_neg_lead, replace=False)
df.loc[neg_idx, "lead_time_days"] = rng_dirt.uniform(
    -30, -1, size=n_neg_lead).round(1)
print(f"      lead_time_days: {n_neg_lead:,} negative values")

n_bad_churn = int(total_rows * 0.003)
churn_idx   = rng_dirt.choice(total_rows, size=n_bad_churn, replace=False)
df.loc[churn_idx, "churn_rate"] = rng_dirt.uniform(
    1.1, 3.5, size=n_bad_churn).round(4)
print(f"      churn_rate: {n_bad_churn:,} values > 1")

n_bad_hc = int(total_rows * 0.002)
hc_idx   = rng_dirt.choice(total_rows, size=n_bad_hc, replace=False)
df.loc[hc_idx, "headcount"] = rng_dirt.integers(-5, 1, size=n_bad_hc)
print(f"      headcount: {n_bad_hc:,} zero/negative values")

# ── 6. Date format errors ─────────────────────────────────────────────────────
print("\n  [6] Date format errors")
bad_formats = ["01/2023", "2023/01", "Jan-2023", "January 2023", "23-01"]
n_date_err  = int(total_rows * 0.005)
date_idx    = rng_dirt.choice(total_rows, size=n_date_err, replace=False)
df.loc[date_idx, "month"] = [
    bad_formats[rng_dirt.integers(0, len(bad_formats))]
    for _ in range(n_date_err)
]
print(f"      month: {n_date_err:,} malformed date strings")

# ── 7. Whitespace ─────────────────────────────────────────────────────────────
print("\n  [7] Whitespace issues")
ws_total = 0
for col in ["business_id", "industry", "region"]:
    n_ws   = int(total_rows * 0.015)
    ws_idx = rng_dirt.choice(len(df), size=n_ws, replace=False)
    for i in ws_idx:
        choice = rng_dirt.integers(0, 3)
        val    = str(df.loc[i, col])
        df.loc[i, col] = ("  " + val if choice == 0
                          else val + "  " if choice == 1
                          else "  " + val + "  ")
    ws_total += n_ws
    print(f"      {col}: {n_ws:,} values with whitespace")

# ── Shuffle rows ──────────────────────────────────────────────────────────────
df = df.sample(frac=1, random_state=DIRT_SEED).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — SAVE OUTPUT
# ══════════════════════════════════════════════════════════════════════════════

df.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 60)
print(f"Done. Saved to '{OUTPUT_FILE}'")
print(f"Final shape: {len(df):,} rows x {len(df.columns)} columns")
print("\nData quality issues summary:")
print(f"  Nulls injected:          {total_nulls:,} cells across 5 columns")
print(f"  Duplicate rows:          {n_dupes:,}")
print(f"  Revenue outliers:        {n_rev_out:,}")
print(f"  Burn rate outliers:      {n_burn_out:,}")
print(f"  Negative lead times:     {n_neg_lead:,}")
print(f"  Invalid churn values:    {n_bad_churn:,}")
print(f"  Invalid headcount:       {n_bad_hc:,}")
print(f"  Date format errors:      {n_date_err:,}")
print(f"  Whitespace issues:       {ws_total:,} cells")
print("=" * 60)
