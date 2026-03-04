# agents/executor_agent.py
# Agent 5: Executor Agent
# Creates PO, updates supplier assignment, sends confirmation.
# GUARD: Only runs if hitl_required==False OR Director has approved.

import uuid
import logging
from datetime import datetime, timezone
from contracts.schemas import ExecutorResult, AgentState
from agents.tools.erp_tools import (
    create_purchase_order,
    update_supplier_assignment,
    send_po_confirmation,
    get_parts_by_supplier,
)
from agents.tools.audit_tools import log_audit_decision
from agents.tools.comms_tools import send_notification

logger = logging.getLogger(__name__)


def run_executor_agent(state: AgentState) -> AgentState:
    """
    Agent 5: Executor.
    - GUARD: Verifies HITL approval if required
    - Creates purchase order for recommended supplier
    - Updates supplier assignment for affected parts
    - Sends PO confirmation notification
    - Returns ExecutorResult
    """
    try:
        # ─── GUARD: Enforce HITL check ───────────────────────
        if state.decision is None:
            raise ValueError("Executor called without a Decision result in state")
        if state.decision.hitl_required and state.decision.hitl_actor is None:
            raise ValueError(
                "Executor called on HITL-required decision without Director approval"
            )

        decision = state.decision
        supplier_id = state.intake.supplier_id if state.intake else state.event_id
        recommended_id = decision.recommended_supplier_id
        approved_by = decision.hitl_actor or "auto_approved"

        # Step 1: Get affected parts
        parts = get_parts_by_supplier(supplier_id)
        part_id = parts[0].get("part_id", "UNKNOWN") if parts else "UNKNOWN"

        # Step 2: Create purchase order
        po_result = create_purchase_order(
            supplier_id=recommended_id or supplier_id,
            part_id=part_id,
            quantity=100,  # default order quantity
            approved_by=approved_by,
        )
        po_id = po_result.get("po_id", f"PO-{uuid.uuid4().hex[:8].upper()}")

        # Step 3: Update supplier assignment (if we have a recommended alternative)
        if recommended_id and recommended_id != supplier_id:
            for part in parts:
                pid = part.get("part_id")
                if pid:
                    update_supplier_assignment(pid, recommended_id)

        # Step 4: Send PO confirmation
        send_po_confirmation(recommended_id or supplier_id, po_id)

        # Step 5: Send notifications
        notifications_sent = []

        # Notify procurement
        notif = send_notification(
            recipient_role="procurement",
            message=f"PO {po_id} created. Supplier swap: {supplier_id} → {recommended_id or 'same'}",
            run_id=state.run_id,
            notification_type="po_created",
        )
        notifications_sent.append(f"procurement: {notif.get('status', 'sent')}")

        # Notify director if HITL was involved
        if decision.hitl_actor:
            notif = send_notification(
                recipient_role="director",
                message=f"PO {po_id} executed per your approval. Run: {state.run_id}",
                run_id=state.run_id,
                notification_type="execution_complete",
            )
            notifications_sent.append(f"director: {notif.get('status', 'sent')}")

        confirmation_timestamp = datetime.now(timezone.utc).isoformat()

        result = ExecutorResult(
            po_id=po_id,
            confirmation_timestamp=confirmation_timestamp,
            notifications_sent=notifications_sent,
        )

        # Step 6: Log audit
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="executor_agent",
            inputs={
                "recommended_supplier_id": recommended_id,
                "approved_by": approved_by,
                "part_id": part_id,
            },
            outputs=result.model_dump(),
            confidence=1.0,
            rationale=f"PO {po_id} created and confirmed at {confirmation_timestamp}.",
            hitl_actor=decision.hitl_actor,
        )
        state.audit_entries.append(audit_entry)
        state.executor = result
        return state

    except ValueError:
        # Re-raise guard errors — these should NOT be caught silently
        raise

    except Exception as e:
        logger.error(f"Executor agent error: {e}")
        # Create a fallback PO ID for audit trail
        fallback_po = f"PO-ERROR-{uuid.uuid4().hex[:8].upper()}"
        result = ExecutorResult(
            po_id=fallback_po,
            confirmation_timestamp=datetime.now(timezone.utc).isoformat(),
            notifications_sent=[f"error: {str(e)}"],
        )
        audit_entry = log_audit_decision(
            run_id=state.run_id,
            agent_name="executor_agent",
            inputs={"error": str(e)},
            outputs=result.model_dump(),
            confidence=0.2,
            rationale=f"Executor error: {e}. Fallback PO created for audit trail.",
            hitl_actor=state.decision.hitl_actor if state.decision else None,
        )
        state.audit_entries.append(audit_entry)
        state.executor = result
        return state
