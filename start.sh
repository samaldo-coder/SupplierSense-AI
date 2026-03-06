#!/bin/bash
# SupplyGuard AI — One-command startup
# Usage: ./start.sh
# Stops all services: Ctrl+C (kills all child processes)

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════╗"
echo "║         SupplyGuard AI — Starting All Services       ║"
echo "╚══════════════════════════════════════════════════════╝"

# ── 0. Check prerequisites ─────────────────────────
echo ""
echo "▸ Checking prerequisites..."

# Find a working Python with pandas available
PYTHON=""
for candidate in python3 /opt/anaconda3/bin/python python; do
    if command -v "$candidate" &> /dev/null; then
        if "$candidate" -c "import pandas" 2>/dev/null; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "✗ No Python with pandas found. Install deps: pip install -r requirements.txt"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "✗ node not found. Install Node.js 18+."
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "✗ .env file not found! Copy .env.example to .env and add your OpenAI key."
    exit 1
fi

echo "✓ Python found: $PYTHON ($($PYTHON --version 2>&1))"
echo "✓ node found: $(node --version)"
echo "✓ .env found"

# ── 1. Generate timeseries data if missing ─────────
if [ ! -f "$PROJECT_ROOT/backend/timeseries.csv" ]; then
    echo ""
    echo "▸ Generating timeseries data..."
    cd "$PROJECT_ROOT/backend"
    $PYTHON data/generate_data.py
    cd "$PROJECT_ROOT"
    echo "✓ timeseries.csv generated"
fi

# ── 2. Install frontend deps if needed ─────────────
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo ""
    echo "▸ Installing frontend dependencies..."
    cd "$PROJECT_ROOT/frontend"
    npm install
    cd "$PROJECT_ROOT"
    echo "✓ Frontend dependencies installed"
fi

# ── Trap to kill all background jobs on exit ───────
cleanup() {
    echo ""
    echo "▸ Shutting down all services..."
    kill $(jobs -p) 2>/dev/null
    wait 2>/dev/null
    echo "✓ All services stopped."
}
trap cleanup EXIT INT TERM

# ── 3. Start Backend (port 3001) ───────────────────
echo ""
echo "▸ Starting Backend API on http://localhost:3001 ..."
cd "$PROJECT_ROOT/backend"
$PYTHON -m uvicorn api.main:app --host 0.0.0.0 --port 3001 --reload &
BACKEND_PID=$!
cd "$PROJECT_ROOT"

# ── 4. Start Agent Resume API (port 8002) ──────────
echo "▸ Starting Agent Resume API on http://localhost:8002 ..."
$PYTHON -m uvicorn agents.resume_api:app --host 0.0.0.0 --port 8002 --reload &
RESUME_PID=$!

# ── 5. Start Frontend (port 5173) ──────────────────
echo "▸ Starting Frontend on http://localhost:5173 ..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

# ── 6. Wait for services to start ──────────────────
echo ""
echo "▸ Waiting for services to start..."
sleep 4

# ── 7. Health checks ───────────────────────────────
echo ""
BACKEND_OK=false
RESUME_OK=false

if curl -sf http://localhost:3001/health > /dev/null 2>&1; then
    BACKEND_OK=true
    echo "✓ Backend API:       http://localhost:3001  (healthy)"
else
    echo "✗ Backend API:       http://localhost:3001  (not responding)"
fi

if curl -sf http://localhost:8002/health > /dev/null 2>&1; then
    RESUME_OK=true
    echo "✓ Agent Resume API:  http://localhost:8002  (healthy)"
else
    echo "✗ Agent Resume API:  http://localhost:8002  (not responding)"
fi

echo "✓ Frontend:          http://localhost:5173  (starting...)"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║            SupplyGuard AI — All Services Up          ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Frontend:    http://localhost:5173                   ║"
echo "║  Backend:     http://localhost:3001                   ║"
echo "║  Resume API:  http://localhost:8002                   ║"
echo "║                                                      ║"
echo "║  Demo flow:                                          ║"
echo "║  1. Open http://localhost:5173                       ║"
echo "║  2. Login as any role                                ║"
echo "║  3. Submit a disruption event                        ║"
echo "║  4. Watch the AI pipeline process it                 ║"
echo "║  5. If HITL: login as Director to approve/reject     ║"
echo "║                                                      ║"
echo "║  CLI agent:                                          ║"
echo "║  python agents/run.py --fixture event_red            ║"
echo "║  python agents/run.py --fixture event_green          ║"
echo "║                                                      ║"
echo "║  Press Ctrl+C to stop all services                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Keep the script running until interrupted
wait
