# agents/tools/data_tools.py
# CrewAI tools wrapping P5's FastAPI (forecasts + anomalies).
# Uses safe defaults when P5's service on :8001 is unreachable.
#
# P3→P4 CONTRACT CHECK: P5's current API uses /forecast and /anomaly
# (global endpoints), not per-supplier /api/forecasts/:id and /api/anomalies/:id.
# P5 must add per-supplier endpoints. See INTEGRATION_NOTES.md.

import httpx
import os
import logging

logger = logging.getLogger(__name__)

DATA_URL = os.getenv("DATA_API_URL", "http://localhost:3001")

# ─── Safe defaults when P5 is offline ────────────────────────
_DEFAULT_FORECAST = {
    "supplier_id": "unknown",
    "forecast_date": "2026-03-04",
    "predicted_delay": 3.0,
    "lower_ci": 2.0,
    "upper_ci": 5.0,
    "forecast_confidence": 0.7,
    "trend": "STABLE",
}

_DEFAULT_ANOMALY = {
    "supplier_id": "unknown",
    "date": "2026-03-04",
    "anomaly_flag": False,
    "votes": 0,
    "zscore_val": 0.0,
    "mad_val": 0.0,
    "percentile_val": 0.5,
}


def get_forecast(supplier_id: str) -> dict:
    """Get P5's AutoARIMA 7-day delay forecast for a supplier.
    Returns: {supplier_id, forecast_date, predicted_delay,
              lower_ci, upper_ci, forecast_confidence}"""
    try:
        resp = httpx.get(f"{DATA_URL}/api/forecasts/{supplier_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"Forecast fetch failed for {supplier_id}: {e} — using safe default")
        return {**_DEFAULT_FORECAST, "supplier_id": supplier_id}


def get_anomaly_status(supplier_id: str) -> dict:
    """Get P5's anomaly ensemble result for a supplier.
    Returns: {supplier_id, date, anomaly_flag, votes,
              zscore_val, mad_val, percentile_val}"""
    try:
        resp = httpx.get(f"{DATA_URL}/api/anomalies/{supplier_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"Anomaly fetch failed for {supplier_id}: {e} — using safe default")
        return {**_DEFAULT_ANOMALY, "supplier_id": supplier_id}
