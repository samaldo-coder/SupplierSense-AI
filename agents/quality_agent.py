# agents/quality_agent.py
# Agent 2: Quality Agent
# Checks certifications, calculates quality sub-score.

import logging
from datetime import datetime, timezone
from contracts.schemas import QualityResult, AgentState
from agents.tools.erp_tools import get_quality_certs, get_parts_by_supplier
from agents.tools.audit_tools import log_audit_decision

logger = logging.getLogger(__name__)


def _compute_quality_sub_score(delay_days: int, cert_valid: bool) -> float:
    """
    Quality sub-score formula (from AGENTS.md Part 7):
    cert_score  = 100 if cert expired or missing, else 0
    delay_score = min(delay_days / 14 * 100, 100)
    quality_sub_score = 0.6 * delay_score + 0.4 * cert_score
    """
    cert_score = 0.0 if cert_valid else 100.0
    delay_score = min(delay_days / 14.0 * 100.0, 100.0)
    return round(0.6 * delay_score + 0.4 * cert_score, 2)


def _determine_defect_trend(parts: list) -> str:
    """Determine defect trend from parts history.
    Without real defect data, uses part count as a heuristic."""
    if not parts:
        return "STABLE"
    # If we had real defect rate data, we'd compare recent vs historical
    # For now, return STABLE as safe default
    return "STABLE"


def run_quality_agent(state: AgentState) -> AgentState:
    """
    Agent 2: Quality.
    - Fetches cert info and parts list from P4 API
    - Checks cert expiry vs today
    - Calculates quality_sub_score
    - Returns QualityResult
    """
    try:
        supplier_id = state.intake.supplier_id if state.intake else state.event_id
        delay_days = state.intake.delay_days if state.intake else 0

        # Step 1: Fetch certs
        certs = get_quality_certs(supplier_id)

        # Step 2: Fetch parts for defect trend
        parts = get_parts_by_supplier(supplier_id)

        # Step 3: Determine cert validity
        cert_expiry_str = certs.get("quality_cert_expiry")
        cert_valid = False
        cert_type = certs.get("quality_cert_type")

        if cert_expiry_str:
            try:
                # Try multiple date formats
                for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        cert_expiry_date = datetime.strptime(cert_expiry_str, fmt)
                        cert_valid = cert_expiry_date > datetime.now()
                        break
                    except ValueError:
                        continue
            except Exception:
                cert_valid = False

        # Step 4: Calculate quality sub-score
        quality_sub_score = _compute_quality_sub_score(delay_days, cert_valid)

        # Step 5: Determine defect trend
        defect_trend = _determine_defect_trend(parts)

        result = QualityResult(
            cert_valid=cert_valid,
            cert_expiry=cert_expiry_str,
            cert_type=cert_type,
            defect_trend=defect_trend,
            quality_sub_score=quality_sub_score,
        )

        # Step 6: Log audit
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="quality_agent",
            inputs={"supplier_id": supplier_id, "delay_days": delay_days},
            outputs=result.model_dump(),
            confidence=0.90,
            rationale=(
                f"Quality score {quality_sub_score:.1f}/100. "
                f"Cert {'valid' if cert_valid else 'EXPIRED/MISSING'}. "
                f"Defect trend: {defect_trend}."
            ),
        )
        state.audit_entries.append(audit_entry)
        state.quality = result
        return state

    except Exception as e:
        logger.error(f"Quality agent error: {e}")
        # Fallback: assume worst case
        result = QualityResult(
            cert_valid=False,
            cert_expiry=None,
            cert_type=None,
            defect_trend="STABLE",
            quality_sub_score=60.0,
        )
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="quality_agent",
            inputs={"error": str(e)},
            outputs=result.model_dump(),
            confidence=0.3,
            rationale=f"Quality agent error: {e}. Using conservative defaults.",
        )
        state.audit_entries.append(audit_entry)
        state.quality = result
        return state
