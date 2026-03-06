# agents/supplier_history_agent.py
# Agent 3: Supplier History Agent
# Pulls forecast + anomaly data from P5, derives trend and risk index.

import logging
from contracts.schemas import HistoryResult, AgentState
from agents.tools.data_tools import get_forecast, get_anomaly_status
from agents.tools.erp_tools import get_parts_by_supplier
from agents.tools.audit_tools import log_audit_decision

logger = logging.getLogger(__name__)


def _derive_forecast_trend(forecast: dict) -> str:
    """
    forecast_trend logic — four tiers:

    WORSENING  — actively getting worse (predicted high AND wide CI = growing uncertainty)
    ELEVATED   — chronically high in absolute terms even if not spiking.
                 A supplier consistently at 7+ days is a supply chain risk
                 regardless of whether the trend is changing.
    IMPROVING  — predicted delay is low and confidence is high
    STABLE     — everything else (low/medium delay, moderate uncertainty)
    """
    predicted = forecast.get("predicted_delay", 3.0)
    upper = forecast.get("upper_ci", predicted + 1)
    lower = forecast.get("lower_ci", predicted - 1)
    ci_width = upper - lower

    # Actively deteriorating: high delay AND growing uncertainty
    if predicted > 5 and ci_width > 4:
        return "WORSENING"
    # Chronically elevated: absolute delay is bad even if trend is flat.
    # This catches suppliers who are always late — their "stable" 8-day delay
    # is still a structural supply chain problem.
    elif predicted >= 7:
        return "ELEVATED"
    elif predicted < 2 and ci_width < 2:
        return "IMPROVING"
    else:
        return "STABLE"


def _derive_forecast_confidence(forecast: dict) -> float:
    """
    forecast_confidence (from AGENTS.md Part 7):
    confidence = 1 - (upper_ci - lower_ci) / max_range
    where max_range = 14 days (reasonable max delay)
    Clamped to [0.0, 1.0].
    """
    upper = forecast.get("upper_ci", 5.0)
    lower = forecast.get("lower_ci", 2.0)
    max_range = 14.0
    confidence = 1.0 - (upper - lower) / max_range
    return max(0.0, min(1.0, confidence))


def _compute_risk_index(
    forecast_confidence: float,
    anomaly_votes: int,
    avg_delay: float,
) -> float:
    """
    Compute a risk index score (0-100) from available signals.
    Higher = riskier.
    """
    delay_factor = min(avg_delay / 10.0, 1.0) * 100  # 10 days = max risk
    confidence_factor = (1 - forecast_confidence) * 100
    anomaly_factor = (anomaly_votes / 3.0) * 100
    return round(0.4 * delay_factor + 0.3 * confidence_factor + 0.3 * anomaly_factor, 2)


def run_history_agent(state: AgentState) -> AgentState:
    """
    Agent 3: Supplier History.
    - Calls P5 forecast + anomaly endpoints (with safe defaults)
    - Derives trend, confidence, risk index
    - Returns HistoryResult
    """
    try:
        supplier_id = state.intake.supplier_id if state.intake else state.event_id
        delay_days = state.intake.delay_days if state.intake else 0

        # Step 1: Fetch forecast from P5
        forecast = get_forecast(supplier_id)

        # Step 2: Fetch anomaly status from P5
        anomaly = get_anomaly_status(supplier_id)

        # Step 3: Derive values
        forecast_trend = _derive_forecast_trend(forecast)
        forecast_confidence = _derive_forecast_confidence(forecast)
        anomaly_votes = anomaly.get("votes", 0)
        anomaly_flagged = anomaly.get("anomaly_flag", False)
        chronic_lateness = anomaly.get("chronic_lateness", False)
        avg_delay = forecast.get("predicted_delay", float(delay_days))

        # Step 4: Compute risk index — chronic lateness adds a floor to risk
        risk_index_score = _compute_risk_index(
            forecast_confidence, anomaly_votes, avg_delay
        )
        # Boost risk index for chronically late suppliers so they can't hide
        # behind a "STABLE" trend score when their absolute delay is bad
        if chronic_lateness:
            risk_index_score = min(100.0, risk_index_score + 20.0)

        result = HistoryResult(
            avg_delay_30d=round(avg_delay, 2),
            forecast_trend=forecast_trend,
            forecast_confidence=round(forecast_confidence, 4),
            anomaly_votes=anomaly_votes,
            anomaly_flagged=anomaly_flagged,
            risk_index_score=round(risk_index_score, 2),
            chronic_lateness=chronic_lateness,
        )

        # Step 5: Log audit
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="supplier_history_agent",
            inputs={
                "supplier_id": supplier_id,
                "forecast_raw": forecast,
                "anomaly_raw": anomaly,
            },
            outputs=result.model_dump(),
            confidence=forecast_confidence,
            rationale=(
                f"Forecast trend: {forecast_trend} (confidence: {forecast_confidence:.2f}). "
                f"Anomaly votes: {anomaly_votes}/3. Risk index: {risk_index_score:.1f}/100."
            ),
        )
        state.audit_entries.append(audit_entry)
        state.history = result
        return state

    except Exception as e:
        logger.error(f"History agent error: {e}")
        result = HistoryResult(
            avg_delay_30d=3.0,
            forecast_trend="STABLE",
            forecast_confidence=0.5,
            anomaly_votes=0,
            anomaly_flagged=False,
            risk_index_score=30.0,
        )
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="supplier_history_agent",
            inputs={"error": str(e)},
            outputs=result.model_dump(),
            confidence=0.3,
            rationale=f"History agent error: {e}. Using conservative defaults.",
        )
        state.audit_entries.append(audit_entry)
        state.history = result
        return state
