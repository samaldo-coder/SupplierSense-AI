/**
 * SupplyGuard AI — Frontend API Service Layer
 * All calls go through the Vite proxy to localhost:3001
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Types ────────────────────────────────────────────────

export interface Supplier {
  supplier_id: string
  supplier_name: string
  country: string
  tier: number
  financial_health: 'GREEN' | 'YELLOW' | 'RED'
  lead_time_days: number
  unit_cost: number
  is_active: boolean
  quality_cert_type: string
  quality_cert_expiry: string
}

export interface SupplierEvent {
  event_id: string
  supplier_id: string
  event_type: 'DELIVERY_MISS' | 'FINANCIAL_FLAG' | 'QUALITY_HOLD'
  delay_days: number
  description: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
}

export interface AuditEntry {
  entry_id: string
  run_id: string
  agent_name: string
  inputs: Record<string, unknown>
  outputs: Record<string, unknown>
  confidence: number
  rationale: string
  hitl_actor: string | null
  timestamp: string
}

export interface Approval {
  approval_id: string
  run_id: string
  state_json: Record<string, unknown>
  summary: string
  recommended_supplier_id: string | null
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  decided_by: string | null
  decision_note: string | null
  decided_at: string | null
  created_at: string
}

export interface PurchaseOrder {
  po_id: string
  supplier_id: string
  part_id: string
  quantity: number
  approved_by: string
  status: string
  created_at: string
}

export interface Notification {
  notification_id: string
  recipient_role: string
  notification_type: string
  title: string
  body: string
  metadata: Record<string, unknown>
  is_read: boolean
  created_at: string
}

export interface DashboardStats {
  total_events: number
  critical_events: number
  pending_approvals: number
  approved_count: number
  total_purchase_orders: number
  active_suppliers: number
  red_suppliers: number
  total_audit_entries: number
  unread_notifications: number
}

export interface PipelineRun {
  run_id: string
  agents_completed: string[]
  started_at: string
  last_update: string
}

// ─── Suppliers ────────────────────────────────────────────

export const getSuppliers = () =>
  api.get<Supplier[]>('/suppliers').then(r => r.data)

export const getSupplier = (id: string) =>
  api.get<Supplier>(`/suppliers/${id}`).then(r => r.data)

// ─── Events ───────────────────────────────────────────────

export const getEvents = () =>
  api.get<SupplierEvent[]>('/events').then(r => r.data)

export const getEvent = (id: string) =>
  api.get<SupplierEvent>(`/events/${id}`).then(r => r.data)

// ─── Audit Trail ──────────────────────────────────────────

export const getAuditTrail = (runId: string) =>
  api.get<AuditEntry[]>(`/audit/${runId}`).then(r => r.data)

// ─── Approvals ────────────────────────────────────────────

export const getApprovals = (status?: string) =>
  api.get<Approval[]>('/approvals', { params: status ? { status } : {} }).then(r => r.data)

export const decideApproval = (approvalId: string, decision: string, note: string, directorId: string) =>
  api.patch(`/approvals/${approvalId}/decide`, {
    decision,
    note,
    director_id: directorId,
  }).then(r => r.data)

// ─── Purchase Orders ──────────────────────────────────────

export const getPurchaseOrders = () =>
  api.get<PurchaseOrder[]>('/purchase-orders').then(r => r.data)

// ─── Notifications ────────────────────────────────────────

export const getNotifications = (role?: string, unreadOnly = false) =>
  api.get<Notification[]>('/notifications', {
    params: { ...(role ? { role } : {}), ...(unreadOnly ? { unread_only: true } : {}) },
  }).then(r => r.data)

export const markNotificationRead = (id: string) =>
  api.patch(`/notifications/${id}/read`).then(r => r.data)

// ─── Dashboard ────────────────────────────────────────────

export const getDashboardStats = () =>
  api.get<DashboardStats>('/dashboard/stats').then(r => r.data)

export const getPipelineRuns = () =>
  api.get<PipelineRun[]>('/pipeline/runs').then(r => r.data)

// ─── Risk / Forecasts ─────────────────────────────────────

export const getSupplierRisk = (supplierId: string) =>
  api.get(`/forecasts/${supplierId}`).then(r => r.data)

export const getSupplierAnomaly = (supplierId: string) =>
  api.get(`/anomalies/${supplierId}`).then(r => r.data)

// ─── Pipeline Trigger ─────────────────────────────────────

export interface PipelineResult {
  status: string
  run_id?: string
  composite_score?: number
  action?: string
  hitl_required?: boolean
  paused_for_hitl?: boolean
  po_id?: string | null
  audit_entries?: number
  error?: string | null
}

export const triggerPipeline = (eventId: string) =>
  api.post<PipelineResult>('/pipeline/run', { event_id: eventId }).then(r => r.data)

export const createEvent = (event: Partial<SupplierEvent>) =>
  api.post<SupplierEvent>('/events', event).then(r => r.data)

// ─── Auto-Scan (AI Disruption Detection) ─────────────────

export interface ScanFinding {
  supplier_id: string
  supplier_name: string
  status: 'OK' | 'FLAGGED' | 'ALREADY_FLAGGED'
  reason?: string
  anomaly_votes: number
  predicted_delay: number
  severity?: string
  event_type?: string
  event_id?: string
  event_created: boolean
  pipeline_result?: {
    run_id?: string
    action?: string
    composite_score?: number
    hitl_required?: boolean
    paused_for_hitl?: boolean
    po_id?: string | null
    error?: string
  }
}

export interface AutoScanResult {
  scan_time: string
  suppliers_scanned: number
  events_created: number
  pipelines_triggered: number
  findings: ScanFinding[]
}

export const triggerAutoScan = () =>
  api.post<AutoScanResult>('/auto-scan').then(r => r.data)

export const resetAutoScan = () =>
  api.post('/auto-scan/reset').then(r => r.data)

export default api
