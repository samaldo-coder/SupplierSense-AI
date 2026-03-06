import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Shield,
  Activity,
  BarChart3,
  Users,
  Package,
  XCircle,
  Radar,
} from 'lucide-react'
import {
  getApprovals,
  decideApproval,
  getDashboardStats,
  getSuppliers,
  getEvents,
  getPipelineRuns,
  triggerAutoScan,
  type Approval,
  type DashboardStats,
  type Supplier,
  type SupplierEvent,
  type PipelineRun,
} from '../../api'
import { useGlobalToast } from '../ui/Toast'

// Format a run_id or timestamp into a short human label
const fmt = (iso?: string) =>
  iso
    ? new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    : ''

export default function DirectorDashboard() {
  const toast = useGlobalToast()
  const [selectedTab, setSelectedTab] = useState('approvals')
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [events, setEvents] = useState<SupplierEvent[]>([])
  const [pipelineRuns, setPipelineRuns] = useState<PipelineRun[]>([])
  const [decidingId, setDecidingId] = useState<string | null>(null)
  const [decisionNote, setDecisionNote] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isScanning, setIsScanning] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const [approvalsData, statsData, suppliersData, eventsData, runsData] =
        await Promise.all([
          getApprovals().catch(() => []),
          getDashboardStats().catch(() => null),
          getSuppliers().catch(() => []),
          getEvents().catch(() => []),
          getPipelineRuns().catch(() => []),
        ])
      setApprovals(approvalsData)
      setStats(statsData)
      setSuppliers(suppliersData)
      setEvents(eventsData)
      setPipelineRuns(runsData)
    } catch {
      console.warn('Backend may be offline, using empty state')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000) // Poll every 5s
    return () => clearInterval(interval)
  }, [fetchData])

  const handleDecision = async (approvalId: string, decision: 'approved' | 'rejected') => {
    try {
      await decideApproval(approvalId, decision, decisionNote, 'director_james')
      setDecidingId(null)
      setDecisionNote('')
      await fetchData()
      if (decision === 'approved') {
        toast.success('Approved — Agent 5 will execute the supplier swap.')
      } else {
        toast.info('Rejected — pipeline halted, no PO created.')
      }
    } catch (err) {
      console.error('Decision failed:', err)
      toast.error('Decision failed — please try again.')
    }
  }

  const pendingApprovals = approvals.filter(a => a.status === 'PENDING')
  const decidedApprovals = approvals.filter(a => a.status !== 'PENDING')

  const agentStepNames = ['intake_agent', 'quality_agent', 'supplier_history_agent', 'decision_agent', 'executor_agent']

  // Helper: extract pipeline details from the saved state_json in an approval
  const getPipelineDetail = (approval: Approval) => {
    const state = approval.state_json as Record<string, any> | undefined
    if (!state) return null
    const decision = state.decision as Record<string, any> | undefined
    const intake = state.intake as Record<string, any> | undefined
    const quality = state.quality as Record<string, any> | undefined
    const history = state.history as Record<string, any> | undefined

    const supplierProfile = intake?.supplier_profile as Record<string, any> | undefined
    const supplierName = supplierProfile?.supplier_name ?? 'Unknown Supplier'

    return {
      compositeScore: decision?.composite_score as number | undefined,
      action: decision?.action as string | undefined,
      rationale: decision?.rationale as string | undefined,
      supplierName,
      supplierId: intake?.supplier_id as string | undefined,
      eventType: intake?.event_type as string | undefined,
      delayDays: intake?.delay_days as number | undefined,
      certValid: quality?.cert_valid as boolean | undefined,
      qualityScore: quality?.quality_sub_score as number | undefined,
      defectTrend: quality?.defect_trend as string | undefined,
      forecastTrend: history?.forecast_trend as string | undefined,
      anomalyVotes: history?.anomaly_votes as number | undefined,
      riskIndex: history?.risk_index_score as number | undefined,
    }
  }

  // SVG gauge helper
  const RiskGauge = ({ score }: { score: number }) => {
    const clampedScore = Math.max(0, Math.min(100, score))
    const radius = 50
    const circumference = Math.PI * radius // half circle
    const progress = (clampedScore / 100) * circumference
    const color =
      clampedScore >= 70 ? '#ef4444' :
      clampedScore >= 40 ? '#f59e0b' : '#10b981'

    return (
      <div className="flex flex-col items-center">
        <svg width="120" height="70" viewBox="0 0 120 70">
          {/* Background arc */}
          <path
            d="M 10 65 A 50 50 0 0 1 110 65"
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="8"
            strokeLinecap="round"
          />
          {/* Progress arc */}
          <path
            d="M 10 65 A 50 50 0 0 1 110 65"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${progress} ${circumference}`}
            style={{ transition: 'stroke-dasharray 0.8s ease-out' }}
          />
        </svg>
        <div className="text-center -mt-6">
          <span className="text-2xl font-bold" style={{ color }}>{clampedScore.toFixed(0)}</span>
          <span className="text-xs text-gray-400 block">/100 risk</span>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6 flex items-center justify-center h-64">
        <motion.div
          className="w-8 h-8 border-2 border-purple-400/30 border-t-purple-400 rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Director Command Center</h1>
          <p className="text-gray-400 font-mono text-sm">AI-powered supply chain oversight</p>
        </div>
        <div className="flex items-center space-x-3">
          <motion.button
            onClick={async () => {
              setIsScanning(true)
              try {
                const result = await triggerAutoScan()
                if (result.events_created > 0) {
                  toast.warning(`AI detected ${result.events_created} disruption(s) — check approval queue`)
                  fetchData()
                } else {
                  toast.success('All suppliers healthy — no disruptions detected')
                }
              } catch {
                toast.error('Auto-scan failed')
              } finally {
                setIsScanning(false)
              }
            }}
            disabled={isScanning}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              isScanning
                ? 'bg-cyan-500/20 text-cyan-300 cursor-wait'
                : 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20'
            }`}
            whileHover={!isScanning ? { scale: 1.05 } : {}}
            whileTap={!isScanning ? { scale: 0.95 } : {}}
          >
            <motion.div
              animate={isScanning ? { rotate: 360 } : {}}
              transition={isScanning ? { duration: 1, repeat: Infinity, ease: 'linear' } : {}}
            >
              <Radar className="w-4 h-4" />
            </motion.div>
            <span>{isScanning ? 'Scanning...' : 'AI Scan'}</span>
          </motion.button>
          {pendingApprovals.length > 0 && (
            <motion.div
              className="flex items-center space-x-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg"
              animate={{ scale: [1, 1.02, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-red-300 font-medium">{pendingApprovals.length} Pending Approval{pendingApprovals.length > 1 ? 's' : ''}</span>
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Active Suppliers', value: stats.active_suppliers, icon: Users, color: 'text-blue-400' },
            { label: 'Critical Events', value: stats.critical_events, icon: AlertTriangle, color: 'text-red-400' },
            { label: 'Pending Approvals', value: stats.pending_approvals, icon: Clock, color: 'text-amber-400' },
            { label: 'Purchase Orders', value: stats.total_purchase_orders, icon: Package, color: 'text-emerald-400' },
          ].map((card, i) => (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">{card.label}</div>
                  <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
                </div>
                <card.icon className={`w-8 h-8 ${card.color} opacity-50`} />
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-white/5 p-1 rounded-lg">
        {[
          { id: 'approvals', label: 'Approval Queue', icon: Shield, badge: pendingApprovals.length },
          { id: 'pipeline', label: 'Agent Pipeline', icon: Activity },
          { id: 'suppliers', label: 'Supplier Risk', icon: BarChart3 },
          { id: 'events', label: 'Events', icon: AlertTriangle },
        ].map(tab => {
          const Icon = tab.icon
          return (
            <motion.button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedTab === tab.id
                  ? 'bg-white/10 text-white border border-white/20'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.badge ? (
                <span className="ml-1 px-1.5 py-0.5 bg-red-500/30 text-red-300 rounded-full text-xs">{tab.badge}</span>
              ) : null}
            </motion.button>
          )
        })}
      </div>

      {/* ═══ APPROVALS TAB ═══ */}
      {selectedTab === 'approvals' && (
        <div className="space-y-4">
          {pendingApprovals.length === 0 && decidedApprovals.length === 0 ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-12 text-center">
              <Shield className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl text-white mb-2">No Approvals Yet</h3>
              <p className="text-gray-400">Run the agent pipeline to generate approval requests. Agents will escalate decisions that need your review.</p>
            </motion.div>
          ) : (
            <>
              {pendingApprovals.map((approval, index) => {
                const detail = getPipelineDetail(approval)
                const recommendedSupplier = approval.recommended_supplier_id
                  ? suppliers.find(s => s.supplier_id === approval.recommended_supplier_id)
                  : null

                return (
                <motion.div
                  key={approval.approval_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass-card p-6 border-l-4 border-amber-500"
                >
                  {/* Header row */}
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <div className="flex items-center space-x-3">
                        <motion.span
                          className="px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full text-sm font-medium"
                          animate={{ scale: [1, 1.05, 1] }}
                          transition={{ duration: 2, repeat: Infinity }}
                        >
                          ⏳ PENDING APPROVAL
                        </motion.span>
                        {detail?.action && (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            detail.action === 'ESCALATE_TO_VP' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'
                          }`}>
                            {detail.action.replace(/_/g, ' ')}
                          </span>
                        )}
                        <span className="text-gray-400 text-sm">📅 {fmt(approval.created_at)}</span>
                      </div>
                      <p className="text-white mt-2">{approval.summary || 'Agent pipeline requires director approval'}</p>
                    </div>
                    <div className="text-right text-sm text-gray-400">
                      {new Date(approval.created_at).toLocaleString()}
                    </div>
                  </div>

                  {/* Risk Score Gauge + Detail Grid */}
                  {detail && (
                    <div className="flex items-start space-x-6 mb-4">
                      {detail.compositeScore != null && (
                        <div className="shrink-0">
                          <RiskGauge score={detail.compositeScore} />
                        </div>
                      )}
                      <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-3">
                        {detail.supplierName && (
                          <div className="bg-white/5 border border-white/10 rounded-lg p-3">
                            <div className="text-xs text-gray-400">Flagged Supplier</div>
                            <div className="text-sm text-white font-medium">{detail.supplierName}</div>
                            {detail.eventType && <div className="text-xs text-gray-400 mt-0.5">{detail.eventType} · {detail.delayDays}d delay</div>}
                          </div>
                        )}
                        {detail.certValid !== undefined && (
                          <div className="bg-white/5 border border-white/10 rounded-lg p-3">
                            <div className="text-xs text-gray-400">Quality Cert</div>
                            <div className={`text-sm font-medium ${detail.certValid ? 'text-emerald-400' : 'text-red-400'}`}>
                              {detail.certValid ? '✅ Valid' : '❌ Expired/Missing'}
                            </div>
                            {detail.qualityScore != null && (
                              <div className="text-xs text-gray-400 mt-0.5">Score: {detail.qualityScore.toFixed(0)}/100</div>
                            )}
                          </div>
                        )}
                        {detail.forecastTrend && (
                          <div className="bg-white/5 border border-white/10 rounded-lg p-3">
                            <div className="text-xs text-gray-400">Forecast Trend</div>
                            <div className={`text-sm font-medium ${
                              detail.forecastTrend === 'WORSENING' ? 'text-red-400' :
                              detail.forecastTrend === 'IMPROVING' ? 'text-emerald-400' : 'text-gray-300'
                            }`}>
                              {detail.forecastTrend === 'WORSENING' ? '📈 Worsening' :
                               detail.forecastTrend === 'IMPROVING' ? '📉 Improving' : '➡️ Stable'}
                            </div>
                            {detail.anomalyVotes != null && (
                              <div className="text-xs text-gray-400 mt-0.5">Anomaly votes: {detail.anomalyVotes}/3</div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* AI Rationale */}
                  {detail?.rationale && (
                    <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3 mb-4">
                      <div className="text-xs text-blue-400 font-medium mb-1">🤖 AI Rationale</div>
                      <p className="text-sm text-gray-300">{detail.rationale}</p>
                    </div>
                  )}

                  {/* Recommended supplier info */}
                  {approval.recommended_supplier_id && (
                    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-3 mb-4">
                      <div className="text-xs text-emerald-400 font-medium mb-1">Recommended Alternative Supplier</div>
                      <div className="text-sm text-white">
                        {recommendedSupplier
                          ? `${recommendedSupplier.supplier_name} (${recommendedSupplier.country}, ${recommendedSupplier.lead_time_days}d lead, $${recommendedSupplier.unit_cost})`
                          : 'Unknown supplier'}
                      </div>
                    </div>
                  )}

                  {/* Decision UI */}
                  <AnimatePresence>
                    {decidingId === approval.approval_id ? (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-3"
                      >
                        <textarea
                          value={decisionNote}
                          onChange={e => setDecisionNote(e.target.value)}
                          placeholder="Add decision notes (optional)..."
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:ring-1 focus:ring-purple-400"
                          rows={2}
                        />
                        <div className="flex space-x-3">
                          <motion.button
                            onClick={() => handleDecision(approval.approval_id, 'approved')}
                            className="flex-1 flex items-center justify-center space-x-2 py-3 bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 rounded-lg font-medium hover:bg-emerald-500/30"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <CheckCircle className="w-5 h-5" />
                            <span>Approve & Execute</span>
                          </motion.button>
                          <motion.button
                            onClick={() => handleDecision(approval.approval_id, 'rejected')}
                            className="flex-1 flex items-center justify-center space-x-2 py-3 bg-red-500/20 border border-red-500/30 text-red-300 rounded-lg font-medium hover:bg-red-500/30"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <XCircle className="w-5 h-5" />
                            <span>Reject</span>
                          </motion.button>
                          <motion.button
                            onClick={() => { setDecidingId(null); setDecisionNote('') }}
                            className="px-4 py-3 bg-white/10 border border-white/20 text-gray-300 rounded-lg hover:bg-white/15"
                            whileHover={{ scale: 1.02 }}
                          >
                            Cancel
                          </motion.button>
                        </div>
                      </motion.div>
                    ) : (
                      <motion.button
                        onClick={() => setDecidingId(approval.approval_id)}
                        className="w-full py-3 bg-linear-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 shadow-lg shadow-purple-500/25"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        Review & Decide
                      </motion.button>
                    )}
                  </AnimatePresence>
                </motion.div>
                )
              })}

              {/* Decided Approvals History */}
              {decidedApprovals.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Decision History</h3>
                  <div className="space-y-3">
                    {decidedApprovals.map((a, idx) => (
                      <div key={a.approval_id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-white font-medium">
                            Pipeline #{decidedApprovals.length - idx}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            a.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                          }`}>
                            {a.status}
                          </span>
                        </div>
                        <div className="text-sm text-gray-400">
                          {fmt(a.decided_at ?? a.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ═══ PIPELINE TAB ═══ */}
      {selectedTab === 'pipeline' && (
        <div className="space-y-4">
          {pipelineRuns.length === 0 ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-12 text-center">
              <Activity className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl text-white mb-2">No Pipeline Runs Yet</h3>
              <p className="text-gray-400">Run <code className="text-purple-400">python agents/run.py --fixture event_red</code> to start a pipeline.</p>
            </motion.div>
          ) : (
            pipelineRuns.map((run, idx) => (
              <motion.div
                key={run.run_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="glass-card p-6"
              >
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <span className="text-white font-semibold">
                      Pipeline #{pipelineRuns.length - idx}
                    </span>
                    <span className="ml-3 text-sm text-gray-400">
                      {fmt(run.started_at)} · {run.agents_completed.length}/{agentStepNames.length} agents
                    </span>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    run.agents_completed.length >= 5
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : 'bg-blue-500/20 text-blue-300'
                  }`}>
                    {run.agents_completed.length >= 5 ? '✅ Complete' : '⏳ In Progress'}
                  </span>
                </div>
                <div className="flex space-x-2">
                  {agentStepNames.map((step, i) => {
                    const done = run.agents_completed.includes(step)
                    return (
                      <div key={step} className="flex-1">
                        <div className={`h-2 rounded-full ${done ? 'bg-emerald-500' : 'bg-gray-700'}`} />
                        <div className={`text-xs mt-1 text-center ${done ? 'text-emerald-300' : 'text-gray-500'}`}>
                          {step.replace('_agent', '').replace('_', ' ')}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </motion.div>
            ))
          )}
        </div>
      )}

      {/* ═══ SUPPLIERS TAB ═══ */}
      {selectedTab === 'suppliers' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {suppliers.map((s, i) => (
            <motion.div
              key={s.supplier_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`glass-card p-4 border-l-4 ${
                s.financial_health === 'RED' ? 'border-red-500' :
                s.financial_health === 'YELLOW' ? 'border-amber-500' : 'border-emerald-500'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-white font-medium">{s.supplier_name}</div>
                  <div className="text-sm text-gray-400">{s.country} · Tier {s.tier}</div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  s.financial_health === 'RED' ? 'bg-red-500/20 text-red-300' :
                  s.financial_health === 'YELLOW' ? 'bg-amber-500/20 text-amber-300' :
                  'bg-emerald-500/20 text-emerald-300'
                }`}>
                  {s.financial_health}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 mt-3 text-center">
                <div>
                  <div className="text-xs text-gray-400">Lead Time</div>
                  <div className="text-sm text-white font-medium">{s.lead_time_days}d</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400">Unit Cost</div>
                  <div className="text-sm text-white font-medium">${s.unit_cost}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400">Cert</div>
                  <div className={`text-sm font-medium ${
                    new Date(s.quality_cert_expiry) < new Date() ? 'text-red-400' : 'text-emerald-400'
                  }`}>
                    {new Date(s.quality_cert_expiry) < new Date() ? 'Expired' : 'Valid'}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* ═══ EVENTS TAB ═══ */}
      {selectedTab === 'events' && (
        <div className="space-y-3">
          {events.map((e, i) => {
            const supplier = suppliers.find(s => s.supplier_id === e.supplier_id)
            return (
              <motion.div
                key={e.event_id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`glass-card p-4 border-l-4 ${
                  e.severity === 'CRITICAL' ? 'border-red-500' :
                  e.severity === 'HIGH' ? 'border-orange-500' :
                  e.severity === 'MEDIUM' ? 'border-amber-500' : 'border-emerald-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-white font-medium">{supplier?.supplier_name || 'Unknown Supplier'}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        e.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-300' :
                        e.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-300' :
                        e.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-emerald-500/20 text-emerald-300'
                      }`}>
                        {e.severity}
                      </span>
                      <span className="px-2 py-0.5 bg-white/10 text-gray-300 rounded text-xs">{e.event_type}</span>
                      {e.description.startsWith('[AUTO-DETECTED]') && (
                        <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 rounded text-xs flex items-center space-x-1">
                          <Radar className="w-3 h-3" />
                          <span>AI Detected</span>
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{e.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white">{e.delay_days}d</div>
                    <div className="text-xs text-gray-400">delay</div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
