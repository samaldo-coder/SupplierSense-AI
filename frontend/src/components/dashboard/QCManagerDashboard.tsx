import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Eye,
  TrendingUp,
  Shield,
  Activity,
  BarChart3
} from 'lucide-react'
import {
  getEvents,
  getSuppliers,
  getPipelineRuns,
  getAuditTrail,
  getDashboardStats,
  type SupplierEvent,
  type Supplier,
  type PipelineRun,
  type AuditEntry,
  type DashboardStats,
} from '../../api'

export default function QCManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState('queue')
  const [events, setEvents] = useState<SupplierEvent[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [pipelineRuns, setPipelineRuns] = useState<PipelineRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)

  const agentSteps = [
    { name: 'intake_agent', label: 'Intake Agent', icon: '📥', description: 'Data validation' },
    { name: 'quality_agent', label: 'Quality Agent', icon: '🎯', description: 'Score calculation' },
    { name: 'supplier_history_agent', label: 'History Agent', icon: '📚', description: 'Supplier analysis' },
    { name: 'decision_agent', label: 'Decision Agent', icon: '⚖️', description: 'Recommendation' },
    { name: 'executor_agent', label: 'Executor Agent', icon: '🚀', description: 'PO execution' },
  ]

  const fetchData = useCallback(async () => {
    try {
      const [eventsData, suppliersData, runsData, statsData] = await Promise.all([
        getEvents().catch(() => []),
        getSuppliers().catch(() => []),
        getPipelineRuns().catch(() => []),
        getDashboardStats().catch(() => null),
      ])
      setEvents(eventsData)
      setSuppliers(suppliersData)
      setPipelineRuns(runsData)
      setStats(statsData)

      // Auto-select latest run
      if (runsData.length > 0 && !selectedRunId) {
        setSelectedRunId(runsData[0].run_id)
      }
    } catch {
      console.warn('Backend offline — using empty state')
    }
  }, [selectedRunId])

  // Poll for updates
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [fetchData])

  // Fetch audit trail when run is selected
  useEffect(() => {
    if (!selectedRunId) return
    const fetchTrail = async () => {
      try {
        const trail = await getAuditTrail(selectedRunId)
        setAuditTrail(trail)
      } catch {
        setAuditTrail([])
      }
    }
    fetchTrail()
    const interval = setInterval(fetchTrail, 3000)
    return () => clearInterval(interval)
  }, [selectedRunId])

  const getSupplierName = (supplierId: string) => {
    const s = suppliers.find(sup => sup.supplier_id === supplierId)
    return s?.supplier_name || supplierId
  }

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      CRITICAL: 'bg-red-500/20 text-red-300',
      HIGH: 'bg-orange-500/20 text-orange-300',
      MEDIUM: 'bg-amber-500/20 text-amber-300',
      LOW: 'bg-emerald-500/20 text-emerald-300',
    }
    return styles[severity] || 'bg-gray-500/20 text-gray-300'
  }

  const completedAgents = selectedRunId
    ? pipelineRuns.find(r => r.run_id === selectedRunId)?.agents_completed || []
    : []

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Quality Control Dashboard</h1>
          <p className="text-gray-400 font-mono text-sm">Monitor agent pipeline and review flagged events</p>
        </div>
        <div className="flex items-center space-x-4">
          {stats && (
          <div className="text-right">
              <div className="text-sm text-gray-400">Audit Entries</div>
              <div className="text-xl font-bold text-blue-400">{stats.total_audit_entries}</div>
          </div>
          )}
        </div>
      </motion.div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-white/5 p-1 rounded-lg">
        {[
          { id: 'queue', label: 'Event Queue', icon: AlertTriangle },
          { id: 'agents', label: 'Live Agents', icon: Activity },
          { id: 'metrics', label: 'Metrics', icon: BarChart3 }
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
            </motion.button>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {selectedTab === 'queue' && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                  <h2 className="text-lg font-semibold text-white">Supplier Events</h2>
                </div>
                <span className="px-3 py-1 bg-white/10 text-gray-300 rounded-full text-sm">
                  {events.length} Events
                </span>
              </div>

              <div className="space-y-4">
                {events.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">No events loaded. Start the backend to see real data.</div>
                ) : (
                  events.map((event, index) => (
                  <motion.div
                      key={event.event_id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all"
                    whileHover={{ scale: 1.01 }}
                  >
                      <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="flex items-center space-x-3">
                            <span className="font-medium text-white">{getSupplierName(event.supplier_id)}</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityBadge(event.severity)}`}>
                              {event.severity}
                            </span>
                          </div>
                          <div className="text-sm text-gray-400 mt-1">{event.event_type} · {event.delay_days} day delay</div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-white">{event.delay_days}d</div>
                          <div className="text-xs text-gray-400">delay</div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-300">{event.description}</p>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}

          {selectedTab === 'agents' && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
              <div className="flex items-center space-x-3 mb-6">
                <Activity className="w-6 h-6 text-blue-400" />
                <h2 className="text-lg font-semibold text-white">Live Agent Pipeline</h2>
                {pipelineRuns.length > 0 && (
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    completedAgents.length >= 5 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-blue-500/20 text-blue-300'
                  }`}>
                    {completedAgents.length >= 5 ? '✅ COMPLETED' : '🔄 PROCESSING'}
                  </span>
                )}
              </div>

              {/* Run Selector */}
              {pipelineRuns.length > 1 && (
                <div className="mb-4">
                  <select
                    value={selectedRunId || ''}
                    onChange={e => setSelectedRunId(e.target.value)}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm"
                  >
                    {pipelineRuns.map(r => (
                      <option key={r.run_id} value={r.run_id} className="bg-slate-800">
                        Run {r.run_id.slice(0, 12)}... ({r.agents_completed.length} agents)
                      </option>
                    ))}
                  </select>
                    </div>
              )}

              {pipelineRuns.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <Activity className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No pipeline runs detected yet.</p>
                  <p className="text-sm mt-2">Run: <code className="text-purple-400">python agents/run.py --fixture event_red</code></p>
                </div>
              ) : (
                <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <div className="space-y-4 mb-6">
                    {agentSteps.map((agent, index) => {
                      const isDone = completedAgents.includes(agent.name)
                      const isCurrent = !isDone && index === completedAgents.length
                      const auditEntry = auditTrail.find(a => a.agent_name === agent.name)

                      return (
                    <motion.div 
                          key={agent.name}
                      className="flex items-center space-x-4"
                      animate={{ 
                            opacity: isDone ? 1 : isCurrent ? 1 : 0.4,
                            scale: isCurrent ? 1.02 : 1
                      }}
                    >
                          <span className="text-2xl w-8 text-center">{agent.icon}</span>
                      <div className="flex-1">
                            <div className="text-sm text-gray-300">{agent.label}</div>
                        <div className="text-xs text-gray-500">{agent.description}</div>
                            {auditEntry && (
                              <div className="text-xs text-blue-400 mt-1">
                                Confidence: {(auditEntry.confidence * 100).toFixed(0)}% · {auditEntry.rationale.slice(0, 80)}...
                              </div>
                            )}
                      </div>
                          <span className={`text-xs px-3 py-1 rounded-full ${
                            isDone ? 'bg-emerald-500/20 text-emerald-300' :
                            isCurrent ? 'bg-blue-500/20 text-blue-300' :
                          'bg-gray-500/20 text-gray-400'
                          }`}>
                            {isDone ? '✅ Complete' : isCurrent ? '⏳ Processing' : '⬜ Waiting'}
                          </span>
                    </motion.div>
                      )
                    })}
                </div>

                  {/* Progress bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Overall Progress</span>
                      <span className="text-white">{Math.round((completedAgents.length / 5) * 100)}%</span>
                  </div>
                  <div className="bg-gray-700 rounded-full h-3 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                        animate={{ width: `${(completedAgents.length / 5) * 100}%` }}
                        transition={{ duration: 0.5 }}
                    />
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Today's Metrics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h3 className="text-lg font-semibold text-white">System Stats</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Total Events</span>
                <span className="text-white font-bold text-lg">{events.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Critical</span>
                <span className="text-red-400 font-bold text-lg">
                  {events.filter(e => e.severity === 'CRITICAL').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Pipeline Runs</span>
                <span className="text-blue-400 font-bold text-lg">{pipelineRuns.length}</span>
              </div>
              {stats && (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Pending Approvals</span>
                    <span className="text-amber-400 font-bold text-lg">{stats.pending_approvals}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Audit Entries</span>
                    <span className="text-purple-400 font-bold text-lg">{stats.total_audit_entries}</span>
                  </div>
                </>
              )}
            </div>
          </motion.div>

          {/* At-Risk Suppliers */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <Shield className="w-5 h-5 text-red-400" />
              <h3 className="text-lg font-semibold text-white">At-Risk Suppliers</h3>
            </div>
            
            <div className="space-y-3">
              {suppliers.filter(s => s.financial_health !== 'GREEN').map(s => (
                <div key={s.supplier_id} className="flex items-center justify-between p-2 bg-white/5 rounded-lg">
                  <div>
                    <div className="text-sm text-white">{s.supplier_name}</div>
                    <div className="text-xs text-gray-400">{s.country}</div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    s.financial_health === 'RED' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    {s.financial_health}
                  </span>
                </div>
              ))}
              {suppliers.filter(s => s.financial_health !== 'GREEN').length === 0 && (
                <div className="text-sm text-gray-400 text-center py-4">All suppliers healthy</div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
