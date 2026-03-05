# agents/tools/data_tools.py
# Tools wrapping the Data/ML layer (forecasts + anomaly detection).
#
# When running in-process with the backend, calls intelligence modules directly.
# When running standalone, falls back to HTTP calls.

import os
import logging

logger = logging.getLogger(__name__)

DATA_URL = os.getenv("DATA_API_URL", "http://localhost:3001")

# ─── Safe defaults when data layer is unavailable ────────────
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


def _try_direct_forecast(supplier_id: str):
    """Try to call the intelligence forecast module directly."""
    try:
        from intelligence.forecast import run_forecast_for_supplier
        return run_forecast_for_supplier(supplier_id)
    except ImportError:
        return None


def _try_direct_anomaly(supplier_id: str):
    """Try to call the intelligence anomaly module directly."""
    try:
        from intelligence.anomaly import anomaly_score_for_supplier
        return anomaly_score_for_supplier(supplier_id)
    except ImportError:
        return None


def get_forecast(supplier_id: str) -> dict:
    """Get 7-day delay forecast for a supplier.
    Returns: {supplier_id, forecast_date, predicted_delay,
              lower_ci, upper_ci, forecast_confidence, trend}"""
    try:
        # ── Direct in-process access ──
        result = _try_direct_forecast(supplier_id)
        if result is not None:
            return result

        # ── Fallback: HTTP call ──
        import httpx
        resp = httpx.get(f"{DATA_URL}/api/forecasts/{supplier_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Forecast fetch failed for {supplier_id}: {e} — using safe default")
        return {**_DEFAULT_FORECAST, "supplier_id": supplier_id}


def get_anomaly_status(supplier_id: str) -> dict:
    """Get anomaly ensemble result for a supplier.
    Returns: {supplier_id, date, anomaly_flag, votes,
              zscore_val, mad_val, percentile_val}"""
    try:
        # ── Direct in-process access ──
        result = _try_direct_anomaly(supplier_id)
        if result is not None:
            return result

        # ── Fallback: HTTP call ──
        import httpx
        resp = httpx.get(f"{DATA_URL}/api/anomalies/{supplier_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Anomaly fetch failed for {supplier_id}: {e} — using safe default")
        return {**_DEFAULT_ANOMALY, "supplier_id": supplier_id}
