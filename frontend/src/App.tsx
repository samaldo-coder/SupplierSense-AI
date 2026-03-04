import { useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import Navigation from './components/layout/Navigation'
import LoginPage from './components/auth/LoginPage'
import DirectorDashboard from './components/dashboard/DirectorDashboard'
import QCManagerDashboard from './components/dashboard/QCManagerDashboard'
import WarehouseDashboard from './components/dashboard/WarehouseDashboard'
import { ToastContainer, useToast } from './components/ui/Toast'

type UserRole = 'procurement' | 'qc_manager' | 'director'

const roleNames: Record<UserRole, string> = {
  procurement: 'Ana Torres',
  qc_manager: 'Marcus Chen',
  director: 'James Rivera',
}

function DashboardRouter({ role }: { role: UserRole }) {
  switch (role) {
    case 'director':
      return <DirectorDashboard />
    case 'qc_manager':
      return <QCManagerDashboard />
    case 'procurement':
    default:
      return <WarehouseDashboard />
  }
}

export default function App() {
  const [userRole, setUserRole] = useState<UserRole | null>(() => {
    const saved = localStorage.getItem('supplyguard_role')
    return saved ? (saved as UserRole) : null
  })

  const { toasts, addToast, removeToast } = useToast()

  const handleLogin = useCallback(
    (role: string) => {
      const validRole = role as UserRole
      setUserRole(validRole)
      localStorage.setItem('supplyguard_role', validRole)
      addToast({
        type: 'success',
        message: `Welcome, ${roleNames[validRole]}! Logged in as ${validRole.replace('_', ' ')}.`,
      })
    },
    [addToast],
  )

  const handleLogout = useCallback(() => {
    setUserRole(null)
    localStorage.removeItem('supplyguard_role')
    addToast({ type: 'info', message: 'Signed out successfully.' })
  }, [addToast])

  if (!userRole) {
    return (
      <div className="min-h-screen bg-slate-950">
        <LoginPage onLogin={handleLogin} />
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    )
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950">
        <Navigation
          userRole={userRole}
          userName={roleNames[userRole]}
          onLogout={handleLogout}
        />
        <main className="pb-12">
          <Routes>
            {/* Main dashboard — role-specific */}
            <Route path="/dashboard" element={<DashboardRouter role={userRole} />} />

            {/* Director-specific routes */}
            <Route path="/analytics" element={<DirectorDashboard />} />

            {/* QC Manager routes */}
            <Route path="/review" element={<QCManagerDashboard />} />
            <Route path="/processing" element={<QCManagerDashboard />} />

            {/* Shared routes */}
            <Route path="/shipments" element={<WarehouseDashboard />} />
            <Route path="/suppliers" element={<DirectorDashboard />} />

            {/* Settings placeholder */}
            <Route
              path="/settings"
              element={
                <div className="max-w-7xl mx-auto p-6">
                  <div className="glass-card p-12 text-center">
                    <h2 className="text-xl font-bold text-white mb-2">Settings</h2>
                    <p className="text-gray-400">Settings page coming soon. Configure alert thresholds, notification preferences, and API keys.</p>
                  </div>
                </div>
              }
            />

            {/* Redirect root to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </BrowserRouter>
  )
}
