# SupplyGuard AI

**AI-powered supply chain disruption detection & response system.**

Built for the Cummins Xtern 2026 competition. Detects supplier disruptions in real time, routes them through a 5-agent AI pipeline, requests human-in-the-loop (HITL) approval, then executes a supplier swap — with a full immutable audit trail.

## Quick Start

```bash
chmod +x start.sh
./start.sh
```

This starts the backend (port 3001) and frontend (port 5173).

**Manual startup:**

```bash
# 1. Generate seed data
cd backend && python data/generate_data.py && cd ..

# 2. Start backend
cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 3001 --reload &

# 3. Start frontend
cd frontend && npm install && npm run dev &
```

## Architecture

| Layer | Tech | Port |
|---|---|---|
| **Frontend** | React + TypeScript + Tailwind + shadcn/ui | 5173 |
| **Backend** | Python FastAPI (unified API + data/ML) | 3001 |
| **Agents** | Python (CrewAI-style pipeline, 5 agents) | — |
| **HITL Resume** | FastAPI (resumes pipeline after approval) | 8002 |

## Agent Pipeline

1. **Intake Agent** — Parses event, enriches with supplier profile
2. **Quality Agent** — Checks certifications, computes quality score
3. **Supplier History Agent** — Forecasts + anomaly detection
4. **Decision Agent** — Composite risk score + escalation rules
5. **Executor Agent** — Creates PO, updates supplier assignment (requires approval if HITL)

## Key API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/suppliers` | GET | List all suppliers |
| `/api/events` | GET/POST | Supplier events |
| `/api/pipeline/run` | POST | Trigger agent pipeline |
| `/api/auto-scan` | POST | AI disruption scan (all suppliers) |
| `/api/approvals` | GET | Pending HITL approvals |
| `/api/approvals/:id/decide` | PATCH | Director approve/reject |
| `/api/audit/:run_id` | GET | Immutable audit trail |

## Dashboards

- **Director** — Approve/reject escalations, view risk scores, trigger AI scan
- **QC Manager** — Monitor agent pipelines, run AI auto-detect scans
- **Warehouse** — Report disruptions, log shipments

## Team

| Role | Owner |
|---|---|
| P1 — Project Lead | — |
| P2 — Frontend | — |
| P3 — AI Agent Architect | — |
| P4 — Backend/MCP | — |
| P5 — Data/ML | — |
