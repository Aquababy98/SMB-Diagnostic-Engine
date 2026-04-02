"""
SMB Diagnostic Engine
Script : risk_scoring.py
Purpose: Calculate weighted propensity-to-fail scores for each SMB
Author : Oceana O'Dean
"""

import pandas as pd
from sqlalchemy import create_engine

# ── Connection settings ────────────────────────────────────────
DB_USER     = "postgres"
DB_PASSWORD = "Heliconius$35"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "smb_analytics"

# ── Load clean data ────────────────────────────────────────────
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("Loading smb_diagnostic...")
df = pd.read_sql("SELECT * FROM smb_diagnostic", engine)
print(f"Loaded {len(df):,} rows")

# ── Weighted risk score ────────────────────────────────────────
# Weights derived from US Chamber of Commerce SMB failure research:
#   Cash flow  50% — accounts for 82% of SMB failures
#   Churn      30% — accounts for 42% of SMB failures
#   Lead time  20% — proxy for labor & productivity gap

print("\nCalculating propensity scores...")

df["risk_score_v2"] = (
    df["burn_rate"].fillna(0)        * 0.50 +
    df["churn_rate"].fillna(0)       * 0.30 +
    (df["lead_time_days"].fillna(0) / 60) * 0.20
) * 100

# Clip to valid range 0-100
df["risk_score_v2"] = df["risk_score_v2"].clip(0, 100).round(2)

# ── Summary statistics ─────────────────────────────────────────
print(f"\nRisk score summary:")
print(df["risk_score_v2"].describe().round(2))

# ── Top 10 highest risk businesses ────────────────────────────
print(f"\nTop 10 highest risk businesses:")
top10 = (df.groupby("business_id")["risk_score_v2"]
           .mean()
           .sort_values(ascending=False)
           .head(10)
           .reset_index())
top10.columns = ["business_id", "avg_risk_score_v2"]
top10["avg_risk_score_v2"] = top10["avg_risk_score_v2"].round(2)
print(top10.to_string(index=False))

# ── Export scored dataset ──────────────────────────────────────
print("\nExporting scored_smbs.csv...")
df.to_csv("scored_smbs.csv", index=False)
print(f"Done — {len(df):,} rows saved to scored_smbs.csv")
