"""
Generate synthetic timeseries data for 10 suppliers.
Each supplier has 180 days of daily delay data with varying risk profiles.
Matches the supplier IDs from db/seed.sql.

Usage: python data/generate_data.py
Output: timeseries.csv in the project root
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

# 10 suppliers with different delay profiles (base delay, volatility)
suppliers = {
    "S1":  {"name": "AlphaForge Industries",   "base": 6.0, "vol": 2.5, "trend": 0.02},    # HIGH risk, worsening
    "S2":  {"name": "BetaSteel Corporation",    "base": 2.0, "vol": 0.5, "trend": 0.0},     # LOW risk, stable
    "S3":  {"name": "GammaCast Manufacturing",  "base": 3.0, "vol": 1.0, "trend": 0.0},     # LOW-MED risk
    "S4":  {"name": "DeltaSteel Corp",          "base": 4.5, "vol": 1.5, "trend": 0.01},    # MED risk, slight worsening
    "S5":  {"name": "EpsilonCast Systems",      "base": 3.5, "vol": 1.2, "trend": 0.0},     # MED risk, stable
    "S6":  {"name": "ZetaAlloy Solutions",      "base": 1.5, "vol": 0.3, "trend": 0.0},     # VERY LOW risk
    "S7":  {"name": "EtaPrecision Parts",       "base": 2.5, "vol": 0.8, "trend": -0.005},  # LOW risk, improving
    "S8":  {"name": "ThetaForge Ltd",           "base": 5.0, "vol": 2.0, "trend": 0.015},   # HIGH risk, worsening
    "S9":  {"name": "IotaMetals Inc",           "base": 2.0, "vol": 0.6, "trend": 0.005},   # LOW risk, slight trend
    "S10": {"name": "KappaComponents Global",   "base": 7.0, "vol": 3.0, "trend": 0.03},    # VERY HIGH risk, worsening
}

dates = pd.date_range(end=pd.Timestamp.today(), periods=180)

rows = []
for supplier_id, profile in suppliers.items():
    for i, d in enumerate(dates):
        # Base + trend + noise + occasional spikes
        delay = (
            profile["base"]
            + profile["trend"] * i
            + np.random.normal(0, profile["vol"])
        )
        # Add occasional spikes for high-risk suppliers
        if profile["vol"] > 1.5 and np.random.random() < 0.05:
            delay += np.random.uniform(3, 8)

        rows.append({
            "supplier_id": supplier_id,
            "date": d.strftime("%Y-%m-%d"),
            "delay_days": max(0, round(delay, 2)),
        })

df = pd.DataFrame(rows)

# Save to project root
output_path = Path(__file__).parent.parent / "timeseries.csv"
df.to_csv(output_path, index=False)

print(f"Dataset generated: {len(df)} rows for {len(suppliers)} suppliers")
print(f"Saved to: {output_path}")
print(f"\nSupplier delay profiles:")
for sid in sorted(suppliers.keys(), key=lambda x: int(x[1:])):
    sdf = df[df["supplier_id"] == sid]
    print(f"  {sid} ({suppliers[sid]['name'][:25]:25s}): "
          f"mean={sdf['delay_days'].mean():.1f}, "
          f"std={sdf['delay_days'].std():.1f}, "
          f"max={sdf['delay_days'].max():.1f}")
