import { useState, useEffect } from 'react'
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

export default function QCManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState('queue')
  const [currentAgentStep, setCurrentAgentStep] = useState(0)
  const [agentProgress, setAgentProgress] = useState(0)
  const [isAgentProcessing, setIsAgentProcessing] = useState(true)

  // Real-time agent pipeline simulation
  useEffect(() => {
    if (!isAgentProcessing) return

    const interval = setInterval(() => {
      setAgentProgress(prev => {
        if (prev >= 100) {
          setCurrentAgentStep(curr => {
            const nextStep = curr + 1
            if (nextStep >= 4) {
              setIsAgentProcessing(false)
              return 0
            }
            return nextStep
          })
          return 0
        }
        return prev + 2
      })
    }, 100)
    
    return () => clearInterval(interval)
  }, [currentAgentStep, isAgentProcessing])

  const agentSteps = [
    { name: 'Intake Agent', icon: '📥', description: 'Data validation' },
    { name: 'Quality Agent', icon: '🎯', description: 'Score calculation' },
    { name: 'History Agent', icon: '📚', description: 'Supplier analysis' },
    { name: 'Decision Agent', icon: '⚖️', description: 'Recommendation' }
  ]

  const priorityReviews = [
    {
      id: 'SH-4475',
      supplier: 'ZetaCorp',
      part: 'PT-9901-X',
      score: 23,
      defectRate: 12,
      risk: 'high',
      aiRecommendation: 'REJECT',
      confidence: 94,
      timeAgo: '5 min ago'
    },
    {
      id: 'SH-4474', 
      supplier: 'AlphaCorp',
      part: 'PT-4471-K',
      score: 34,
      defectRate: 8,
      risk: 'high',
      aiRecommendation: 'ESCALATE',
      confidence: 87,
      timeAgo: '12 min ago'
    },
    {
      id: 'SH-4476',
      supplier: 'BetaSteel',
      part: 'PT-8832-Z',
      score: 67,
      defectRate: 4,
      risk: 'medium',
      aiRecommendation: 'REVIEW',
      confidence: 78,
      timeAgo: '18 min ago'
    }
  ]

  const todaysMetrics = {
    totalProcessed: 89,
    autoApproved: 67,
    manualReviews: 15,
    rejected: 7,
    avgReviewTime: '4.2min'
  }

  const handleReviewAction = (shipmentId: string, action: 'approve' | 'reject' | 'escalate') => {
    console.log(`${action.toUpperCase()} action for ${shipmentId}`)
    // Start new agent processing simulation
    setIsAgentProcessing(true)
    setCurrentAgentStep(0)
    setAgentProgress(0)
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Quality Control Dashboard</h1>
          <p className="text-gray-400 font-mono text-sm">Review flagged shipments and AI recommendations</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Queue Status</div>
            <div className="text-xl font-bold text-amber-400">{priorityReviews.length} Pending</div>
          </div>
        </div>
      </motion.div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-white/5 p-1 rounded-lg">
        {[
          { id: 'queue', label: 'Review Queue', icon: AlertTriangle },
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
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                  <h2 className="text-lg font-semibold text-white">Priority Review Queue</h2>
                </div>
                <motion.span 
                  className="px-3 py-1 bg-red-500/20 text-red-300 rounded-full text-sm font-medium"
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {priorityReviews.length} High Priority
                </motion.span>
              </div>

              <div className="space-y-4">
                {priorityReviews.map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all"
                    whileHover={{ scale: 1.01 }}
                  >
                    {/* Header */}
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <div className="flex items-center space-x-3">
                          <span className="font-mono text-white font-medium text-lg">{item.id}</span>
                          <motion.span 
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              item.risk === 'high' ? 'bg-red-500/20 text-red-300' :
                              item.risk === 'medium' ? 'bg-amber-500/20 text-amber-300' :
                              'bg-emerald-500/20 text-emerald-300'
                            }`}
                            animate={{ scale: [1, 1.05, 1] }}
                            transition={{ duration: 3, repeat: Infinity }}
                          >
                            🔴 {item.risk.toUpperCase()} RISK
                          </motion.span>
                        </div>
                        <div className="text-sm text-gray-400 mt-1">
                          {item.supplier} | {item.part} | {item.timeAgo}
                        </div>
                      </div>
                      <div className="text-right">
                        <motion.div 
                          className="text-3xl font-bold text-red-400"
                          key={item.score}
                          initial={{ scale: 1.2 }}
                          animate={{ scale: 1 }}
                          transition={{ duration: 0.3 }}
                        >
                          {item.score}
                        </motion.div>
                        <div className="text-xs text-gray-400">AI Score</div>
                      </div>
                    </div>
                    
                    {/* Metrics */}
                    <div className="grid grid-cols-4 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-xs text-gray-400">Defect Rate</div>
                        <div className="text-red-400 font-bold">{item.defectRate}%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-400">AI Confidence</div>
                        <div className="text-blue-400 font-bold">{item.confidence}%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-400">Recommendation</div>
                        <div className="text-red-400 font-bold text-xs">{item.aiRecommendation}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-gray-400">Supplier Risk</div>
                        <div className="text-red-400 font-bold text-xs">VERY HIGH</div>
                      </div>
                    </div>

                    {/* AI Reasoning */}
                    <motion.div 
                      className="bg-white/5 border border-white/10 rounded-lg p-3 mb-4"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 + index * 0.1 }}
                    >
                      <div className="text-xs text-gray-400 mb-1">🤖 AI Analysis</div>
                      <div className="text-sm text-gray-300">
                        "{item.supplier} has failed quality inspections on 3 of their last 5 shipments. 
                        Current defect rate of {item.defectRate}% exceeds acceptable threshold of 3%. 
                        Recommend {item.aiRecommendation.toLowerCase()} and supplier performance review."
                      </div>
                    </motion.div>

                    {/* Action Buttons */}
                    <div className="grid grid-cols-3 gap-3">
                      <motion.button
                        onClick={() => handleReviewAction(item.id, 'approve')}
                        className="flex items-center justify-center space-x-2 py-2 bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 rounded-lg text-sm hover:bg-emerald-500/30 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <CheckCircle className="w-4 h-4" />
                        <span>Approve</span>
                      </motion.button>
                      <motion.button
                        onClick={() => handleReviewAction(item.id, 'reject')}
                        className="flex items-center justify-center space-x-2 py-2 bg-red-500/20 border border-red-500/30 text-red-300 rounded-lg text-sm hover:bg-red-500/30 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <AlertTriangle className="w-4 h-4" />
                        <span>Reject</span>
                      </motion.button>
                      <motion.button
                        onClick={() => handleReviewAction(item.id, 'escalate')}
                        className="flex items-center justify-center space-x-2 py-2 bg-white/10 border border-white/20 text-gray-300 rounded-lg text-sm hover:bg-white/15 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <Eye className="w-4 h-4" />
                        <span>Details</span>
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {selectedTab === 'agents' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6"
            >
              <div className="flex items-center space-x-3 mb-6">
                <Activity className="w-6 h-6 text-blue-400" />
                <h2 className="text-lg font-semibold text-white">Live Agent Pipeline</h2>
                <motion.span
                  className={`px-2 py-1 rounded-full text-xs ${
                    isAgentProcessing ? 'bg-blue-500/20 text-blue-300' : 'bg-emerald-500/20 text-emerald-300'
                  }`}
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  {isAgentProcessing ? '🔄 PROCESSING' : '✅ COMPLETED'}
                </motion.span>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-6">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <div className="font-mono text-white font-medium text-lg">Processing SH-4477</div>
                    <div className="text-sm text-gray-400">
                      {isAgentProcessing ? 
                        `Step ${currentAgentStep + 1} of ${agentSteps.length}: ${agentSteps[currentAgentStep]?.description}` :
                        'Processing Complete'
                      }
                    </div>
                  </div>
                  <div className="text-right">
                    <motion.div 
                      className="text-blue-400 font-medium text-lg"
                      key={`${currentAgentStep}-${agentProgress}`}
                      initial={{ scale: 1.1 }}
                      animate={{ scale: 1 }}
                      transition={{ duration: 0.2 }}
                    >
                      {isAgentProcessing ? Math.round(agentProgress) : 100}%
                    </motion.div>
                    <div className="text-xs text-gray-400">
                      {isAgentProcessing ? 
                        `ETA: ${Math.round((100 - agentProgress) / 10)} seconds` :
                        'Completed'
                      }
                    </div>
                  </div>
                </div>

                <div className="space-y-4 mb-6">
                  {agentSteps.map((agent, index) => (
                    <motion.div 
                      key={index} 
                      className="flex items-center space-x-4"
                      initial={{ opacity: 0.5 }}
                      animate={{ 
                        opacity: index < currentAgentStep ? 1 : 
                                index === currentAgentStep && isAgentProcessing ? 1 : 0.5,
                        scale: index === currentAgentStep && isAgentProcessing ? 1.02 : 1
                      }}
                      transition={{ duration: 0.3 }}
                    >
                      <span className="text-2xl">{agent.icon}</span>
                      <div className="flex-1">
                        <span className="text-sm text-gray-300">{agent.name}</span>
                        <div className="text-xs text-gray-500">{agent.description}</div>
                      </div>
                      <motion.span 
                        className={`text-xs px-3 py-1 rounded-full ${
                          index < currentAgentStep ? 'bg-emerald-500/20 text-emerald-300' :
                          index === currentAgentStep && isAgentProcessing ? 'bg-blue-500/20 text-blue-300' :
                          'bg-gray-500/20 text-gray-400'
                        }`}
                        animate={{
                          scale: index === currentAgentStep && isAgentProcessing ? [1, 1.05, 1] : 1
                        }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        {index < currentAgentStep ? '✅ Complete' :
                         index === currentAgentStep && isAgentProcessing ? '⏳ Processing' : '⬜ Waiting'}
                      </motion.span>
                    </motion.div>
                  ))}
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Overall Progress</span>
                    <span className="text-white">
                      {isAgentProcessing ? 
                        `${Math.round((currentAgentStep * 25) + (agentProgress * 0.25))}%` : 
                        '100%'
                      }
                    </span>
                  </div>
                  <div className="bg-gray-700 rounded-full h-3 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                      animate={{ 
                        width: isAgentProcessing ? 
                          `${(currentAgentStep * 25) + (agentProgress * 0.25)}%` : 
                          '100%'
                      }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>
              </div>
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
              <h3 className="text-lg font-semibold text-white">Today's Metrics</h3>
            </div>
            
            <div className="space-y-4">
              <motion.div 
                className="flex justify-between items-center"
                whileHover={{ scale: 1.02 }}
              >
                <span className="text-gray-400">Total Processed</span>
                <span className="text-white font-bold text-lg">{todaysMetrics.totalProcessed}</span>
              </motion.div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Auto-Approved</span>
                <span className="text-emerald-400 font-bold text-lg">
                  {todaysMetrics.autoApproved} ({Math.round((todaysMetrics.autoApproved / todaysMetrics.totalProcessed) * 100)}%)
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Manual Reviews</span>
                <span className="text-amber-400 font-bold text-lg">
                  {todaysMetrics.manualReviews} ({Math.round((todaysMetrics.manualReviews / todaysMetrics.totalProcessed) * 100)}%)
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Rejected</span>
                <span className="text-red-400 font-bold text-lg">
                  {todaysMetrics.rejected} ({Math.round((todaysMetrics.rejected / todaysMetrics.totalProcessed) * 100)}%)
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Avg Review Time</span>
                <span className="text-blue-400 font-bold text-lg font-mono">{todaysMetrics.avgReviewTime}</span>
              </div>
            </div>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            
            <div className="space-y-3">
              <motion.button 
                className="w-full py-2 bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded-lg text-sm hover:bg-blue-500/30 transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                📊 Generate Quality Report
              </motion.button>
              <motion.button 
                className="w-full py-2 bg-purple-500/20 border border-purple-500/30 text-purple-300 rounded-lg text-sm hover:bg-purple-500/30 transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                🔍 Audit Supplier History
              </motion.button>
              <motion.button 
                className="w-full py-2 bg-amber-500/20 border border-amber-500/30 text-amber-300 rounded-lg text-sm hover:bg-amber-500/30 transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                ⚠️ Flag Quality Alert
              </motion.button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}