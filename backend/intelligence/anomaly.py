"""
Anomaly detection module.
- anomaly_score(): global anomaly ratio (original from P5)
- anomaly_score_for_supplier(supplier_id): per-supplier ensemble-style result
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date

# Try multiple paths for the timeseries CSV
def _find_timeseries():
    candidates = [
        Path("timeseries.csv"),
        Path("data/timeseries.csv"),
        Path(__file__).parent.parent / "timeseries.csv",
        Path(__file__).parent.parent / "data" / "timeseries.csv",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def anomaly_score() -> float:
    """Global anomaly ratio across all suppliers (original P5 function)."""
    csv_path = _find_timeseries()
    if not csv_path:
        return 0.05  # safe default
    df = pd.read_csv(csv_path)
    z = (df["delay_days"] - df["delay_days"].mean()) / df["delay_days"].std()
    df["anomaly"] = (np.abs(z) > 2.5).astype(int)
    return float(df["anomaly"].mean())


def anomaly_score_for_supplier(supplier_id: str) -> dict:
    """Per-supplier anomaly detection using a 3-method ensemble:
    1. Z-score vs own history (>2.5 std) — detects sudden spikes
    2. MAD vs own history (>3.0) — robust spike detection
    3. Cross-supplier fleet percentile (>80th pctile of peer averages)
       — detects CHRONIC lateness that self-comparison misses entirely.
       A supplier always late by 10 days looks "normal" compared to itself
       but is clearly an outlier compared to the fleet.
    Returns votes (0-3) and individual method values.
    """
    csv_path = _find_timeseries()
    if not csv_path:
        return {
            "supplier_id": supplier_id,
            "date": date.today().isoformat(),
            "anomaly_flag": False,
            "votes": 0,
            "zscore_val": 0.0,
            "mad_val": 0.0,
            "percentile_val": 0.5,
            "chronic_lateness": False,
        }

    df = pd.read_csv(csv_path)

    # Map supplier_id to the format used in timeseries.csv
    supplier_map = _get_supplier_map()
    short_id = supplier_map.get(supplier_id, supplier_id)

    supplier_df = df[df["supplier_id"] == short_id]

    if supplier_df.empty:
        supplier_df = df[df["supplier_id"] == supplier_id]

    if supplier_df.empty or len(supplier_df) < 10:
        return {
            "supplier_id": supplier_id,
            "date": date.today().isoformat(),
            "anomaly_flag": False,
            "votes": 0,
            "zscore_val": 0.0,
            "mad_val": 0.0,
            "percentile_val": 0.5,
            "chronic_lateness": False,
        }

    delays = supplier_df["delay_days"].values
    latest = delays[-1] if len(delays) > 0 else 0

    # Method 1: Z-score vs own history — catches sudden spikes
    mean_val = np.mean(delays)
    std_val = np.std(delays)
    zscore_val = (latest - mean_val) / std_val if std_val > 0 else 0.0
    zscore_flag = abs(zscore_val) > 2.5

    # Method 2: MAD vs own history — robust spike detection
    median_val = np.median(delays)
    mad = np.median(np.abs(delays - median_val))
    mad_val = (latest - median_val) / (mad * 1.4826) if mad > 0 else 0.0
    mad_flag = abs(mad_val) > 3.0

    # Method 3: Cross-supplier fleet comparison — catches CHRONIC lateness.
    # A supplier that is always slow looks "normal" to methods 1 & 2 (their own
    # history is their baseline). This method compares each supplier's average
    # delay against ALL suppliers' averages. If this supplier is worse than 80%
    # of their peers on average, they are a structural problem — not just a spike.
    fleet_avg_per_supplier = df.groupby("supplier_id")["delay_days"].mean()
    supplier_avg = float(np.mean(delays))
    # What fraction of peer suppliers have a LOWER average delay than this one?
    percentile_val = float(np.mean(fleet_avg_per_supplier <= supplier_avg))
    # >0.80 = worse than 80% of suppliers on average = chronic underperformer
    percentile_flag = percentile_val > 0.80
    chronic_lateness = percentile_flag

    votes = int(zscore_flag) + int(mad_flag) + int(percentile_flag)

    return {
        "supplier_id": supplier_id,
        "date": date.today().isoformat(),
        "anomaly_flag": votes >= 2,
        "votes": votes,
        "zscore_val": round(float(zscore_val), 4),
        "mad_val": round(float(mad_val), 4),
        "percentile_val": round(float(percentile_val), 4),
        "chronic_lateness": bool(chronic_lateness),
    }


def _get_supplier_map() -> dict:
    """Map UUID supplier IDs to short IDs used in timeseries.csv."""
    return {
        "a1000000-0000-0000-0000-000000000001": "S1",
        "a1000000-0000-0000-0000-000000000002": "S2",
        "a1000000-0000-0000-0000-000000000003": "S3",
        "a1000000-0000-0000-0000-000000000004": "S4",
        "a1000000-0000-0000-0000-000000000005": "S5",
        "a1000000-0000-0000-0000-000000000006": "S6",
        "a1000000-0000-0000-0000-000000000007": "S7",
        "a1000000-0000-0000-0000-000000000008": "S8",
        "a1000000-0000-0000-0000-000000000009": "S9",
        "a1000000-0000-0000-0000-000000000010": "S10",
    }
