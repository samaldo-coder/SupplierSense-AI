# agents/decision_agent.py
# Agent 4: Decision Agent
# Computes composite score, applies escalation rules, picks best alt supplier.
# This is the HITL trigger point.

import json
import logging
from contracts.schemas import DecisionResult, AgentState
from agents.tools.erp_tools import query_avl, get_parts_by_supplier
from agents.tools.audit_tools import log_audit_decision
from agents.utils import (
    compute_composite_score,
    determine_action_and_hitl,
    fallback_rule_engine,
)

logger = logging.getLogger(__name__)


def _score_alternative_supplier(alt: dict) -> float:
    """
    Alternative supplier scoring (from AGENTS.md Part 7):
    S = 0.35*(1 - lead_days/30) + 0.30*(1 - cost_delta) + 0.25*cert_valid + 0.10*(1 - geo_risk)
    """
    lead_days = alt.get("lead_time_days", 15)
    cost_delta = alt.get("cost_delta", alt.get("unit_cost", 100) / 200.0)  # normalize
    cert_valid = 1.0 if alt.get("is_approved", False) else 0.0
    geo_risk = alt.get("geographic_risk", 0.5)

    return (
        0.35 * (1 - min(lead_days / 30.0, 1.0))
        + 0.30 * (1 - min(cost_delta, 1.0))
        + 0.25 * cert_valid
        + 0.10 * (1 - min(geo_risk, 1.0))
    )


def run_decision_agent(state: AgentState) -> AgentState:
    """
    Agent 4: Decision.
    - Gathers quality + history results from state
    - Queries AVL for affected parts
    - Computes composite risk score
    - Applies escalation rules (deterministic)
    - Uses LLM to select best alt supplier and write rationale
    - Falls back to rule engine if LLM fails
    """
    try:
        # Step 1: Extract prior agent results
        q = state.quality
        h = state.history
        intake = state.intake

        if not intake:
            raise ValueError("Decision agent requires intake result")

        supplier_id = intake.supplier_id
        financial_health = intake.supplier_profile.get("financial_health", "YELLOW")

        # Step 2: Compute composite score
        composite_score = compute_composite_score(
            quality_sub_score=q.quality_sub_score if q else 50.0,
            forecast_confidence_in_stable=h.forecast_confidence if h else 0.5,
            anomaly_votes=h.anomaly_votes if h else 0,
            risk_index_score=h.risk_index_score if h else 50.0,
        )

        # Step 3: Determine action via rules
        cert_valid = q.cert_valid if q else True
        forecast_trend = h.forecast_trend if h else "STABLE"
        anomaly_votes = h.anomaly_votes if h else 0

        action, hitl_required = determine_action_and_hitl(
            composite_score, cert_valid, financial_health, forecast_trend, anomaly_votes
        )

        # Step 4: Query AVL for alternative suppliers
        parts = get_parts_by_supplier(supplier_id)
        avl_entries = []
        for part in parts:
            part_id = part.get("part_id", "")
            if part_id:
                avl_entries.extend(query_avl(part_id))

        # Step 5: Try LLM for supplier selection + rationale
        recommended_supplier_id = None
        rationale = ""

        if avl_entries:
            # Score alternatives deterministically first
            scored = [
                (alt, _score_alternative_supplier(alt))
                for alt in avl_entries
                if alt.get("supplier_id") != supplier_id
            ]
            scored.sort(key=lambda x: x[1], reverse=True)

            if scored:
                best_alt = scored[0][0]
                recommended_supplier_id = best_alt.get("supplier_id")

                try:
                    from agents.utils import call_llm_with_validation

                    prompt = f"""You are a supply chain decision engine for a Fortune 200 manufacturer.

Given the following assessment data:
- Intake: {intake.model_dump_json()}
- Quality Assessment: {q.model_dump_json() if q else '{}'}
- Supplier History: {h.model_dump_json() if h else '{}'}
- Available Alternative Suppliers (AVL): {json.dumps(avl_entries)}
- Computed Composite Risk Score: {composite_score:.1f}/100

Task:
1. Select the best alternative supplier from the AVL list using this scoring:
   S = 0.35*(1 - lead_days/30) + 0.30*(1 - cost_delta) + 0.25*cert_valid + 0.10*(1 - geo_risk)
2. Justify your selection in exactly 2 plain-English sentences.
   Start with: "Recommended because..."
3. The action and hitl_required have already been determined by rule engine.
   Use action="{action}" and hitl_required={str(hitl_required).lower()}.

Return valid JSON:
{{
  "action": "{action}",
  "recommended_supplier_id": "{recommended_supplier_id}",
  "composite_score": {composite_score:.2f},
  "rationale": "Recommended because...",
  "hitl_required": {str(hitl_required).lower()}
}}"""
                    result = call_llm_with_validation(prompt, DecisionResult)
                    # Override action/hitl to match our deterministic rules
                    result.action = action
                    result.hitl_required = hitl_required
                    result.composite_score = round(composite_score, 2)

                except Exception as llm_err:
                    logger.warning(f"Decision LLM failed: {llm_err} — using fallback")
                    rationale = (
                        f"Recommended because supplier {recommended_supplier_id} has the best "
                        f"combined score for lead time, cost, and certification status."
                    )
                    result = DecisionResult(
                        action=action,
                        recommended_supplier_id=recommended_supplier_id,
                        composite_score=round(composite_score, 2),
                        rationale=rationale,
                        hitl_required=hitl_required,
                    )
            else:
                # No valid alternatives found
                result = DecisionResult(
                    action=action,
                    recommended_supplier_id=None,
                    composite_score=round(composite_score, 2),
                    rationale="Recommended because no alternative suppliers available in AVL. Manual sourcing required.",
                    hitl_required=hitl_required,
                )
        else:
            # No AVL data (parts list empty or API offline)
            result = DecisionResult(
                action=action,
                recommended_supplier_id=None,
                composite_score=round(composite_score, 2),
                rationale=(
                    "Recommended because AVL data unavailable. "
                    "Decision based on risk score alone; manual supplier selection needed."
                ),
                hitl_required=hitl_required,
            )

        # Step 6: Log audit
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="decision_agent",
            inputs={
                "composite_score": composite_score,
                "action": action,
                "hitl_required": hitl_required,
                "avl_count": len(avl_entries),
            },
            outputs=result.model_dump(),
            confidence=0.85 if avl_entries else 0.5,
            rationale=result.rationale,
        )
        state.audit_entries.append(audit_entry)
        state.decision = result
        return state

    except Exception as e:
        logger.error(f"Decision agent error: {e}")
        # Use deterministic fallback
        try:
            result = fallback_rule_engine(state)
        except Exception:
            result = DecisionResult(
                action="ESCALATE_TO_DIRECTOR",
                composite_score=50.0,
                rationale="Recommended because decision agent encountered an error. Manual review required.",
                hitl_required=True,
            )
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="decision_agent",
            inputs={"error": str(e)},
            outputs=result.model_dump(),
            confidence=0.3,
            rationale=f"Decision agent error: {e}. Fallback used.",
        )
        state.audit_entries.append(audit_entry)
        state.decision = result
        return state
