-- SupplyGuard AI — Full Database Schema
-- Compatible with Supabase (Postgres) free tier
-- Run this in Supabase SQL editor or via psql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ═══════════════════════════════════════════════
-- TABLE: suppliers
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_name  TEXT NOT NULL,
    country        TEXT NOT NULL,
    tier           INT NOT NULL CHECK (tier IN (1, 2, 3)),
    financial_health TEXT NOT NULL CHECK (financial_health IN ('GREEN', 'YELLOW', 'RED')),
    lead_time_days INT NOT NULL DEFAULT 7,
    unit_cost      NUMERIC(10,2) NOT NULL DEFAULT 100.00,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    quality_cert_type  TEXT DEFAULT 'ISO 9001',
    quality_cert_expiry DATE,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- ═══════════════════════════════════════════════
-- TABLE: parts
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS parts (
    part_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    part_number    TEXT NOT NULL UNIQUE,
    part_name      TEXT NOT NULL,
    category       TEXT NOT NULL,
    primary_supplier_id UUID REFERENCES suppliers(supplier_id),
    factory        TEXT NOT NULL DEFAULT 'Columbus Plant',
    min_order_qty  INT NOT NULL DEFAULT 100,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- ═══════════════════════════════════════════════
-- TABLE: approved_vendor_list (AVL)
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS approved_vendor_list (
    avl_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    part_id        UUID NOT NULL REFERENCES parts(part_id),
    supplier_id    UUID NOT NULL REFERENCES suppliers(supplier_id),
    lead_time_days INT NOT NULL DEFAULT 7,
    unit_cost      NUMERIC(10,2) NOT NULL,
    quality_cert_expiry DATE,
    geographic_risk NUMERIC(3,2) DEFAULT 0.50,
    is_approved    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(part_id, supplier_id)
);

-- ═══════════════════════════════════════════════
-- TABLE: supplier_events
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS supplier_events (
    event_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id    UUID NOT NULL REFERENCES suppliers(supplier_id),
    event_type     TEXT NOT NULL CHECK (event_type IN ('DELIVERY_MISS', 'FINANCIAL_FLAG', 'QUALITY_HOLD')),
    delay_days     INT NOT NULL DEFAULT 0,
    description    TEXT NOT NULL,
    severity       TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- ═══════════════════════════════════════════════
-- TABLE: audit_log (immutable — no UPDATE/DELETE allowed)
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS audit_log (
    entry_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id         TEXT NOT NULL,
    agent_name     TEXT NOT NULL,
    inputs         JSONB NOT NULL DEFAULT '{}',
    outputs        JSONB NOT NULL DEFAULT '{}',
    confidence     NUMERIC(4,3) NOT NULL DEFAULT 0.000,
    rationale      TEXT NOT NULL DEFAULT '',
    hitl_actor     TEXT,
    timestamp      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_run_id ON audit_log(run_id);

-- ═══════════════════════════════════════════════
-- TABLE: pending_approvals
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS pending_approvals (
    approval_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id         TEXT NOT NULL UNIQUE,
    state_json     JSONB NOT NULL DEFAULT '{}',
    summary        TEXT NOT NULL DEFAULT '',
    recommended_supplier_id UUID,
    status         TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    decided_by     TEXT,
    decision_note  TEXT,
    decided_at     TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- ═══════════════════════════════════════════════
-- TABLE: purchase_orders
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id    UUID NOT NULL REFERENCES suppliers(supplier_id),
    part_id        UUID NOT NULL REFERENCES parts(part_id),
    quantity       INT NOT NULL,
    approved_by    TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'CREATED' CHECK (status IN ('CREATED', 'CONFIRMED', 'SHIPPED', 'DELIVERED')),
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- ═══════════════════════════════════════════════
-- TABLE: notifications (simulated Teams/comms)
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_role TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    title          TEXT NOT NULL,
    body           TEXT NOT NULL DEFAULT '',
    metadata       JSONB DEFAULT '{}',
    is_read        BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- ═══════════════════════════════════════════════
-- TABLE: timeseries (supplier delivery delay history)
-- ═══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS timeseries (
    id             SERIAL PRIMARY KEY,
    supplier_id    UUID NOT NULL REFERENCES suppliers(supplier_id),
    date           DATE NOT NULL,
    delay_days     NUMERIC(6,2) NOT NULL DEFAULT 0,
    UNIQUE(supplier_id, date)
);

-- Immutability trigger for audit_log
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is immutable — UPDATE and DELETE are forbidden';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS no_audit_update ON audit_log;
CREATE TRIGGER no_audit_update
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
