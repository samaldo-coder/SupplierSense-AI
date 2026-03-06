# contracts/schemas.py
# Shared Pydantic models — single source of truth for all agent data contracts.
# All agents import from here. Never change these without team agreement.
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ─── Inbound Event ───────────────────────────────────────────
class SupplierEvent(BaseModel):
    event_id: str
    supplier_id: str
    event_type: Literal["DELIVERY_MISS", "FINANCIAL_FLAG", "QUALITY_HOLD"]
    delay_days: int
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    created_at: Optional[str] = None


# ─── Agent 1 Output ──────────────────────────────────────────
class IntakeResult(BaseModel):
    supplier_id: str
    event_type: str
    delay_days: int
    raw_summary: str
    supplier_profile: dict  # full row from suppliers table


# ─── Agent 2 Output ──────────────────────────────────────────
class QualityResult(BaseModel):
    cert_valid: bool
    cert_expiry: Optional[str] = None
    cert_type: Optional[str] = None
    defect_trend: Literal["WORSENING", "STABLE", "IMPROVING"]
    quality_sub_score: float  # 0–100


# ─── Agent 3 Output ──────────────────────────────────────────
class HistoryResult(BaseModel):
    avg_delay_30d: float
    forecast_trend: Literal["WORSENING", "ELEVATED", "STABLE", "IMPROVING"]
    forecast_confidence: float      # 0.0–1.0 (from P5 AutoARIMA)
    anomaly_votes: int              # 0–3 (from P5 ensemble)
    anomaly_flagged: bool
    risk_index_score: float         # 0–100
    chronic_lateness: bool = False  # True if supplier avg delay > 80% of fleet peers


# ─── Agent 4 Output ──────────────────────────────────────────
class DecisionResult(BaseModel):
    action: Literal[
        "APPROVE",
        "ESCALATE_TO_DIRECTOR",
        "ESCALATE_TO_VP",
        "REJECT"
    ]
    recommended_supplier_id: Optional[str] = None
    composite_score: float          # 0–100
    rationale: str                  # ≤2 sentences, starts with "Recommended because..."
    hitl_required: bool
    hitl_actor: Optional[str] = None  # filled after Director acts


# ─── Agent 5 Output ──────────────────────────────────────────
class ExecutorResult(BaseModel):
    po_id: str
    confirmation_timestamp: str
    notifications_sent: list[str]


# ─── Full Pipeline State ─────────────────────────────────────
class AgentState(BaseModel):
    event_id: str
    run_id: str
    intake: Optional[IntakeResult] = None
    quality: Optional[QualityResult] = None
    history: Optional[HistoryResult] = None
    decision: Optional[DecisionResult] = None
    executor: Optional[ExecutorResult] = None
    audit_entries: list[dict] = Field(default_factory=list)
    error: Optional[str] = None
    paused_for_hitl: bool = False


# ─── Audit Log Entry ─────────────────────────────────────────
class AuditEntry(BaseModel):
    run_id: str
    agent_name: str
    inputs: dict
    outputs: dict
    confidence: float           # 0.0–1.0
    rationale: str
    hitl_actor: Optional[str] = None
    timestamp: str
