import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import LoginPage from './components/auth/LoginPage'
import Navigation from './components/layout/Navigation'
import WarehouseDashboard from './components/dashboard/WarehouseDashboard'
import QCManagerDashboard from './components/dashboard/QCManagerDashboard'
import DirectorDashboard from './components/dashboard/DirectorDashboard'
import { ToastContainer, useToast } from './components/ui/Toast'
import './index.css'

function App() {
  const [user, setUser] = useState<{
    role: 'procurement' | 'qc_manager' | 'director'
    name: string
  } | null>(null)

  const { toasts, addToast, removeToast } = useToast()

  const handleLogin = (role: string) => {
    const names = {
      procurement: 'John Smith',
      qc_manager: 'Sarah Wilson', 
      director: 'Mike Rodriguez'
    }
    
    setUser({
      role: role as 'procurement' | 'qc_manager' | 'director',
      name: names[role as keyof typeof names]
    })

    // Welcome toast
    addToast({
      type: 'success',
      message: `Welcome back, ${names[role as keyof typeof names]}!`
    })
  }

  const handleLogout = () => {
    addToast({
      type: 'info',
      message: 'Successfully logged out'
    })
    setUser(null)
  }

  // Role-based default routing
  const getDefaultRoute = () => {
    if (!user) return '/dashboard'
    
    const routes = {
      procurement: '/dashboard',
      qc_manager: '/review', 
      director: '/analytics'
    }
    return routes[user.role]
  }

  if (!user) {
    return (
      <>
        <LoginPage onLogin={handleLogin} />
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </>
    )
  }

  return (
    <Router>
      <div className="min-h-screen">
        <Navigation userRole={user.role} userName={user.name} onLogout={handleLogout} />
        <Routes>
          <Route path="/dashboard" element={<WarehouseDashboard />} />
          <Route path="/review" element={<QCManagerDashboard />} />
          <Route path="/analytics" element={<DirectorDashboard />} />
          <Route path="/shipments" element={<div className="p-6 text-center text-white">Shipments Management Coming Soon</div>} />
          <Route path="/suppliers" element={<div className="p-6 text-center text-white">Supplier Management Coming Soon</div>} />
          <Route path="/processing" element={<div className="p-6 text-center text-white">Live Agent Processing Coming Soon</div>} />
          <Route path="/settings" element={<div className="p-6 text-center text-white">Settings Coming Soon</div>} />
          <Route path="/" element={<Navigate to={getDefaultRoute()} replace />} />
        </Routes>
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </Router>
  )
}

export default App