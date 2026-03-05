# SupplyGuard AI

**AI-powered supply chain disruption detection & response system.**

Built for the **Cummins Xtern 2026 Challenge** — *Enter the Matrix: Fortune 200 Edition*.

SupplyGuard AI detects supplier disruptions in real time, routes them through a **5-agent AI pipeline**, requests **human-in-the-loop (HITL) approval** from a Director, then executes a supplier swap — with a **full immutable audit trail**.

---

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Agent Pipeline](#agent-pipeline)
- [MCP Servers](#mcp-servers)
- [API Reference](#api-reference)
- [User Roles & Dashboards](#user-roles--dashboards)
- [Human-in-the-Loop (HITL) Flow](#human-in-the-loop-hitl-flow)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Deliverables](#deliverables)
- [Team](#team)

---

## Architecture

| Layer | Technology | Port |
|---|---|---|
| **Frontend** | React 19 + TypeScript + Tailwind CSS + shadcn/ui | 5173 |
| **Backend API** | Python FastAPI (unified REST API) | 3001 |
| **Agent Pipeline** | Python (5 sequential agents, Pydantic-validated) | in-process |
| **MCP Servers** | Node.js `@modelcontextprotocol/sdk` (3 servers) | stdio |
| **Intelligence/ML** | Python (statsforecast, NumPy, Pandas) | in-process |
| **HITL Resume API** | Python FastAPI | 8002 |
| **Data Store** | In-memory (production: Supabase Postgres) | — |

**Data flow:**
```
User (React UI) → Vite Proxy → FastAPI Backend (:3001) → Agent Orchestrator
    → Agent 1 (Intake) → Agent 2 (Quality) → Agent 3 (History) → Agent 4 (Decision)
    → HITL Check → Agent 5 (Executor) → PO Created + Notifications Sent
```

Each agent invokes **MCP tool servers** (ERP, Audit, Comms) to read/write structured data and logs an immutable audit entry before returning.

---

## Quick Start

### Prerequisites
- **Node.js** >= 18
- **Python** >= 3.10
- **npm** and **pip**

### 1. Clone and Install

```bash
git clone https://github.com/samaldo-coder/SupplierSense-AI.git
cd SupplierSense-AI

# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..

# MCP server dependencies
cd mcp && npm install && cd ..
```

### 2. Generate Seed Data

```bash
cd backend && python data/generate_data.py && cd ..
```

This creates `timeseries.csv` with 180 days of synthetic delay data for 10 suppliers.

### 3. Start the Backend

```bash
cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 3001 --reload
```

### 4. Start the Frontend

```bash
cd frontend && npm run dev
```

### 5. (Optional) Start the HITL Resume API

```bash
python -m uvicorn agents.resume_api:app --host 0.0.0.0 --port 8002 --reload
```

### 6. Open the App

Navigate to **http://localhost:5173**. Select a role to log in:
- **Warehouse Associate** (Ana Torres) — report disruptions
- **QC Manager** (Marcus Chen) — monitor pipelines, trigger AI scans
- **Director** (James Rivera) — approve/reject supplier swaps

### One-Command Start

```bash
chmod +x start.sh && ./start.sh
```

---

## Agent Pipeline

| # | Agent | Responsibility | Key Tools (MCP) |
|---|---|---|---|
| 1 | **Intake** | Parse event, enrich with supplier profile, 1-sentence summary | `get_supplier_profile` |
| 2 | **Quality** | Check cert expiry, compute quality sub-score (0-100) | `get_quality_certs`, `get_parts_by_supplier` |
| 3 | **History** | Run forecasts + anomaly detection, derive trend and risk index | `get_forecast`, `get_anomaly_status` |
| 4 | **Decision** | Composite risk score, escalation rules, pick best alt supplier | `query_avl`, `get_parts_by_supplier` |
| 5 | **Executor** | Create PO, swap supplier assignment, send notifications | `create_purchase_order`, `update_supplier_assignment` |

### Composite Score Formula
```
score = 0.35 * quality_sub_score
      + 0.25 * (1 - forecast_confidence) * 100
      + 0.25 * (anomaly_votes / 3) * 100
      + 0.15 * risk_index_score
```

### Escalation Rules (priority order)
1. RED financial + expired cert → **ESCALATE_TO_VP** (HITL required)
2. WORSENING trend + 2+ anomaly votes → **ESCALATE_TO_DIRECTOR** (HITL required)
3. Score >= 70 → **ESCALATE_TO_DIRECTOR** (HITL required)
4. Expired cert alone → **ESCALATE_TO_DIRECTOR** (HITL required)
5. Otherwise → **APPROVE** (auto-execute)

---

## MCP Servers

Three MCP servers built with `@modelcontextprotocol/sdk`:

| Server | File | Tools |
|---|---|---|
| **ERP** | `mcp/erp-server.js` | `get_supplier_profile`, `get_parts_by_supplier`, `query_avl`, `get_quality_certs`, `create_purchase_order`, `update_supplier_assignment`, `get_open_orders`, `list_suppliers` |
| **Audit** | `mcp/audit-server.js` | `log_audit_decision`, `get_audit_trail`, `list_pipeline_runs` |
| **Comms** | `mcp/comms-server.js` | `send_notification`, `create_approval_request`, `get_pending_approvals`, `decide_approval`, `get_notifications` |

Each server uses stdio transport and delegates to the FastAPI backend. The Python agent layer invokes these tools via HTTP wrappers (`agents/tools/*.py`).

### Running MCP Servers

```bash
# Individual servers (stdio transport)
node mcp/erp-server.js
node mcp/audit-server.js
node mcp/comms-server.js
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/suppliers` | GET | List all suppliers |
| `/api/suppliers/:id` | GET | Supplier profile |
| `/api/suppliers/:id/certs` | GET | Quality cert info |
| `/api/parts` | GET | Parts (filter by `?supplier_id=`) |
| `/api/avl/:part_id` | GET | Approved vendor list for a part |
| `/api/events` | GET/POST | Supplier disruption events |
| `/api/pipeline/run` | POST | Trigger agent pipeline for an event |
| `/api/auto-scan` | POST | AI disruption scan (all suppliers) |
| `/api/approvals` | GET/POST | HITL approval requests |
| `/api/approvals/:id/decide` | PATCH | Director approve/reject |
| `/api/audit/:run_id` | GET | Immutable audit trail |
| `/api/purchase-orders` | GET/POST | Purchase orders |
| `/api/notifications` | GET | Notifications by role |
| `/api/dashboard/stats` | GET | Aggregate statistics |
| `/api/forecasts/:supplier_id` | GET | Per-supplier delay forecast |
| `/api/anomalies/:supplier_id` | GET | Per-supplier anomaly detection |

---

## User Roles and Dashboards

| Role | User | Dashboard Features |
|---|---|---|
| **Warehouse Associate** | Ana Torres | Report disruptions, log shipments, trigger pipeline on events |
| **QC Manager** | Marcus Chen | Monitor agent pipelines, run AI auto-detect scans, view audit trails |
| **Director** | James Rivera | Approve/reject escalations, view risk scores, trigger AI scan |

---

## Human-in-the-Loop (HITL) Flow

```
Pipeline runs Agents 1-4
    |
    +-> Agent 4 Decision: hitl_required?
         |
    YES -+-> POST /api/approvals (state saved, notification sent)
         |-> Pipeline PAUSES
         |-> Director sees approval in React UI
         |-> Director clicks Approve/Reject
         |-> PATCH /api/approvals/:id/decide
         |-> Backend calls POST localhost:8002/resume
         |-> Resume API loads state, runs Agent 5 only
         |-> PO created, notifications sent
         |
    NO --+-> Agent 5 runs immediately inline
         |-> PO created, notifications sent
```

---

## Project Structure

```
supplyguard-ai/
├── agents/                     # 5-agent pipeline
│   ├── orchestrator.py         # Sequential pipeline with HITL
│   ├── intake_agent.py         # Agent 1
│   ├── quality_agent.py        # Agent 2
│   ├── supplier_history_agent.py # Agent 3
│   ├── decision_agent.py       # Agent 4 (HITL trigger)
│   ├── executor_agent.py       # Agent 5
│   ├── resume_api.py           # HITL resume endpoint (:8002)
│   ├── run.py                  # CLI entry point
│   ├── utils.py                # LLM retry, scoring, fallback
│   └── tools/                  # MCP tool wrappers
│       ├── erp_tools.py
│       ├── audit_tools.py
│       ├── comms_tools.py
│       └── data_tools.py
├── backend/
│   ├── api/main.py             # FastAPI backend (all endpoints)
│   ├── data/generate_data.py   # Synthetic data generator
│   └── intelligence/           # ML modules
│       ├── anomaly.py          # 3-method anomaly ensemble
│       ├── forecast.py         # AutoARIMA forecasting
│       └── risk_score.py       # Risk computation
├── mcp/                        # MCP servers (@modelcontextprotocol/sdk)
│   ├── erp-server.js           # ERP data tools (8 tools)
│   ├── audit-server.js         # Audit trail tools (3 tools)
│   └── comms-server.js         # Notifications + approvals (5 tools)
├── frontend/
│   └── src/
│       ├── App.tsx             # Role-based routing
│       ├── api/index.ts        # API service layer
│       └── components/
│           ├── auth/LoginPage.tsx
│           └── dashboard/
│               ├── DirectorDashboard.tsx
│               ├── QCManagerDashboard.tsx
│               └── WarehouseDashboard.tsx
├── contracts/schemas.py        # Shared Pydantic models
├── db/
│   ├── schema.sql              # Postgres DDL
│   └── seed.sql                # Seed data
├── docs/
│   ├── technical_design_document.docx
│   ├── governance_safety_brief.docx
│   ├── business_sketch.docx
│   ├── next_steps_pilot_plan.docx
│   ├── tco_yoy_cost_optimization.docx
│   ├── tco_cost_model_financials.docx
│   ├── tco_integration_sla.docx
│   ├── tco_licensing_legal.docx
│   └── example_decision_logs/
│       ├── run_green.json
│       ├── run_yellow.json
│       └── run_red.json
├── tests/
│   ├── test_scoring_unit.py
│   ├── test_pipeline_integration.py
│   ├── test_hitl_flow.py
│   └── fixtures/
├── requirements.txt
├── start.sh
└── README.md
```

---

## Testing

### Unit Tests (no network, no LLM)
```bash
pytest tests/test_scoring_unit.py -v
```

### Integration Tests (requires full stack running)
```bash
pytest tests/test_pipeline_integration.py -v -m integration
```

### CLI Pipeline Test
```bash
# Using test fixtures (offline)
python agents/run.py --fixture event_red
python agents/run.py --fixture event_green
python agents/run.py --fixture event_yellow

# Using backend event
python agents/run.py --event_id c3000000-0000-0000-0000-000000000001
```

---

## Deliverables

| # | Deliverable | Location |
|---|---|---|
| 1 | 10-minute pitch | (video/live presentation) |
| 2 | Runnable demo | This repository |
| 3 | Code repository + README | This file |
| 4 | Technical design document | `docs/technical_design_document.docx` |
| 5 | Governance and safety brief | `docs/governance_safety_brief.docx` |
| 6 | Business sketch | `docs/business_sketch.docx` |
| 7 | Next steps / pilot plan | `docs/next_steps_pilot_plan.docx` |
| 8 | Example decision logs | `docs/example_decision_logs/` |
| 9 | MCP server definitions | `mcp/` directory |
| **Bonus** | TCO cost optimization | `docs/tco_*.docx` (4 documents) |

---

## Team

| Role | Owner |
|---|---|
| P1 — Project Lead / Systems | Sahithi Maldoddi |
| P2 — Frontend Engineer | — |
| P3 — AI Agent Architect | — |
| P4 — Backend / MCP | — |
| P5 — Data / ML | — |
