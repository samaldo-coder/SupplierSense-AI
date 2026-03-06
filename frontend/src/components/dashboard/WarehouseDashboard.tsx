import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Package, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  Save,
  Zap,
  ArrowRight
} from 'lucide-react'
import { getSuppliers, getEvents, getDashboardStats, createEvent, triggerPipeline, type Supplier, type SupplierEvent, type DashboardStats, type PipelineResult } from '../../api'
import { useGlobalToast } from '../ui/Toast'

export default function WarehouseDashboard() {
  const toast = useGlobalToast()
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [events, setEvents] = useState<SupplierEvent[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [formData, setFormData] = useState({
    supplier: '',
    poNumber: '',
    partNumber: '',
    quantity: '',
    visualInspection: false,
    dimensionalCheck: false,
    weightVerified: false,
    defectsFound: '',
    totalUnits: '',
    notes: ''
  })
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formProgress, setFormProgress] = useState(0)

  // Disruption report state
  const [disruptionForm, setDisruptionForm] = useState({
    supplier_id: '',
    event_type: 'DELIVERY_MISS' as 'DELIVERY_MISS' | 'FINANCIAL_FLAG' | 'QUALITY_HOLD',
    delay_days: 3,
    severity: 'MEDIUM' as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
    description: '',
  })
  const [isRunningPipeline, setIsRunningPipeline] = useState(false)
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null)
  const [selectedTab, setSelectedTab] = useState<'shipment' | 'disruption'>('disruption')

  const fetchData = useCallback(async () => {
    try {
      const [s, e, st] = await Promise.all([
        getSuppliers().catch(() => []),
        getEvents().catch(() => []),
        getDashboardStats().catch(() => null),
      ])
      setSuppliers(s)
      setEvents(e)
      setStats(st)
    } catch {
      console.warn('Backend offline')
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [fetchData])

  useEffect(() => {
    const requiredFields = ['supplier', 'poNumber', 'partNumber', 'quantity']
    const completed = requiredFields.filter(field => formData[field as keyof typeof formData]).length
    setFormProgress((completed / requiredFields.length) * 100)
  }, [formData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    console.log('Shipment submitted:', formData)
    setFormData({
      supplier: '', poNumber: '', partNumber: '', quantity: '',
      visualInspection: false, dimensionalCheck: false, weightVerified: false,
      defectsFound: '', totalUnits: '', notes: ''
    })
    setIsSubmitting(false)
    toast.success('Shipment data logged successfully.')
  }

  const handleReportDisruption = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!disruptionForm.supplier_id) return

    setIsRunningPipeline(true)
    setPipelineResult(null)

    try {
      // 1. Create the event in the backend
      const event = await createEvent({
        supplier_id: disruptionForm.supplier_id,
        event_type: disruptionForm.event_type,
        delay_days: disruptionForm.delay_days,
        severity: disruptionForm.severity,
        description: disruptionForm.description || `${disruptionForm.event_type} reported for supplier`,
      })

      // 2. Trigger the AI pipeline
      const result = await triggerPipeline(event.event_id)
      setPipelineResult(result)

      // 3. Show toast based on result
      if (result.status === 'completed') {
        toast.success('Pipeline completed — auto-approved, PO created.')
      } else if (result.status === 'paused_for_hitl') {
        toast.warning('Pipeline paused — awaiting Director approval.')
      } else if (result.status === 'error') {
        toast.error(`Pipeline error: ${result.error ?? 'unknown'}`)
      }

      // 4. Refresh data
      await fetchData()
    } catch (err) {
      console.error('Pipeline trigger failed:', err)
      setPipelineResult({ status: 'error', error: 'Failed to reach backend. Is it running?' })
      toast.error('Pipeline trigger failed — is the backend running?')
    } finally {
      setIsRunningPipeline(false)
    }
  }

  const recentEvents = events.slice(0, 5)

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Shipment Intake Dashboard</h1>
          <p className="text-gray-400 font-mono text-sm">Log new shipments and track system status</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-400">Today</div>
          <div className="text-xl font-bold text-white">{new Date().toLocaleDateString()}</div>
        </div>
      </motion.div>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Active Suppliers', value: stats.active_suppliers, color: 'text-blue-400' },
            { label: 'Total Events', value: stats.total_events, color: 'text-amber-400' },
            { label: 'Pending Approvals', value: stats.pending_approvals, color: 'text-purple-400' },
            { label: 'Purchase Orders', value: stats.total_purchase_orders, color: 'text-emerald-400' },
          ].map((card, i) => (
            <motion.div key={card.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }} className="glass-card p-4 text-center">
              <div className="text-sm text-gray-400">{card.label}</div>
              <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Tab Switcher */}
      <div className="flex space-x-1 bg-white/5 p-1 rounded-lg">
        {[
          { id: 'disruption' as const, label: 'Report Disruption', icon: Zap },
          { id: 'shipment' as const, label: 'Log Shipment', icon: Package },
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
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="lg:col-span-2">

          {/* ═══ REPORT DISRUPTION TAB ═══ */}
          {selectedTab === 'disruption' && (
          <div className="glass-card p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-linear-to-r from-red-500 to-orange-500 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Report Supplier Disruption</h2>
                <p className="text-sm text-gray-400">Submit a disruption event — the AI pipeline processes it automatically</p>
              </div>
            </div>

            <form onSubmit={handleReportDisruption} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Supplier *</label>
                  <select
                    value={disruptionForm.supplier_id}
                    onChange={e => setDisruptionForm({...disruptionForm, supplier_id: e.target.value})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-red-400 focus:ring-1 focus:ring-red-400"
                    required
                  >
                    <option value="">Select Supplier</option>
                    {suppliers.map(s => (
                      <option key={s.supplier_id} value={s.supplier_id} className="bg-slate-800">
                        {s.supplier_name} ({s.financial_health})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Event Type *</label>
                  <select
                    value={disruptionForm.event_type}
                    onChange={e => setDisruptionForm({...disruptionForm, event_type: e.target.value as any})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-red-400"
                  >
                    <option value="DELIVERY_MISS" className="bg-slate-800">Delivery Miss</option>
                    <option value="FINANCIAL_FLAG" className="bg-slate-800">Financial Flag</option>
                    <option value="QUALITY_HOLD" className="bg-slate-800">Quality Hold</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Delay (days) *</label>
                  <input
                    type="number"
                    value={disruptionForm.delay_days}
                    onChange={e => setDisruptionForm({...disruptionForm, delay_days: parseInt(e.target.value) || 0})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-red-400"
                    min={0} max={30}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Severity *</label>
                  <select
                    value={disruptionForm.severity}
                    onChange={e => setDisruptionForm({...disruptionForm, severity: e.target.value as any})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-red-400"
                  >
                    <option value="LOW" className="bg-slate-800">LOW</option>
                    <option value="MEDIUM" className="bg-slate-800">MEDIUM</option>
                    <option value="HIGH" className="bg-slate-800">HIGH</option>
                    <option value="CRITICAL" className="bg-slate-800">CRITICAL</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
                <textarea
                  value={disruptionForm.description}
                  onChange={e => setDisruptionForm({...disruptionForm, description: e.target.value})}
                  placeholder="Describe the disruption (e.g. facility fire, port congestion, quality defect)..."
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-red-400"
                  rows={2}
                />
              </div>

              <motion.button
                type="submit"
                disabled={isRunningPipeline || !disruptionForm.supplier_id}
                className="w-full py-4 bg-linear-to-r from-red-600 to-orange-600 text-white rounded-lg font-bold text-lg hover:from-red-700 hover:to-orange-700 disabled:opacity-50 shadow-lg shadow-red-500/25"
                whileHover={{ scale: isRunningPipeline ? 1 : 1.02 }}
                whileTap={{ scale: isRunningPipeline ? 1 : 0.98 }}
              >
                {isRunningPipeline ? (
                  <div className="flex items-center justify-center space-x-3">
                    <motion.div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} />
                    <span>AI Pipeline Processing...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-3">
                    <Zap className="w-5 h-5" />
                    <span>Report Disruption & Run AI Pipeline</span>
                    <ArrowRight className="w-5 h-5" />
                  </div>
                )}
              </motion.button>
            </form>

            {/* Pipeline Result */}
            <AnimatePresence>
              {pipelineResult && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className={`mt-6 p-4 rounded-lg border ${
                    pipelineResult.error
                      ? 'bg-red-500/10 border-red-500/30'
                      : pipelineResult.paused_for_hitl
                      ? 'bg-amber-500/10 border-amber-500/30'
                      : 'bg-emerald-500/10 border-emerald-500/30'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    {pipelineResult.error ? (
                      <AlertTriangle className="w-6 h-6 text-red-400 shrink-0 mt-0.5" />
                    ) : pipelineResult.paused_for_hitl ? (
                      <Clock className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <h4 className={`font-semibold ${
                        pipelineResult.error ? 'text-red-300' :
                        pipelineResult.paused_for_hitl ? 'text-amber-300' : 'text-emerald-300'
                      }`}>
                        {pipelineResult.error ? 'Pipeline Error' :
                         pipelineResult.paused_for_hitl ? 'Escalated — Awaiting Director Approval' :
                         'Auto-Approved & Executed'}
                      </h4>
                      <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                        {pipelineResult.composite_score != null && (
                          <div><span className="text-gray-400">Risk Score:</span> <span className={`font-bold ${
                            pipelineResult.composite_score >= 70 ? 'text-red-400' :
                            pipelineResult.composite_score >= 40 ? 'text-amber-400' : 'text-emerald-400'
                          }`}>{pipelineResult.composite_score.toFixed(1)}/100</span></div>
                        )}
                        {pipelineResult.action && (
                          <div><span className="text-gray-400">Action:</span> <span className="text-white">{pipelineResult.action}</span></div>
                        )}
                        {pipelineResult.po_id && (
                          <div><span className="text-gray-400">PO:</span> <span className="text-emerald-400 font-mono">{pipelineResult.po_id}</span></div>
                        )}
                        {pipelineResult.audit_entries != null && (
                          <div><span className="text-gray-400">Agents Run:</span> <span className="text-white">{pipelineResult.audit_entries}/5</span></div>
                        )}
                        {pipelineResult.error && (
                          <div className="col-span-2"><span className="text-gray-400">Error:</span> <span className="text-red-300">{pipelineResult.error}</span></div>
                        )}
                      </div>
                      {pipelineResult.paused_for_hitl && (
                        <p className="text-amber-300/70 text-xs mt-2">
                          Switch to Director role to approve or reject this decision.
                        </p>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          )}

          {/* ═══ SHIPMENT ENTRY TAB ═══ */}
          {selectedTab === 'shipment' && (
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-linear-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <Package className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Quick Shipment Entry</h2>
                <p className="text-sm text-gray-400">Enter shipment details for AI processing</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-400 mb-1">Form Progress</div>
                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div className="h-full bg-linear-to-r from-blue-500 to-purple-500" animate={{ width: `${formProgress}%` }} transition={{ duration: 0.3 }} />
                </div>
                <div className="text-xs text-gray-400 mt-1">{Math.round(formProgress)}%</div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Supplier *</label>
                  <select
                    value={formData.supplier}
                    onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-purple-400 focus:ring-1 focus:ring-purple-400"
                    required
                  >
                    <option value="">Select Supplier</option>
                    {suppliers.map(s => (
                      <option key={s.supplier_id} value={s.supplier_id} className="bg-slate-800">
                        {s.supplier_name} ({s.financial_health})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">PO Number *</label>
                  <input type="text" value={formData.poNumber} onChange={(e) => setFormData({...formData, poNumber: e.target.value})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400" placeholder="PO-2026-001" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Part Number *</label>
                  <input type="text" value={formData.partNumber} onChange={(e) => setFormData({...formData, partNumber: e.target.value})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400" placeholder="PT-ENG-001" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Quantity *</label>
                  <input type="number" value={formData.quantity} onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400" placeholder="150" required />
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                <h3 className="text-sm font-medium text-white mb-3">Quality Inspection</h3>
                <div className="space-y-3">
                  {[
                    { key: 'visualInspection', label: 'Visual inspection completed' },
                    { key: 'dimensionalCheck', label: 'Dimensional measurements taken' },
                    { key: 'weightVerified', label: 'Weight verified' }
                  ].map(item => (
                    <label key={item.key} className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" checked={formData[item.key as keyof typeof formData] as boolean}
                        onChange={(e) => setFormData({...formData, [item.key]: e.target.checked})}
                        className="w-4 h-4 bg-white/5 border border-white/20 rounded text-purple-600" />
                      <span className="text-sm text-gray-300">{item.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex space-x-4">
                <motion.button type="button" onClick={() => setFormData({
                    supplier: '', poNumber: '', partNumber: '', quantity: '',
                    visualInspection: false, dimensionalCheck: false, weightVerified: false,
                    defectsFound: '', totalUnits: '', notes: ''
                  })}
                  className="flex-1 py-3 bg-white/10 border border-white/20 text-gray-300 rounded-lg font-medium hover:bg-white/15"
                  whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                >
                  Clear Form
                </motion.button>
                <motion.button type="submit" disabled={isSubmitting || formProgress < 100}
                  className="flex-1 py-3 bg-linear-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 shadow-lg shadow-purple-500/25"
                  whileHover={{ scale: formProgress >= 100 ? 1.02 : 1 }} whileTap={{ scale: formProgress >= 100 ? 0.98 : 1 }}
                >
                  {isSubmitting ? (
                    <div className="flex items-center justify-center space-x-2">
                      <motion.div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} />
                      <span>Processing...</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center space-x-2">
                      <Save className="w-4 h-4" />
                      <span>Submit Shipment</span>
                    </div>
                  )}
                </motion.button>
              </div>
            </form>
          </div>
          )}
        </motion.div>

        <div className="space-y-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
            <div className="flex items-center space-x-3 mb-4">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h3 className="text-lg font-semibold text-white">System Overview</h3>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Active Suppliers</span>
                <span className="text-white font-bold text-lg">{suppliers.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">At-Risk</span>
                <span className="text-red-400 font-bold text-lg">{suppliers.filter(s => s.financial_health === 'RED').length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Events Tracked</span>
                <span className="text-amber-400 font-bold text-lg">{events.length}</span>
              </div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Clock className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-semibold text-white">Recent Events</h3>
            </div>
            <div className="space-y-3">
              {recentEvents.map((event, index) => {
                const supplier = suppliers.find(s => s.supplier_id === event.supplier_id)
                return (
                  <motion.div key={event.event_id}
                    initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + index * 0.1 }}
                  className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10"
                >
                  <div>
                      <div className="text-sm font-medium text-white">{supplier?.supplier_name || 'Unknown'}</div>
                      <div className="text-xs text-gray-400">{event.event_type}</div>
                  </div>
                  <div className="text-right">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        event.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-300' :
                        event.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-300' :
                        event.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-emerald-500/20 text-emerald-300'
                      }`}>{event.severity}</span>
                  </div>
                </motion.div>
                )
              })}
              {recentEvents.length === 0 && (
                <div className="text-sm text-gray-400 text-center py-4">Start the backend to see events</div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
