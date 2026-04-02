"""
SMB Diagnostic Engine
Script : db_connect.py
Purpose: Connect to PostgreSQL and load smb_diagnostic into a DataFrame
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

# ── Create connection ──────────────────────────────────────────
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ── Load smb_diagnostic into DataFrame ────────────────────────
print("Connecting to database...")
df = pd.read_sql("SELECT * FROM smb_diagnostic", engine)

# ── Confirm load ───────────────────────────────────────────────
print(f"Successfully loaded {len(df):,} rows x {len(df.columns)} columns")
print(f"\nColumns: {list(df.columns)}")
print(f"\nFirst 3 rows:")
print(df.head(3))


