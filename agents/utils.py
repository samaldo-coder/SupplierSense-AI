# agents/utils.py
# LLM retry/validation utilities + deterministic scoring logic.
# Used by all 5 agents.

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from pydantic import BaseModel, ValidationError
import json
import os
import logging

logger = logging.getLogger(__name__)


# ─── OpenAI client (lazy init) ───────────────────────────────
_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        except Exception as e:
            logger.warning(f"OpenAI client init failed: {e}")
            _openai_client = None
    return _openai_client


# ─── LLM Call with Pydantic Validation ───────────────────────
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((ValueError, ValidationError)),
)
def call_llm_with_validation(prompt: str, schema: type[BaseModel]) -> BaseModel:
    """
    Call OpenAI and validate output against a Pydantic schema.
    Retries up to 3x with corrective prompt on validation failure.
    Raises ValueError if OpenAI is not configured.
    """
    client = _get_openai_client()
    if client is None:
        raise RuntimeError("OpenAI client not available — set OPENAI_API_KEY")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    raw = response.choices[0].message.content
    try:
        return schema.model_validate_json(raw)
    except ValidationError as e:
        corrective = (
            f"Your previous response failed Pydantic validation with error: {str(e)}\n"
            f"Raw response was: {raw}\n"
            f"Please fix and return valid JSON matching the required schema."
        )
        raise ValueError(corrective)


# ─── Composite Risk Score ────────────────────────────────────
def compute_composite_score(
    quality_sub_score: float,              # 0-100, from Agent 2
    forecast_confidence_in_stable: float,  # 0.0-1.0, from Agent 3
    anomaly_votes: int,                    # 0-3, from Agent 3 (P5 ensemble)
    risk_index_score: float,               # 0-100, from Agent 3
) -> float:
    """
    Composite risk score formula (from AGENTS.md Part 7).
    Higher score = higher risk = more likely to need HITL.
    Returns a float 0-100.
    """
    score = (
        0.35 * quality_sub_score
        + 0.25 * (1 - forecast_confidence_in_stable) * 100
        + 0.25 * (anomaly_votes / 3.0) * 100
        + 0.15 * risk_index_score
    )
    return max(0.0, min(100.0, score))


# ─── Escalation Rules ────────────────────────────────────────
def determine_action_and_hitl(
    composite_score: float,
    cert_valid: bool,
    financial_health: str,       # "GREEN" | "YELLOW" | "RED"
    forecast_trend: str,         # "WORSENING" | "ELEVATED" | "STABLE" | "IMPROVING"
    anomaly_votes: int,
    chronic_lateness: bool = False,
) -> tuple[str, bool]:
    """
    Escalation rules applied in priority order.
    Returns (action, hitl_required).
    """
    # Rule 1: Highest severity — VP escalation
    if financial_health == "RED" and not cert_valid:
        return "ESCALATE_TO_VP", True

    # Rule 2: Strong dual signal — Director escalation
    # ELEVATED treated the same as WORSENING — a supplier stuck at high delays
    # is as dangerous as one that is actively getting worse
    if forecast_trend in ("WORSENING", "ELEVATED") and anomaly_votes >= 2:
        return "ESCALATE_TO_DIRECTOR", True

    # Rule 3: Score-based threshold
    if composite_score >= 70:
        return "ESCALATE_TO_DIRECTOR", True

    # Rule 4: Cert alone forces review
    if not cert_valid:
        return "ESCALATE_TO_DIRECTOR", True

    # Rule 5: Chronic lateness with no improvement — still needs Director eyes
    if chronic_lateness and forecast_trend not in ("IMPROVING",):
        return "ESCALATE_TO_DIRECTOR", True

    # Rule 6: Safe to auto-approve
    return "APPROVE", False


# ─── Deterministic Fallback ──────────────────────────────────
def fallback_rule_engine(state) -> "DecisionResult":
    """
    Deterministic fallback if LLM fails 3x.
    Uses scoring formula directly — no LLM call.
    """
    from contracts.schemas import DecisionResult

    q = state.quality
    h = state.history

    score = compute_composite_score(
        quality_sub_score=q.quality_sub_score if q else 50.0,
        forecast_confidence_in_stable=h.forecast_confidence if h else 0.5,
        anomaly_votes=h.anomaly_votes if h else 0,
        risk_index_score=h.risk_index_score if h else 50.0,
    )

    financial_health = (
        state.intake.supplier_profile.get("financial_health", "YELLOW")
        if state.intake
        else "YELLOW"
    )
    cert_valid = q.cert_valid if q else True
    forecast_trend = h.forecast_trend if h else "STABLE"
    anomaly_votes = h.anomaly_votes if h else 0
    chronic_lateness = h.chronic_lateness if h else False

    action, hitl_required = determine_action_and_hitl(
        score, cert_valid, financial_health, forecast_trend, anomaly_votes, chronic_lateness
    )

    return DecisionResult(
        action=action,
        composite_score=round(score, 2),
        rationale=(
            "Recommended because rule-based fallback triggered after LLM failure. "
            "Manual review advised."
        ),
        hitl_required=hitl_required,
    )
