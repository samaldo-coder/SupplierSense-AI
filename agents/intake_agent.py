# agents/intake_agent.py
# Agent 1: Intake Agent
# Parses a raw SupplierEvent, enriches with supplier profile, writes 1-sentence summary.

import json
import logging
from contracts.schemas import SupplierEvent, IntakeResult, AgentState
from agents.tools.erp_tools import get_supplier_profile
from agents.tools.audit_tools import log_audit_decision

logger = logging.getLogger(__name__)


def _fallback_intake(event: SupplierEvent, supplier: dict) -> IntakeResult:
    """Deterministic fallback when LLM is unavailable."""
    summary = (
        f"{event.event_type} event for supplier {supplier.get('supplier_name', event.supplier_id)}: "
        f"{event.description}"
    )
    return IntakeResult(
        supplier_id=event.supplier_id,
        event_type=event.event_type,
        delay_days=event.delay_days,
        raw_summary=summary,
        supplier_profile=supplier,
    )


def run_intake_agent(event: SupplierEvent, state: AgentState) -> AgentState:
    """
    Agent 1: Intake.
    - Fetches supplier profile from P4 API
    - Uses LLM to create structured summary (or falls back to rule-based)
    - Validates output with Pydantic
    - Logs to audit trail
    """
    try:
        # Step 1: Fetch supplier profile
        supplier = get_supplier_profile(event.supplier_id)

        # Step 2: Try LLM summarization
        try:
            from agents.utils import call_llm_with_validation

            prompt = f"""You are a supply chain analyst. A supplier event has been received.

Event: {event.model_dump_json()}
Supplier Profile: {json.dumps(supplier)}

Extract and return JSON matching this schema exactly:
{{
  "supplier_id": "{event.supplier_id}",
  "event_type": "{event.event_type}",
  "delay_days": {event.delay_days},
  "raw_summary": "1 sentence describing what happened and its potential impact",
  "supplier_profile": {json.dumps(supplier)}
}}

The raw_summary must be exactly 1 sentence, factual, and include the supplier name and delay impact."""

            result = call_llm_with_validation(prompt, IntakeResult)
        except Exception as llm_err:
            logger.warning(f"Intake LLM failed: {llm_err} — using rule-based fallback")
            result = _fallback_intake(event, supplier)

        # Step 3: Log audit decision
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="intake_agent",
            inputs=event.model_dump(),
            outputs=result.model_dump(),
            confidence=0.95,
            rationale=result.raw_summary,
        )
        state.audit_entries.append(audit_entry)
        state.intake = result
        return state

    except Exception as e:
        logger.error(f"Intake agent error: {e}")
        # Even on error, create a minimal result and log it
        supplier = {"supplier_id": event.supplier_id, "error": str(e)}
        result = _fallback_intake(event, supplier)
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="intake_agent",
            inputs=event.model_dump(),
            outputs={"error": str(e)},
            confidence=0.5,
            rationale=f"Intake agent encountered an error: {e}",
        )
        state.audit_entries.append(audit_entry)
        state.intake = result
        return state
