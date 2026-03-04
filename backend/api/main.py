"""
SupplyGuard AI — Unified Backend API
FastAPI server providing ALL endpoints for:
  - Agent tools (ERP, audit, approvals, PO, comms)
  - Frontend dashboards (suppliers, events, approvals, audit trail)
  - Data/ML layer (forecasts, anomalies)

Runs on port 3001 (primary backend) with CORS enabled for frontend.
Uses in-memory seed data that mirrors db/seed.sql.
When Supabase is connected, swap _STORE dicts with real DB queries.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, date
import uuid
import json
import os

# ── Import intelligence modules ──────────────────────────────
from intelligence.anomaly import anomaly_score, anomaly_score_for_supplier
from intelligence.forecast import run_forecast, run_forecast_for_supplier
from intelligence.risk_score import compute_risk

app = FastAPI(title="SupplyGuard AI Backend", version="1.0.0")

# ── CORS — allow frontend on any localhost port ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════
# IN-MEMORY SEED DATA (mirrors db/seed.sql)
# ═══════════════════════════════════════════════

SUPPLIERS = {
    "a1000000-0000-0000-0000-000000000001": {
        "supplier_id": "a1000000-0000-0000-0000-000000000001",
        "supplier_name": "AlphaForge Industries",
        "country": "Mexico",
        "tier": 1,
        "financial_health": "RED",
        "lead_time_days": 12,
        "unit_cost": 85.50,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2025-06-15",
    },
    "a1000000-0000-0000-0000-000000000002": {
        "supplier_id": "a1000000-0000-0000-0000-000000000002",
        "supplier_name": "BetaSteel Corporation",
        "country": "USA",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 5,
        "unit_cost": 92.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2027-12-31",
    },
    "a1000000-0000-0000-0000-000000000003": {
        "supplier_id": "a1000000-0000-0000-0000-000000000003",
        "supplier_name": "GammaCast Manufacturing",
        "country": "Germany",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 7,
        "unit_cost": 110.00,
        "is_active": True,
        "quality_cert_type": "IATF 16949",
        "quality_cert_expiry": "2027-08-20",
    },
    "a1000000-0000-0000-0000-000000000004": {
        "supplier_id": "a1000000-0000-0000-0000-000000000004",
        "supplier_name": "DeltaSteel Corp",
        "country": "Brazil",
        "tier": 2,
        "financial_health": "YELLOW",
        "lead_time_days": 9,
        "unit_cost": 78.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2026-03-01",
    },
    "a1000000-0000-0000-0000-000000000005": {
        "supplier_id": "a1000000-0000-0000-0000-000000000005",
        "supplier_name": "EpsilonCast Systems",
        "country": "India",
        "tier": 2,
        "financial_health": "GREEN",
        "lead_time_days": 8,
        "unit_cost": 65.00,
        "is_active": True,
        "quality_cert_type": "ISO 14001",
        "quality_cert_expiry": "2027-05-10",
    },
    "a1000000-0000-0000-0000-000000000006": {
        "supplier_id": "a1000000-0000-0000-0000-000000000006",
        "supplier_name": "ZetaAlloy Solutions",
        "country": "USA",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 4,
        "unit_cost": 98.00,
        "is_active": True,
        "quality_cert_type": "IATF 16949",
        "quality_cert_expiry": "2028-01-15",
    },
    "a1000000-0000-0000-0000-000000000007": {
        "supplier_id": "a1000000-0000-0000-0000-000000000007",
        "supplier_name": "EtaPrecision Parts",
        "country": "Japan",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 6,
        "unit_cost": 120.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2027-11-30",
    },
    "a1000000-0000-0000-0000-000000000008": {
        "supplier_id": "a1000000-0000-0000-0000-000000000008",
        "supplier_name": "ThetaForge Ltd",
        "country": "China",
        "tier": 2,
        "financial_health": "YELLOW",
        "lead_time_days": 10,
        "unit_cost": 55.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2025-12-01",
    },
    "a1000000-0000-0000-0000-000000000009": {
        "supplier_id": "a1000000-0000-0000-0000-000000000009",
        "supplier_name": "IotaMetals Inc",
        "country": "South Korea",
        "tier": 1,
        "financial_health": "GREEN",
        "lead_time_days": 5,
        "unit_cost": 105.00,
        "is_active": True,
        "quality_cert_type": "IATF 16949",
        "quality_cert_expiry": "2027-09-15",
    },
    "a1000000-0000-0000-0000-000000000010": {
        "supplier_id": "a1000000-0000-0000-0000-000000000010",
        "supplier_name": "KappaComponents Global",
        "country": "Turkey",
        "tier": 3,
        "financial_health": "RED",
        "lead_time_days": 14,
        "unit_cost": 48.00,
        "is_active": True,
        "quality_cert_type": "ISO 9001",
        "quality_cert_expiry": "2024-08-01",
    },
}

PARTS = [
    {"part_id": "b2000000-0000-0000-0000-000000000001", "part_number": "PT-ENG-001", "part_name": "Engine Block Assembly", "category": "Engine", "primary_supplier_id": "a1000000-0000-0000-0000-000000000001", "factory": "Columbus Plant", "min_order_qty": 50},
    {"part_id": "b2000000-0000-0000-0000-000000000002", "part_number": "PT-ENG-002", "part_name": "Cylinder Head", "category": "Engine", "primary_supplier_id": "a1000000-0000-0000-0000-000000000002", "factory": "Columbus Plant", "min_order_qty": 100},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "part_number": "PT-TURBO-001", "part_name": "Turbocharger Assembly", "category": "Turbo", "primary_supplier_id": "a1000000-0000-0000-0000-000000000003", "factory": "Jamestown Plant", "min_order_qty": 75},
    {"part_id": "b2000000-0000-0000-0000-000000000004", "part_number": "PT-TURBO-002", "part_name": "Turbo Wastegate Actuator", "category": "Turbo", "primary_supplier_id": "a1000000-0000-0000-0000-000000000004", "factory": "Jamestown Plant", "min_order_qty": 200},
    {"part_id": "b2000000-0000-0000-0000-000000000005", "part_number": "PT-EXH-001", "part_name": "Exhaust Manifold", "category": "Exhaust", "primary_supplier_id": "a1000000-0000-0000-0000-000000000005", "factory": "Rocky Mount Plant", "min_order_qty": 150},
    {"part_id": "b2000000-0000-0000-0000-000000000006", "part_number": "PT-EXH-002", "part_name": "DPF Assembly", "category": "Exhaust", "primary_supplier_id": "a1000000-0000-0000-0000-000000000006", "factory": "Rocky Mount Plant", "min_order_qty": 80},
    {"part_id": "b2000000-0000-0000-0000-000000000007", "part_number": "PT-FUEL-001", "part_name": "Fuel Injector Set", "category": "Fuel System", "primary_supplier_id": "a1000000-0000-0000-0000-000000000007", "factory": "Columbus Plant", "min_order_qty": 120},
    {"part_id": "b2000000-0000-0000-0000-000000000008", "part_number": "PT-FUEL-002", "part_name": "High Pressure Fuel Pump", "category": "Fuel System", "primary_supplier_id": "a1000000-0000-0000-0000-000000000008", "factory": "Jamestown Plant", "min_order_qty": 60},
    {"part_id": "b2000000-0000-0000-0000-000000000009", "part_number": "PT-COOL-001", "part_name": "Radiator Assembly", "category": "Cooling", "primary_supplier_id": "a1000000-0000-0000-0000-000000000009", "factory": "Columbus Plant", "min_order_qty": 90},
    {"part_id": "b2000000-0000-0000-0000-000000000010", "part_number": "PT-COOL-002", "part_name": "Water Pump", "category": "Cooling", "primary_supplier_id": "a1000000-0000-0000-0000-000000000010", "factory": "Rocky Mount Plant", "min_order_qty": 200},
    {"part_id": "b2000000-0000-0000-0000-000000000011", "part_number": "PT-ENG-003", "part_name": "Crankshaft", "category": "Engine", "primary_supplier_id": "a1000000-0000-0000-0000-000000000002", "factory": "Columbus Plant", "min_order_qty": 40},
    {"part_id": "b2000000-0000-0000-0000-000000000012", "part_number": "PT-TURBO-003", "part_name": "Intercooler", "category": "Turbo", "primary_supplier_id": "a1000000-0000-0000-0000-000000000005", "factory": "Jamestown Plant", "min_order_qty": 100},
    {"part_id": "b2000000-0000-0000-0000-000000000013", "part_number": "PT-EXH-003", "part_name": "SCR Catalyst", "category": "Exhaust", "primary_supplier_id": "a1000000-0000-0000-0000-000000000003", "factory": "Rocky Mount Plant", "min_order_qty": 70},
    {"part_id": "b2000000-0000-0000-0000-000000000014", "part_number": "PT-FUEL-003", "part_name": "Fuel Filter Module", "category": "Fuel System", "primary_supplier_id": "a1000000-0000-0000-0000-000000000009", "factory": "Columbus Plant", "min_order_qty": 250},
    {"part_id": "b2000000-0000-0000-0000-000000000015", "part_number": "PT-COOL-003", "part_name": "Thermostat Housing Assembly", "category": "Cooling", "primary_supplier_id": "a1000000-0000-0000-0000-000000000006", "factory": "Jamestown Plant", "min_order_qty": 180},
]

AVL = [
    {"part_id": "b2000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000001", "lead_time_days": 12, "unit_cost": 85.50, "quality_cert_expiry": "2025-06-15", "geographic_risk": 0.40, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000002", "lead_time_days": 5, "unit_cost": 95.00, "quality_cert_expiry": "2027-12-31", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000003", "lead_time_days": 7, "unit_cost": 112.00, "quality_cert_expiry": "2027-08-20", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000002", "supplier_id": "a1000000-0000-0000-0000-000000000002", "lead_time_days": 5, "unit_cost": 92.00, "quality_cert_expiry": "2027-12-31", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000002", "supplier_id": "a1000000-0000-0000-0000-000000000007", "lead_time_days": 6, "unit_cost": 125.00, "quality_cert_expiry": "2027-11-30", "geographic_risk": 0.15, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000003", "lead_time_days": 7, "unit_cost": 110.00, "quality_cert_expiry": "2027-08-20", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000009", "lead_time_days": 5, "unit_cost": 115.00, "quality_cert_expiry": "2027-09-15", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000005", "lead_time_days": 8, "unit_cost": 70.00, "quality_cert_expiry": "2027-05-10", "geographic_risk": 0.55, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000004", "supplier_id": "a1000000-0000-0000-0000-000000000004", "lead_time_days": 9, "unit_cost": 78.00, "quality_cert_expiry": "2026-03-01", "geographic_risk": 0.45, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000004", "supplier_id": "a1000000-0000-0000-0000-000000000008", "lead_time_days": 10, "unit_cost": 58.00, "quality_cert_expiry": "2025-12-01", "geographic_risk": 0.60, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000005", "supplier_id": "a1000000-0000-0000-0000-000000000005", "lead_time_days": 8, "unit_cost": 65.00, "quality_cert_expiry": "2027-05-10", "geographic_risk": 0.55, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000005", "supplier_id": "a1000000-0000-0000-0000-000000000006", "lead_time_days": 4, "unit_cost": 102.00, "quality_cert_expiry": "2028-01-15", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000006", "supplier_id": "a1000000-0000-0000-0000-000000000006", "lead_time_days": 4, "unit_cost": 98.00, "quality_cert_expiry": "2028-01-15", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000006", "supplier_id": "a1000000-0000-0000-0000-000000000007", "lead_time_days": 6, "unit_cost": 130.00, "quality_cert_expiry": "2027-11-30", "geographic_risk": 0.15, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000007", "supplier_id": "a1000000-0000-0000-0000-000000000007", "lead_time_days": 6, "unit_cost": 120.00, "quality_cert_expiry": "2027-11-30", "geographic_risk": 0.15, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000007", "supplier_id": "a1000000-0000-0000-0000-000000000009", "lead_time_days": 5, "unit_cost": 108.00, "quality_cert_expiry": "2027-09-15", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000008", "supplier_id": "a1000000-0000-0000-0000-000000000008", "lead_time_days": 10, "unit_cost": 55.00, "quality_cert_expiry": "2025-12-01", "geographic_risk": 0.60, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000008", "supplier_id": "a1000000-0000-0000-0000-000000000010", "lead_time_days": 14, "unit_cost": 50.00, "quality_cert_expiry": "2024-08-01", "geographic_risk": 0.70, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000009", "supplier_id": "a1000000-0000-0000-0000-000000000009", "lead_time_days": 5, "unit_cost": 105.00, "quality_cert_expiry": "2027-09-15", "geographic_risk": 0.20, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000009", "supplier_id": "a1000000-0000-0000-0000-000000000002", "lead_time_days": 5, "unit_cost": 99.00, "quality_cert_expiry": "2027-12-31", "geographic_risk": 0.10, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000010", "supplier_id": "a1000000-0000-0000-0000-000000000010", "lead_time_days": 14, "unit_cost": 48.00, "quality_cert_expiry": "2024-08-01", "geographic_risk": 0.70, "is_approved": True},
    {"part_id": "b2000000-0000-0000-0000-000000000010", "supplier_id": "a1000000-0000-0000-0000-000000000005", "lead_time_days": 8, "unit_cost": 68.00, "quality_cert_expiry": "2027-05-10", "geographic_risk": 0.55, "is_approved": True},
]

EVENTS = [
    {"event_id": "c3000000-0000-0000-0000-000000000001", "supplier_id": "a1000000-0000-0000-0000-000000000001", "event_type": "DELIVERY_MISS", "delay_days": 9, "description": "Facility fire at AlphaForge Monterrey plant. 9-day delivery delay confirmed.", "severity": "CRITICAL"},
    {"event_id": "c3000000-0000-0000-0000-000000000002", "supplier_id": "a1000000-0000-0000-0000-000000000006", "event_type": "DELIVERY_MISS", "delay_days": 1, "description": "Minor 1-day delay within SLA buffer. No factory impact.", "severity": "LOW"},
    {"event_id": "c3000000-0000-0000-0000-000000000003", "supplier_id": "a1000000-0000-0000-0000-000000000004", "event_type": "FINANCIAL_FLAG", "delay_days": 4, "description": "DeltaSteel flagged for Q3 cash flow concerns. Delivery delay possible.", "severity": "HIGH"},
    {"event_id": "c3000000-0000-0000-0000-000000000004", "supplier_id": "a1000000-0000-0000-0000-000000000010", "event_type": "QUALITY_HOLD", "delay_days": 6, "description": "KappaComponents quality cert expired. Multiple defect reports received.", "severity": "CRITICAL"},
    {"event_id": "c3000000-0000-0000-0000-000000000005", "supplier_id": "a1000000-0000-0000-0000-000000000008", "event_type": "DELIVERY_MISS", "delay_days": 5, "description": "ThetaForge production line down for 5 days. Partial shipment only.", "severity": "HIGH"},
    {"event_id": "c3000000-0000-0000-0000-000000000006", "supplier_id": "a1000000-0000-0000-0000-000000000002", "event_type": "DELIVERY_MISS", "delay_days": 1, "description": "Weather delay, 1-day impact. Full recovery expected.", "severity": "LOW"},
    {"event_id": "c3000000-0000-0000-0000-000000000007", "supplier_id": "a1000000-0000-0000-0000-000000000003", "event_type": "QUALITY_HOLD", "delay_days": 3, "description": "GammaCast batch #4421 held for dimensional tolerance review.", "severity": "MEDIUM"},
    {"event_id": "c3000000-0000-0000-0000-000000000008", "supplier_id": "a1000000-0000-0000-0000-000000000005", "event_type": "DELIVERY_MISS", "delay_days": 3, "description": "Port congestion in Mumbai causing 3-day delay on EpsilonCast shipment.", "severity": "MEDIUM"},
    {"event_id": "c3000000-0000-0000-0000-000000000009", "supplier_id": "a1000000-0000-0000-0000-000000000007", "event_type": "DELIVERY_MISS", "delay_days": 1, "description": "Customs clearance delay, 1-day impact. Documentation resolved.", "severity": "LOW"},
    {"event_id": "c3000000-0000-0000-0000-000000000010", "supplier_id": "a1000000-0000-0000-0000-000000000009", "event_type": "FINANCIAL_FLAG", "delay_days": 2, "description": "IotaMetals credit rating downgrade flagged by monitoring service.", "severity": "MEDIUM"},
]

# ── Mutable stores (in-memory, reset on restart) ─────────────
AUDIT_LOG: list[dict] = []
PENDING_APPROVALS: dict[str, dict] = {}
PURCHASE_ORDERS: list[dict] = []
NOTIFICATIONS: list[dict] = []


# ═══════════════════════════════════════════════
# HEALTH & ROOT
# ═══════════════════════════════════════════════

@app.get("/")
def root():
    return {"message": "SupplyGuard AI Backend API running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "SupplyGuard AI Backend", "suppliers_loaded": len(SUPPLIERS), "events_loaded": len(EVENTS)}


# ═══════════════════════════════════════════════
# SUPPLIERS — used by agents/tools/erp_tools.py
# ═══════════════════════════════════════════════

@app.get("/api/suppliers")
def list_suppliers():
    """List all suppliers."""
    return list(SUPPLIERS.values())

@app.get("/api/suppliers/{supplier_id}")
def get_supplier(supplier_id: str):
    """GET /api/suppliers/:id — full supplier profile."""
    s = SUPPLIERS.get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return s

@app.get("/api/suppliers/{supplier_id}/certs")
def get_supplier_certs(supplier_id: str):
    """GET /api/suppliers/:id/certs — quality cert info."""
    s = SUPPLIERS.get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    today = date.today().isoformat()
    expiry = s.get("quality_cert_expiry", "2025-01-01")
    return {
        "supplier_id": supplier_id,
        "quality_cert_type": s.get("quality_cert_type", "ISO 9001"),
        "quality_cert_expiry": expiry,
        "is_approved": expiry >= today,
    }


# ═══════════════════════════════════════════════
# PARTS — used by agents
# ═══════════════════════════════════════════════

@app.get("/api/parts")
def list_parts(supplier_id: Optional[str] = Query(None)):
    """GET /api/parts?supplier_id=:id — filter parts by primary supplier."""
    if supplier_id:
        return [p for p in PARTS if p["primary_supplier_id"] == supplier_id]
    return PARTS


# ═══════════════════════════════════════════════
# AVL (Approved Vendor List) — used by Decision Agent
# ═══════════════════════════════════════════════

@app.get("/api/avl/{part_id}")
def get_avl(part_id: str):
    """GET /api/avl/:part_id — all approved vendors for a part."""
    entries = [a for a in AVL if a["part_id"] == part_id]
    # Enrich with supplier name and cert_valid flag
    enriched = []
    for a in entries:
        s = SUPPLIERS.get(a["supplier_id"], {})
        today = date.today().isoformat()
        cert_valid = (a.get("quality_cert_expiry", "2025-01-01") >= today)
        enriched.append({
            **a,
            "supplier_name": s.get("supplier_name", "Unknown"),
            "cert_valid": cert_valid,
        })
    return enriched


# ═══════════════════════════════════════════════
# EVENTS — used by agents/run.py and frontend
# ═══════════════════════════════════════════════

@app.get("/api/events")
def list_events():
    """GET /api/events — all supplier events (for pipeline testing)."""
    return EVENTS

@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    """GET /api/events/:id — single event."""
    for e in EVENTS:
        if e["event_id"] == event_id:
            return e
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")


# ═══════════════════════════════════════════════
# AUDIT LOG — used by all agents & frontend stepper
# ═══════════════════════════════════════════════

class AuditLogEntry(BaseModel):
    run_id: str
    agent_name: str
    inputs: dict = {}
    outputs: dict = {}
    confidence: float = 0.0
    rationale: str = ""
    hitl_actor: Optional[str] = None
    timestamp: Optional[str] = None

@app.post("/api/audit")
def create_audit_entry(entry: AuditLogEntry):
    """POST /api/audit — immutably log an agent decision."""
    entry_id = str(uuid.uuid4())
    record = {
        "entry_id": entry_id,
        "run_id": entry.run_id,
        "agent_name": entry.agent_name,
        "inputs": entry.inputs,
        "outputs": entry.outputs,
        "confidence": entry.confidence,
        "rationale": entry.rationale,
        "hitl_actor": entry.hitl_actor,
        "timestamp": entry.timestamp or datetime.now(timezone.utc).isoformat(),
    }
    AUDIT_LOG.append(record)
    return {"entry_id": entry_id}

@app.get("/api/audit/{run_id}")
def get_audit_trail(run_id: str):
    """GET /api/audit/:run_id — ordered audit trail for a pipeline run."""
    trail = [a for a in AUDIT_LOG if a["run_id"] == run_id]
    trail.sort(key=lambda x: x.get("timestamp", ""))
    return trail

@app.delete("/api/audit/{entry_id}")
def delete_audit_entry(entry_id: str):
    """DELETE /api/audit/:id — FORBIDDEN (immutability)."""
    raise HTTPException(status_code=403, detail="audit_log is immutable — DELETE is forbidden")


# ═══════════════════════════════════════════════
# APPROVALS — HITL workflow
# ═══════════════════════════════════════════════

class ApprovalRequest(BaseModel):
    run_id: str
    state_json: dict = {}
    summary: str = ""
    recommended_supplier_id: Optional[str] = None

class ApprovalDecision(BaseModel):
    decision: str  # "approved" | "rejected"
    note: str = ""
    director_id: str = ""

@app.post("/api/approvals")
def create_approval(req: ApprovalRequest):
    """POST /api/approvals — create pending approval for Director."""
    approval_id = str(uuid.uuid4())
    record = {
        "approval_id": approval_id,
        "run_id": req.run_id,
        "state_json": req.state_json,
        "summary": req.summary,
        "recommended_supplier_id": req.recommended_supplier_id,
        "status": "PENDING",
        "decided_by": None,
        "decision_note": None,
        "decided_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    PENDING_APPROVALS[approval_id] = record

    # Also write a notification for the director
    NOTIFICATIONS.append({
        "notification_id": str(uuid.uuid4()),
        "recipient_role": "director",
        "notification_type": "approval_required",
        "title": f"Approval Required: {req.summary[:80]}",
        "body": req.summary,
        "metadata": {"approval_id": approval_id, "run_id": req.run_id},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"approval_id": approval_id}

@app.get("/api/approvals")
def list_approvals(status: Optional[str] = Query(None)):
    """GET /api/approvals?status=PENDING — list approvals, optionally filtered."""
    items = list(PENDING_APPROVALS.values())
    if status:
        items = [a for a in items if a["status"] == status.upper()]
    # Sort newest first
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items

@app.get("/api/approvals/{approval_id}")
def get_approval(approval_id: str):
    """GET /api/approvals/:id"""
    a = PENDING_APPROVALS.get(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    return a

@app.patch("/api/approvals/{approval_id}/decide")
def decide_approval(approval_id: str, body: ApprovalDecision):
    """PATCH /api/approvals/:id/decide — Director approves/rejects.
    After DB update, calls POST localhost:8002/resume to trigger Agent 5."""
    a = PENDING_APPROVALS.get(approval_id)
    if not a:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    if a["status"] != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval already decided: {a['status']}")

    a["status"] = body.decision.upper()
    a["decided_by"] = body.director_id
    a["decision_note"] = body.note
    a["decided_at"] = datetime.now(timezone.utc).isoformat()

    # Try to call the agent resume API
    resume_url = os.getenv("RESUME_API_URL", "http://localhost:8002")
    try:
        import httpx
        resp = httpx.post(f"{resume_url}/resume", json={
            "run_id": a["run_id"],
            "decision": body.decision.lower(),
            "hitl_actor": body.director_id,
        }, timeout=30)
        resume_result = resp.json()
    except Exception as e:
        resume_result = {"status": "resume_call_failed", "error": str(e)}

    return {
        "approval_id": approval_id,
        "status": a["status"],
        "resume_result": resume_result,
    }


# ═══════════════════════════════════════════════
# PURCHASE ORDERS — used by Executor Agent
# ═══════════════════════════════════════════════

class PORequest(BaseModel):
    supplier_id: str
    part_id: str
    quantity: int
    approved_by: str

@app.post("/api/purchase-orders")
def create_purchase_order(req: PORequest):
    """POST /api/purchase-orders — create a new PO."""
    po_id = f"PO-{uuid.uuid4().hex[:8].upper()}"
    record = {
        "po_id": po_id,
        "supplier_id": req.supplier_id,
        "part_id": req.part_id,
        "quantity": req.quantity,
        "approved_by": req.approved_by,
        "status": "CREATED",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    PURCHASE_ORDERS.append(record)
    return {"po_id": po_id}

@app.get("/api/purchase-orders")
def list_purchase_orders():
    """GET /api/purchase-orders — list all POs."""
    return PURCHASE_ORDERS


# ═══════════════════════════════════════════════
# PARTS SUPPLIER UPDATE — used by Executor Agent
# ═══════════════════════════════════════════════

class SupplierUpdateRequest(BaseModel):
    new_supplier_id: str

@app.post("/api/parts/{part_id}/supplier")
def update_part_supplier(part_id: str, body: SupplierUpdateRequest):
    """POST /api/parts/:part_id/supplier — update primary supplier assignment."""
    for p in PARTS:
        if p["part_id"] == part_id:
            old_supplier = p["primary_supplier_id"]
            p["primary_supplier_id"] = body.new_supplier_id
            return {"part_id": part_id, "old_supplier_id": old_supplier, "new_supplier_id": body.new_supplier_id}
    raise HTTPException(status_code=404, detail=f"Part {part_id} not found")


# ═══════════════════════════════════════════════
# ORDERS — used by agents
# ═══════════════════════════════════════════════

@app.get("/api/orders")
def list_orders(status: Optional[str] = Query(None)):
    """GET /api/orders?status=OPEN — (demo: returns empty or a few)."""
    # For demo purposes, generate some synthetic open orders
    demo_orders = [
        {"order_id": "ORD-001", "part_id": "b2000000-0000-0000-0000-000000000001", "factory": "Columbus Plant", "quantity": 50, "status": "OPEN", "due_date": "2026-03-10"},
        {"order_id": "ORD-002", "part_id": "b2000000-0000-0000-0000-000000000003", "factory": "Jamestown Plant", "quantity": 75, "status": "OPEN", "due_date": "2026-03-12"},
        {"order_id": "ORD-003", "part_id": "b2000000-0000-0000-0000-000000000005", "factory": "Rocky Mount Plant", "quantity": 150, "status": "OPEN", "due_date": "2026-03-08"},
    ]
    if status:
        return [o for o in demo_orders if o["status"] == status.upper()]
    return demo_orders


# ═══════════════════════════════════════════════
# COMMS — Notification system (simulated Teams)
# ═══════════════════════════════════════════════

class NotificationRequest(BaseModel):
    type: str = "general"
    supplier_id: Optional[str] = None
    po_id: Optional[str] = None
    run_id: Optional[str] = None
    recipient_role: str = "procurement"
    message: str = ""

@app.post("/api/comms/notify")
def send_notification(req: NotificationRequest):
    """POST /api/comms/notify — simulated Teams notification (writes to DB)."""
    notification_id = str(uuid.uuid4())
    record = {
        "notification_id": notification_id,
        "recipient_role": req.recipient_role,
        "notification_type": req.type,
        "title": f"[{req.type.upper()}] {req.message[:60] or 'Notification'}",
        "body": req.message or f"PO {req.po_id} for supplier {req.supplier_id}",
        "metadata": {"supplier_id": req.supplier_id, "po_id": req.po_id, "run_id": req.run_id},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    NOTIFICATIONS.append(record)
    return {"notification_id": notification_id, "status": "sent"}

@app.get("/api/notifications")
def list_notifications(role: Optional[str] = Query(None), unread_only: bool = False):
    """GET /api/notifications?role=director&unread_only=true"""
    items = NOTIFICATIONS
    if role:
        items = [n for n in items if n["recipient_role"] == role]
    if unread_only:
        items = [n for n in items if not n["is_read"]]
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items

@app.patch("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str):
    """PATCH /api/notifications/:id/read — mark as read."""
    for n in NOTIFICATIONS:
        if n["notification_id"] == notification_id:
            n["is_read"] = True
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Notification not found")


# ═══════════════════════════════════════════════
# DATA/ML ENDPOINTS — Per-supplier forecasts & anomalies
# (Wraps intelligence/ modules with per-supplier support)
# ═══════════════════════════════════════════════

@app.get("/api/forecasts/{supplier_id}")
def get_forecast_for_supplier(supplier_id: str):
    """GET /api/forecasts/:supplier_id — P5-style per-supplier forecast."""
    try:
        result = run_forecast_for_supplier(supplier_id)
        return result
    except Exception as e:
        # Fallback with safe defaults
        return {
            "supplier_id": supplier_id,
            "forecast_date": date.today().isoformat(),
            "predicted_delay": 3.0,
            "lower_ci": 1.5,
            "upper_ci": 5.0,
            "model_aic": 0.0,
        }

@app.get("/api/anomalies/{supplier_id}")
def get_anomaly_for_supplier(supplier_id: str):
    """GET /api/anomalies/:supplier_id — P5-style per-supplier anomaly."""
    try:
        result = anomaly_score_for_supplier(supplier_id)
        return result
    except Exception as e:
        return {
            "supplier_id": supplier_id,
            "date": date.today().isoformat(),
            "anomaly_flag": False,
            "votes": 0,
            "zscore_val": 0.0,
            "mad_val": 0.0,
            "percentile_val": 0.5,
        }


# ═══════════════════════════════════════════════
# LEGACY ENDPOINTS (from original Backend branch)
# ═══════════════════════════════════════════════

@app.get("/risk/{supplier_id}")
def get_risk(supplier_id: str):
    """Legacy: overall risk score."""
    ratio = anomaly_score()
    s = SUPPLIERS.get(supplier_id, {})
    financial = s.get("financial_health", "YELLOW")
    risk, tier = compute_risk(financial_status=financial, anomaly_ratio=ratio, forecast_trend="UP")
    return {"supplier_id": supplier_id, "risk_score": risk, "tier": tier}

@app.get("/anomaly")
def get_anomaly():
    return {"anomaly_ratio": anomaly_score()}

@app.get("/forecast")
def get_forecast_all():
    forecast = run_forecast()
    return forecast.to_dict(orient="records")

@app.get("/supplier/{supplier_id}")
def analyze_supplier(supplier_id: str):
    """Legacy: full supplier analysis."""
    ratio = anomaly_score()
    forecast = run_forecast()
    s = SUPPLIERS.get(supplier_id, {})
    financial = s.get("financial_health", "YELLOW")
    risk, tier = compute_risk(financial_status=financial, anomaly_ratio=ratio, forecast_trend="UP")
    return {
        "supplier_id": supplier_id,
        "supplier_name": s.get("supplier_name", "Unknown"),
        "risk_score": risk,
        "tier": tier,
        "anomaly_ratio": ratio,
        "forecast_preview": forecast.head(5).to_dict(orient="records"),
    }


# ═══════════════════════════════════════════════
# DASHBOARD STATS — used by frontend
# ═══════════════════════════════════════════════

@app.get("/api/dashboard/stats")
def dashboard_stats():
    """Aggregate dashboard statistics for frontend."""
    total_events = len(EVENTS)
    critical_events = len([e for e in EVENTS if e["severity"] == "CRITICAL"])
    pending = len([a for a in PENDING_APPROVALS.values() if a["status"] == "PENDING"])
    approved = len([a for a in PENDING_APPROVALS.values() if a["status"] == "APPROVED"])
    total_pos = len(PURCHASE_ORDERS)
    active_suppliers = len([s for s in SUPPLIERS.values() if s["is_active"]])
    red_suppliers = len([s for s in SUPPLIERS.values() if s["financial_health"] == "RED"])

    return {
        "total_events": total_events,
        "critical_events": critical_events,
        "pending_approvals": pending,
        "approved_count": approved,
        "total_purchase_orders": total_pos,
        "active_suppliers": active_suppliers,
        "red_suppliers": red_suppliers,
        "total_audit_entries": len(AUDIT_LOG),
        "unread_notifications": len([n for n in NOTIFICATIONS if not n["is_read"]]),
    }

@app.get("/api/pipeline/runs")
def list_pipeline_runs():
    """Get all distinct pipeline runs from audit log."""
    runs = {}
    for entry in AUDIT_LOG:
        rid = entry["run_id"]
        if rid not in runs:
            runs[rid] = {
                "run_id": rid,
                "agents_completed": [],
                "started_at": entry["timestamp"],
                "last_update": entry["timestamp"],
            }
        runs[rid]["agents_completed"].append(entry["agent_name"])
        if entry["timestamp"] > runs[rid]["last_update"]:
            runs[rid]["last_update"] = entry["timestamp"]
    return list(runs.values())
