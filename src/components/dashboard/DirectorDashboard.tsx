import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Package, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  Camera,
  Upload,
  Save
} from 'lucide-react'

export default function WarehouseDashboard() {
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
  const [focusedField, setFocusedField] = useState('')

  // Calculate form completion percentage
  useEffect(() => {
    const requiredFields = ['supplier', 'poNumber', 'partNumber', 'quantity']
    const completed = requiredFields.filter(field => formData[field as keyof typeof formData]).length
    setFormProgress((completed / requiredFields.length) * 100)
  }, [formData])

  const performanceData = {
    shipmentsLogged: 12,
    autoApproved: 10,
    pendingReview: 2,
    avgProcessTime: '1.8m'
  }

  const recentActivity = [
    { id: 'SH-4470', supplier: 'BetaSteel', status: 'approved', time: '2 min ago' },
    { id: 'SH-4469', supplier: 'AlphaCorp', status: 'pending', time: '5 min ago' },
    { id: 'SH-4468', supplier: 'GammaCast', status: 'approved', time: '15 min ago' },
  ]

  const suppliers = [
    'BetaSteel Corporation',
    'AlphaCorp Industries', 
    'GammaCast Manufacturing',
    'DeltaForge LLC',
    'EpsilonCast Systems'
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    // Simulate API call with realistic timing
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Show success message (you'll add toast later)
    console.log('Shipment submitted successfully!')
    
    setFormData({
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
    
    setIsSubmitting(false)
  }

  const getStatusBadge = (status: string) => {
    const badges = {
      approved: 'status-badge status-approved',
      pending: 'status-badge status-pending',
      rejected: 'status-badge status-rejected'
    }
    
    const icons = {
      approved: CheckCircle,
      pending: Clock,
      rejected: AlertTriangle
    }
    
    const Icon = icons[status as keyof typeof icons]
    
    return (
      <span className={badges[status as keyof typeof badges]}>
        <Icon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Shipment Intake Dashboard</h1>
          <p className="text-gray-400 font-mono text-sm">Log new shipments and track your performance</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-400">Today</div>
          <div className="text-xl font-bold text-white">{new Date().toLocaleDateString()}</div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2"
        >
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                  <Package className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">Quick Shipment Entry</h2>
                  <p className="text-sm text-gray-400">Enter shipment details for AI processing</p>
                </div>
              </div>
              
              {/* Progress Indicator */}
              <div className="text-right">
                <div className="text-xs text-gray-400 mb-1">Form Progress</div>
                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${formProgress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <div className="text-xs text-gray-400 mt-1">{Math.round(formProgress)}%</div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <motion.div
                  animate={{ 
                    scale: focusedField === 'supplier' ? 1.02 : 1,
                    borderColor: focusedField === 'supplier' ? '#a78bfa' : 'rgba(255, 255, 255, 0.1)'
                  }}
                  transition={{ duration: 0.2 }}
                >
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Supplier *
                  </label>
                  <select
                    value={formData.supplier}
                    onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                    onFocus={() => setFocusedField('supplier')}
                    onBlur={() => setFocusedField('')}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:border-purple-400 focus:ring-1 focus:ring-purple-400 transition-all"
                    required
                  >
                    <option value="">Select Supplier</option>
                    {suppliers.map(supplier => (
                      <option key={supplier} value={supplier} className="bg-slate-800">
                        {supplier}
                      </option>
                    ))}
                  </select>
                </motion.div>

                <motion.div
                  animate={{ 
                    scale: focusedField === 'poNumber' ? 1.02 : 1,
                  }}
                  transition={{ duration: 0.2 }}
                >
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    PO Number *
                  </label>
                  <input
                    type="text"
                    value={formData.poNumber}
                    onChange={(e) => setFormData({...formData, poNumber: e.target.value})}
                    onFocus={() => setFocusedField('poNumber')}
                    onBlur={() => setFocusedField('')}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 transition-all"
                    placeholder="PO-2024-4471"
                    required
                  />
                </motion.div>

                <motion.div
                  animate={{ 
                    scale: focusedField === 'partNumber' ? 1.02 : 1,
                  }}
                  transition={{ duration: 0.2 }}
                >
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Part Number *
                  </label>
                  <input
                    type="text"
                    value={formData.partNumber}
                    onChange={(e) => setFormData({...formData, partNumber: e.target.value})}
                    onFocus={() => setFocusedField('partNumber')}
                    onBlur={() => setFocusedField('')}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 transition-all"
                    placeholder="PT-ENGINE-4471-X"
                    required
                  />
                </motion.div>

                <motion.div
                  animate={{ 
                    scale: focusedField === 'quantity' ? 1.02 : 1,
                  }}
                  transition={{ duration: 0.2 }}
                >
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Quantity *
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      value={formData.quantity}
                      onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                      onFocus={() => setFocusedField('quantity')}
                      onBlur={() => setFocusedField('')}
                      className="w-full px-4 py-3 pr-16 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 transition-all"
                      placeholder="150"
                      required
                    />
                    <span className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm">
                      units
                    </span>
                  </div>
                </motion.div>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white/5 border border-white/10 rounded-lg p-4"
              >
                <h3 className="text-sm font-medium text-white mb-3">Quality Inspection</h3>
                <div className="space-y-3">
                  {[
                    { key: 'visualInspection', label: 'Visual inspection completed' },
                    { key: 'dimensionalCheck', label: 'Dimensional measurements taken' },
                    { key: 'weightVerified', label: 'Weight verified' }
                  ].map((item, index) => (
                    <motion.label 
                      key={item.key} 
                      className="flex items-center space-x-3 cursor-pointer"
                      whileHover={{ scale: 1.02 }}
                      transition={{ duration: 0.1 }}
                    >
                      <input
                        type="checkbox"
                        checked={formData[item.key as keyof typeof formData] as boolean}
                        onChange={(e) => setFormData({...formData, [item.key]: e.target.checked})}
                        className="w-4 h-4 bg-white/5 border border-white/20 rounded text-purple-600 focus:ring-purple-500 focus:ring-offset-slate-900"
                      />
                      <span className="text-sm text-gray-300">{item.label}</span>
                      {formData[item.key as keyof typeof formData] && (
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="text-emerald-400"
                        >
                          ✓
                        </motion.span>
                      )}
                    </motion.label>
                  ))}
                </div>
              </motion.div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Defects Found
                  </label>
                  <input
                    type="number"
                    value={formData.defectsFound}
                    onChange={(e) => setFormData({...formData, defectsFound: e.target.value})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 transition-all"
                    placeholder="3"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Total Units Inspected
                  </label>
                  <input
                    type="number"
                    value={formData.totalUnits}
                    onChange={(e) => setFormData({...formData, totalUnits: e.target.value})}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 transition-all"
                    placeholder="100"
                    min="1"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Notes (Optional)
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-purple-400 focus:ring-1 focus:ring-purple-400 transition-all"
                  rows={3}
                  placeholder="Any additional observations or concerns..."
                />
              </div>

              <motion.div 
                className="bg-white/5 border border-white/10 rounded-lg p-4 border-dashed"
                whileHover={{ borderColor: 'rgba(255, 255, 255, 0.2)' }}
                transition={{ duration: 0.2 }}
              >
                <div className="text-center">
                  <Camera className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-400 mb-2">Add inspection photos</p>
                  <button
                    type="button"
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-sm text-gray-300 hover:bg-white/15 transition-colors"
                  >
                    <Upload className="w-4 h-4" />
                    <span>Choose Files</span>
                  </button>
                </div>
              </motion.div>

              <div className="flex space-x-4">
                <motion.button
                  type="button"
                  onClick={() => setFormData({
                    supplier: '', poNumber: '', partNumber: '', quantity: '',
                    visualInspection: false, dimensionalCheck: false, weightVerified: false,
                    defectsFound: '', totalUnits: '', notes: ''
                  })}
                  className="flex-1 py-3 bg-white/10 border border-white/20 text-gray-300 rounded-lg font-medium hover:bg-white/15 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Clear Form
                </motion.button>
                <motion.button
                  type="submit"
                  disabled={isSubmitting || formProgress < 100}
                  className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/25"
                  whileHover={{ scale: formProgress >= 100 ? 1.02 : 1 }}
                  whileTap={{ scale: formProgress >= 100 ? 0.98 : 1 }}
                >
                  {isSubmitting ? (
                    <div className="flex items-center justify-center space-x-2">
                      <motion.div
                        className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      />
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
        </motion.div>

        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h3 className="text-lg font-semibold text-white">My Performance Today</h3>
            </div>
            
            <div className="space-y-4">
              <motion.div 
                className="flex justify-between items-center"
                whileHover={{ scale: 1.02 }}
              >
                <span className="text-gray-400">Shipments Logged</span>
                <motion.span 
                  className="text-white font-bold text-lg"
                  key={performanceData.shipmentsLogged}
                  initial={{ scale: 1.2, color: '#10b981' }}
                  animate={{ scale: 1, color: '#ffffff' }}
                  transition={{ duration: 0.3 }}
                >
                  {performanceData.shipmentsLogged}
                </motion.span>
              </motion.div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Auto-Approved</span>
                <span className="text-emerald-400 font-bold text-lg">{performanceData.autoApproved}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Pending Review</span>
                <span className="text-amber-400 font-bold text-lg">{performanceData.pendingReview}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Avg Process Time</span>
                <span className="text-blue-400 font-bold text-lg font-mono">{performanceData.avgProcessTime}</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <Clock className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
            </div>
            
            <div className="space-y-3">
              {recentActivity.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all cursor-pointer"
                  whileHover={{ scale: 1.02 }}
                >
                  <div>
                    <div className="text-sm font-medium text-white font-mono">{item.id}</div>
                    <div className="text-xs text-gray-400">{item.supplier}</div>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(item.status)}
                    <div className="text-xs text-gray-500 mt-1">{item.time}</div>
                  </div>
                </motion.div>
              ))}
            </div>

            <motion.button 
              className="w-full mt-4 py-2 text-sm text-purple-400 hover:text-purple-300 transition-colors"
              whileHover={{ scale: 1.02 }}
            >
              View All My Shipments →
            </motion.button>
          </motion.div>
        </div>
      </div>
    </div>
  )
}