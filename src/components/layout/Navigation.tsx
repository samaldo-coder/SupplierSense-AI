import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Building2, 
  LayoutDashboard, 
  Package, 
  Users, 
  Activity, 
  ClipboardCheck,
  BarChart3,
  Settings,
  LogOut,
  ChevronDown,
  Bell
} from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

interface NavigationProps {
  userRole: 'procurement' | 'qc_manager' | 'director'
  userName: string
  onLogout: () => void
}

export default function Navigation({ userRole, userName, onLogout }: NavigationProps) {
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const [notifications] = useState(3)
  const location = useLocation()

  const getNavItems = () => {
    const baseItems = [
      { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }
    ]

    const roleItems = {
      procurement: [
        { path: '/shipments', label: 'Shipments', icon: Package },
        { path: '/suppliers', label: 'Suppliers', icon: Users },
      ],
      qc_manager: [
        { path: '/review', label: 'Review Queue', icon: ClipboardCheck },
        { path: '/shipments', label: 'Shipments', icon: Package },
        { path: '/processing', label: 'Live Agents', icon: Activity },
      ],
      director: [
        { path: '/analytics', label: 'Analytics', icon: BarChart3 },
        { path: '/suppliers', label: 'Suppliers', icon: Users },
        { path: '/shipments', label: 'Shipments', icon: Package },
      ]
    }

    return [...baseItems, ...roleItems[userRole]]
  }

  const getRoleBadge = () => {
    const badges = {
      procurement: { label: 'Warehouse', color: 'from-blue-500 to-cyan-500' },
      qc_manager: { label: 'QC Manager', color: 'from-purple-500 to-pink-500' },
      director: { label: 'Director', color: 'from-emerald-500 to-teal-500' }
    }
    return badges[userRole]
  }

  const roleBadge = getRoleBadge()
  const navItems = getNavItems()

  return (
    <nav className="glass-card border-b border-white/10 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-4">
            <Link to="/dashboard" className="flex items-center space-x-3 group">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-gradient font-bold text-lg">SupplierSense</div>
                <div className="text-xs text-gray-400 font-mono -mt-1">AI</div>
              </div>
            </Link>
            
            <div className={`px-2 py-1 rounded-md bg-gradient-to-r ${roleBadge.color} text-xs font-medium text-white`}>
              {roleBadge.label}
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`nav-item flex items-center space-x-2 ${
                    isActive ? 'active' : ''
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{item.label}</span>
                </Link>
              )
            })}
          </div>

          <div className="flex items-center space-x-4">
            <button className="relative p-2 rounded-lg hover:bg-white/10 transition-colors">
              <Bell className="w-5 h-5 text-gray-300" />
              {notifications > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-medium"
                >
                  {notifications}
                </motion.span>
              )}
            </button>

            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {userName.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div className="text-left hidden sm:block">
                  <div className="text-sm font-medium text-white">{userName}</div>
                  <div className="text-xs text-gray-400">{roleBadge.label}</div>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${
                  isProfileOpen ? 'rotate-180' : ''
                }`} />
              </button>

              <AnimatePresence>
                {isProfileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    className="absolute right-0 mt-2 w-48 glass-card border border-white/20 shadow-xl"
                  >
                    <div className="p-2">
                      <Link
                        to="/settings"
                        className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-white/10 transition-colors"
                        onClick={() => setIsProfileOpen(false)}
                      >
                        <Settings className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-300">Settings</span>
                      </Link>
                      
                      <hr className="border-white/10 my-2" />
                      
                      <button
                        onClick={onLogout}
                        className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-red-500/10 hover:text-red-400 transition-colors text-gray-300"
                      >
                        <LogOut className="w-4 h-4" />
                        <span className="text-sm">Sign Out</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
